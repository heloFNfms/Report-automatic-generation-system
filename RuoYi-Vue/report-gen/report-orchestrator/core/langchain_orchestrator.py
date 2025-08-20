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


class DeepSeekLangChainAdapter(ChatOpenAI):
    """将DeepSeek客户端适配为LangChain兼容的聊天模型"""
    
    def __init__(self, deepseek_client: DeepSeekClient, **kwargs):
        # 初始化父类，但不实际使用OpenAI
        super().__init__(api_key="dummy", base_url="dummy", **kwargs)
        self.deepseek_client = deepseek_client
    
    async def _agenerate(self, messages: List[BaseMessage], **kwargs) -> Any:
        """异步生成响应"""
        # 将LangChain消息转换为DeepSeek格式
        system_msg = ""
        user_msg = ""
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_msg = msg.content
            elif isinstance(msg, HumanMessage):
                user_msg = msg.content
        
        # 调用DeepSeek客户端
        try:
            response = await self.deepseek_client.chat_json(
                system_msg, 
                user_msg, 
                "请以JSON格式回复"
            )
            # 返回格式化的响应
            from langchain_core.outputs import LLMResult, ChatGeneration
            from langchain_core.messages import AIMessage
            
            ai_message = AIMessage(content=json.dumps(response, ensure_ascii=False))
            generation = ChatGeneration(message=ai_message)
            return LLMResult(generations=[[generation]])
        except Exception as e:
            from langchain_core.outputs import LLMResult, ChatGeneration
            from langchain_core.messages import AIMessage
            
            ai_message = AIMessage(content=json.dumps({"error": str(e)}, ensure_ascii=False))
            generation = ChatGeneration(message=ai_message)
            return LLMResult(generations=[[generation]])
    
    def _generate(self, messages: List[BaseMessage], **kwargs) -> Any:
        """同步生成响应（通过异步实现）"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._agenerate(messages, **kwargs))


class CreateTaskInput(BaseModel):
    """创建任务的输入模型"""
    project_name: str = Field(description="项目名称")
    company_name: str = Field(description="公司名称")
    research_content: str = Field(description="研究内容")


class GenerateOutlineInput(BaseModel):
    """生成大纲的输入模型"""
    task_id: str = Field(description="任务ID")


class GenerateSectionInput(BaseModel):
    """生成章节内容的输入模型"""
    task_id: str = Field(description="任务ID")


class AssembleReportInput(BaseModel):
    """组装报告的输入模型"""
    task_id: str = Field(description="任务ID")


class FinalizeReportInput(BaseModel):
    """完成报告的输入模型"""
    task_id: str = Field(description="任务ID")


class CreateTaskTool(BaseTool):
    """创建任务工具"""
    name: str = "create_task"
    description: str = "创建新的研究任务，保存项目信息到数据库"
    args_schema: type = CreateTaskInput
    
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
    
    async def _arun(self, project_name: str, company_name: str, research_content: str) -> str:
        """异步执行创建任务"""
        try:
            result = await self.orchestrator.step1(project_name, company_name, research_content)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _run(self, project_name: str, company_name: str, research_content: str) -> str:
        """同步执行创建任务"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(project_name, company_name, research_content))


class GenerateOutlineTool(BaseTool):
    """生成大纲工具"""
    name: str = "generate_outline"
    description: str = "为指定任务生成研究大纲"
    args_schema: type = GenerateOutlineInput
    
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
    
    async def _arun(self, task_id: str) -> str:
        """异步执行生成大纲"""
        try:
            result = await self.orchestrator.step2_outline(task_id)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _run(self, task_id: str) -> str:
        """同步执行生成大纲"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(task_id))


class SearchAndGenerateSectionTool(BaseTool):
    """搜索并生成章节内容工具"""
    name: str = "search_and_generate_section"
    description: str = "使用RAG流水线搜索相关资料并生成章节内容"
    args_schema: type = GenerateSectionInput
    
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
    
    async def _arun(self, task_id: str) -> str:
        """异步执行搜索和生成章节内容"""
        try:
            result = await self.orchestrator.step3_content(task_id)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _run(self, task_id: str) -> str:
        """同步执行搜索和生成章节内容"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(task_id))


