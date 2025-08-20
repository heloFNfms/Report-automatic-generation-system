import os
import time
from typing import Dict, Any
from .mcp_client import MCPClient
from .deepseek_client import DeepSeekClient
from .textops import flatten_snippets, chunk_texts, rerank_texts, budget_context, smart_sentence_split, deduplicate_citations, smart_chunk_by_strategy
from .vectorstore import Embedding, FaissStore, PGVectorStore
from .logger import logger
from . import db

class Orchestrator:
    def __init__(self):
        self.mcp = MCPClient(os.getenv("MCP_BASE", "http://localhost:8000"))
        self.ds = DeepSeekClient.from_env()
        backend = os.getenv("VECTOR_BACKEND", "faiss").lower()
        self.embed = Embedding()
        if backend == "pgvector":
            self.store = PGVectorStore(os.getenv("PG_DSN", ""))
        else:
            self.store = FaissStore()
            self.store.load()  # 载入持久化

    # Step1: 保存主题 → MySQL
    async def step1(self, project_name: str, company_name: str, research_content: str):
        tid = await db.create_task(project_name, company_name, research_content)
        await db.update_task_status(tid, "step1_done")
        return {"task_id": tid}

    # Step2: 生成【研究大纲】 → DeepSeek → 存 MySQL
    async def step2_outline(self, task_id: str):
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

    # Step3: 检索+RAG 生成内容（唯一 MCP 步） → 存 MySQL
    async def _generate_section_content(self, t: Dict[str, Any], h1: str, h2: str):
        """生成单个章节内容"""
        section_key = f"{h1}::{h2}"
        start_time = time.time()
        logger.info(f"[{section_key}] 开始生成章节内容")
        
        try:
            query = f"{t['project_name']} {t['research_content']} {h1} {h2}"
            
            # MCP 检索阶段
            mcp_start = time.time()
            r = await self.mcp.invoke("arxiv_search", {"query": query, "max_results": 8})
            mcp_time = time.time() - mcp_start
            logger.info(f"[{section_key}] MCP arXiv 检索耗时: {mcp_time:.2f}s")
            items = r.get("items", [])
            
            # 向量处理阶段
            vector_start = time.time()
            texts = flatten_snippets(items)
            metas = [{"url": it.get("url"), "title": it.get("title") or it.get("id") } for it in items]
            if texts:
                embs = self.embed.encode(texts)
                self.store.add(embs, texts, metas)
            q_emb = self.embed.encode([query])[0]
            retrieved = self.store.search(q_emb, top_k=12)  # 先检索更多
            retrieved_texts = [rt[0] for rt in retrieved]
            refs = [rt[1].get("url") for rt in retrieved if rt[1].get("url")]
            vector_time = time.time() - vector_start
            logger.info(f"[{section_key}] 向量处理耗时: {vector_time:.2f}s, 检索到 {len(retrieved_texts)} 条文档")
            
            # 文本处理阶段
            process_start = time.time()
            # 引用去重
            deduplicated_texts = deduplicate_citations(retrieved_texts, similarity_threshold=0.8)
            
            # 使用 BM25 重排序
            reranked = rerank_texts(query, deduplicated_texts, top_k=8)
            reranked_texts = [item[0] for item in reranked]
            
            # 智能分块策略（混合策略：段落 -> 句子 -> token）
            all_chunks = []
            for text in reranked_texts:
                chunks = smart_chunk_by_strategy(text, strategy="mixed", max_tokens=400)
                all_chunks.extend(chunks)
            
            # 根据 token 预算控制上下文长度
            budgeted_texts = budget_context(all_chunks, max_tokens=1500)
            context = "\n\n".join(budgeted_texts)
            process_time = time.time() - process_start
            logger.info(f"[{section_key}] 文本处理耗时: {process_time:.2f}s, 最终上下文长度: {len(context)} 字符")
            # DeepSeek 生成阶段
            deepseek_start = time.time()
            system = "你是学术写作助手，请基于证据撰写严谨内容，并给出参考网址。"
            prompt = (
                f"【章节】{h1} / {h2}\n【主题】{t['project_name']}\n【研究方向】{t['research_content']}\n【证据】\n{context}\n"
            )
            instruction = "输出 JSON：{\n  \"研究内容\": \"...\",\n  \"参考网址\": [\"https://...\"]\n}"
            ds = await self.ds.chat_json(system, prompt, instruction)
            deepseek_time = time.time() - deepseek_start
            logger.info(f"[{section_key}] DeepSeek 生成耗时: {deepseek_time:.2f}s")
            
            # 保障包含 refs（双通道：模型给的 + 我们检索的）
            merged_refs = list({*(ds.get("参考网址", []) or []), *[u for u in refs if u]})
            
            total_time = time.time() - start_time
            logger.info(f"[{section_key}] 章节生成完成，总耗时: {total_time:.2f}s (MCP:{mcp_time:.1f}s + 向量:{vector_time:.1f}s + 处理:{process_time:.1f}s + DeepSeek:{deepseek_time:.1f}s)")
            
            return f"{h1}::{h2}", {"研究内容": ds.get("研究内容") or ds.get("content"), "参考网址": merged_refs}
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"[{section_key}] 生成失败，耗时: {error_time:.2f}s, 错误: {str(e)}")
            return f"{h1}::{h2}", {"研究内容": f"生成{h1}/{h2}内容时出错: {str(e)}", "参考网址": []}

    async def step3_content(self, task_id: str):
        step3_start = time.time()
        logger.info(f"[Task {task_id}] 开始 Step3 内容生成")
        
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
        import asyncio
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
        
        step3_total_time = time.time() - step3_start
        logger.info(f"[Task {task_id}] Step3 内容生成完成，总耗时: {step3_total_time:.2f}s, 生成了 {len(section_results)} 个章节")
            
        await db.save_step(task_id, "content", section_results)
        await db.update_task_status(task_id, "step3_done")
        return section_results

    # Step4: 组装润色 → 存 MySQL
    async def step4_report(self, task_id: str):
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
        
        # 处理JSON解析错误的情况
        if isinstance(res, dict) and res.get("parse_error"):
            # 如果JSON解析失败，使用content字段的内容
            final_report = res.get("content", draft)
        else:
            # 正常情况下，res应该是字符串或包含报告内容的字典
            final_report = res if isinstance(res, str) else str(res)
            
        await db.save_step(task_id, "report", final_report)
        await db.update_task_status(task_id, "step4_done")
        return final_report

    # Step5: 摘要+关键词 → 存 MySQL
    async def step5_finalize(self, task_id: str):
        report = await db.latest_step(task_id, "report")
        if not report:
            raise ValueError("run step4 first")
        system = "你是文摘机器人，请在不丢失信息的情况下生成摘要与关键词。"
        instruction = "输出 JSON：{\n  \"摘要\": \"...\", \n  \"关键词\": [\"..\"], \n  \"完整文章\": \"...（在文首添加 摘要/关键词 段落）\"\n}"
        res = await self.ds.chat_json(system, str(report), instruction)
        
        # 处理JSON解析错误的情况
        if isinstance(res, dict) and res.get("parse_error"):
            # 如果JSON解析失败，创建默认格式
            content = res.get("content", str(report))
            final_result = {
                "摘要": "报告摘要生成中遇到格式问题，请查看完整文章。",
                "关键词": ["人工智能", "技术研究"],
                "完整文章": content
            }
        else:
            # 正常情况
            final_result = res
            
        await db.save_step(task_id, "final", final_result)
        await db.update_task_status(task_id, "step5_done")
        return final_result
