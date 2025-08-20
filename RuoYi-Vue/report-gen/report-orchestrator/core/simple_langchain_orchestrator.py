import os
import asyncio
from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import json

from .mcp_client import MCPClient
from .deepseek_client import DeepSeekClient
from .textops import flatten_snippets, chunk_texts, rerank_texts, budget_context, smart_sentence_split, deduplicate_citations, smart_chunk_by_strategy
from .vectorstore import Embedding, FaissStore, PGVectorStore
from .enhanced_rag_pipeline import EnhancedRAGPipeline
from .rag_config import RAGConfig, get_config
from . import db


class SimpleLangChainOrchestrator:
    """简化版的LangChain编排器，保持与原始编排器相同的接口"""
    
    def __init__(self, rag_config: RAGConfig = None):
        # 初始化基础组件
        self.mcp = MCPClient(os.getenv("MCP_BASE", "http://localhost:8000"))
        self.ds = DeepSeekClient(
            os.getenv("DEEPSEEK_BASE", "https://api.deepseek.com"), 
            os.getenv("DEEPSEEK_API_KEY", ""),
            os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        )
        
        # 初始化向量存储
        backend = os.getenv("VECTOR_BACKEND", "faiss").lower()
        self.embed = Embedding()
        if backend == "pgvector":
            self.store = PGVectorStore(os.getenv("PG_DSN", ""))
        else:
            self.store = FaissStore()
            self.store.load()  # 载入持久化
        
        # 初始化增强RAG流水线
        self.rag_pipeline = EnhancedRAGPipeline(
            mcp_client=self.mcp,
            deepseek_client=self.ds,
            embedding=self.embed,
            vector_store=self.store,
            config=rag_config or RAGConfig()
        )
    
    async def step1(self, project_name: str, company_name: str, research_content: str):
        """Step1: 保存主题 → MySQL"""
        tid = await db.create_task(project_name, company_name, research_content)
        await db.update_task_status(tid, "step1_done")
        return {"task_id": tid}
    
    async def step2_outline(self, task_id: str):
        """Step2: 生成【研究大纲】 → DeepSeek → 存 MySQL"""
        t = await db.get_task(task_id)
        if not t:
            raise ValueError("task not found")
        system = "你是一名严格的学术大纲专家，输出三级结构大纲 JSON。"
        prompt = f"项目名称：{t['project_name']}\n研究内容：{t['research_content']}\n请给出清晰的三级标题大纲。"
        instruction = (
            "只输出 JSON：{\n  \"研究大纲\": [\n    {\"一级标题\": \"...\", \"二级标题\": [\"..\", \"..\"]}\n  ]\n}"
        )
        res = await self.ds.chat_json(system, prompt, instruction)
        await db.save_step(task_id, "outline", res)
        await db.update_task_status(task_id, "step2_done")
        return res
    
    async def _generate_section_content(self, t: Dict[str, Any], h1: str, h2: str):
        """使用增强RAG流水线生成单个章节内容"""
        result = await self.rag_pipeline.generate_section_content(t, h1, h2)
        return f"{h1}::{h2}", {"研究内容": result.get("content", ""), "参考网址": [ref.get("url", "") for ref in result.get("参考网址", [])]}
    
    async def step3_content(self, task_id: str):
        """Step3: 检索+RAG 生成内容（唯一 MCP 步） → 存 MySQL"""
        t = await db.get_task(task_id)
        if not t:
            raise ValueError("task not found")
        outline = await db.latest_step(task_id, "outline")
        if not outline:
            raise ValueError("run step2 first")
        outline_list = outline.get("研究大纲") or []
        
        # 收集所有需要处理的章节
        tasks = []
        for block in outline_list:
            h1 = block.get("一级标题")
            for h2 in block.get("二级标题", []):
                tasks.append(self._generate_section_content(t, h1, h2))
        
        # 并行处理所有章节（限制并发数为3）
        semaphore = asyncio.Semaphore(3)  # 限制并发数
        
        async def process_with_limit(task):
            async with semaphore:
                return await task
        
        # 并发执行
        results = await asyncio.gather(*[process_with_limit(task) for task in tasks])
        
        # 组装结果
        section_results: Dict[str, Any] = {}
        for key, value in results:
            section_results[key] = value
            
        await db.save_step(task_id, "content", section_results)
        await db.update_task_status(task_id, "step3_done")
        return section_results
    
    async def step4_report(self, task_id: str):
        """Step4: 组装润色 → 存 MySQL"""
        t = await db.get_task(task_id)
        if not t:
            raise ValueError("task not found")
        content_map = await db.latest_step(task_id, "content")
        if not content_map:
            raise ValueError("run step3 first")
        body_lines, ref_set = [], set()
        for key, val in content_map.items():
            h1, h2 = key.split("::", 1)
            content = val.get('研究内容', '')
            
            # 使用智能分句优化内容结构
            sentences = smart_sentence_split(content)
            formatted_content = '\n'.join(sentences) if sentences else content
            
            body_lines.append(f"### {h1} / {h2}\n{formatted_content}\n")
            for u in val.get("参考网址", []) or []:
                ref_set.add(u)
        
        # 去重参考文献
        unique_refs = list(ref_set)
        draft = f"# {t['project_name']}\n\n" + "\n".join(body_lines) + "\n\n## 参考文献\n" + "\n".join(f"- {u}" for u in sorted(unique_refs))
        system = "你是学术润色师，请优化行文与结构，保持事实与引用。"
        instruction = "输出润色后的完整 Markdown 正文（包含分章与参考文献）。"
        res = await self.ds.chat_json(system, draft, instruction)
        await db.save_step(task_id, "report", res)
        await db.update_task_status(task_id, "step4_done")
        return res
    
    async def step5_finalize(self, task_id: str):
        """Step5: 摘要+关键词 → 存 MySQL"""
        report = await db.latest_step(task_id, "report")
        if not report:
            raise ValueError("run step4 first")
        system = "你是文摘机器人，请在不丢失信息的情况下生成摘要与关键词。"
        instruction = "输出 JSON：{\n  \"摘要\": \"...\", \n  \"关键词\": [\"..\"], \n  \"完整文章\": \"...（在文首添加 摘要/关键词 段落）\"\n}"
        res = await self.ds.chat_json(system, str(report), instruction)
        await db.save_step(task_id, "final", res)
        await db.update_task_status(task_id, "step5_done")
        return res


# 为了向后兼容，创建一个别名
Orchestrator = SimpleLangChainOrchestrator