class AssembleReportTool(BaseTool):
    """组装报告工具"""
    name: str = "assemble_report"
    description: str = "将生成的章节内容组装成完整报告"
    args_schema: type = AssembleReportInput
    
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
    
    async def _arun(self, task_id: str) -> str:
        """异步执行组装报告"""
        try:
            result = await self.orchestrator.step4_report(task_id)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _run(self, task_id: str) -> str:
        """同步执行组装报告"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(task_id))


class FinalizeReportTool(BaseTool):
    """完成报告工具"""
    name: str = "finalize_report"
    description: str = "为报告添加摘要和关键词，完成最终版本"
    args_schema: type = FinalizeReportInput
    
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
    
    async def _arun(self, task_id: str) -> str:
        """异步执行完成报告"""
        try:
            result = await self.orchestrator.step5_finalize(task_id)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _run(self, task_id: str) -> str:
        """同步执行完成报告"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(task_id))


class LangChainOrchestrator:
    """基于LangChain的报告生成编排器"""
    
    def __init__(self):
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
            config=RAGConfig()
        )
        
        # 初始化LangChain组件
        self.llm = DeepSeekLangChainAdapter(self.ds)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # 创建工具
        self.tools = [
            CreateTaskTool(self),
            GenerateOutlineTool(self),
            SearchAndGenerateSectionTool(self),
            AssembleReportTool(self),
            FinalizeReportTool(self)
        ]
        
        # 创建提示模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个专业的研究报告生成助手。你可以使用以下工具来完成报告生成的各个步骤：\n"
                      "1. create_task: 创建新的研究任务\n"
                      "2. generate_outline: 生成研究大纲\n"
                      "3. search_and_generate_section: 搜索资料并生成章节内容\n"
                      "4. assemble_report: 组装完整报告\n"
                      "5. finalize_report: 添加摘要和关键词\n\n"
                      "请根据用户的需求，按顺序使用这些工具来完成报告生成。"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建Agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        
        # 创建AgentExecutor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
    
    # 保持与原始编排器相同的接口
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
        """生成单个章节内容"""
        try:
            query = f"{t['project_name']} {t['research_content']} {h1} {h2}"
            
            # 使用增强RAG流水线生成内容
            result = await self.rag_pipeline.generate_section_content(t, h1, h2)
            
            # 提取参考网址
            references = []
            for ref in result.get("参考网址", []):
                if isinstance(ref, dict) and ref.get("url"):
                    references.append(ref["url"])
                elif isinstance(ref, str):
                    references.append(ref)
            
            return f"{h1}::{h2}", {
                "研究内容": result.get("content", ""),
                "参考网址": references
            }
        except Exception as e:
            return f"{h1}::{h2}", {"研究内容": f"生成{h1}/{h2}内容时出错: {str(e)}", "参考网址": []}
    
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
    
    async def generate_report_with_agent(self, project_name: str, company_name: str, research_content: str):
        """使用LangChain Agent完成整个报告生成流程"""
        try:
            # 构建输入消息
            input_message = f"请为以下项目生成完整的研究报告：\n项目名称：{project_name}\n公司名称：{company_name}\n研究内容：{research_content}\n\n请按照以下步骤执行：\n1. 创建任务\n2. 生成研究大纲\n3. 搜索资料并生成章节内容\n4. 组装完整报告\n5. 添加摘要和关键词"
            
            # 使用Agent执行
            result = await self.agent_executor.ainvoke({"input": input_message})
            
            return result
        except Exception as e:
            return {"error": f"Agent执行失败: {str(e)}"}