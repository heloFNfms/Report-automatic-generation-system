import os
from typing import Dict, Any
from .mcp_client import MCPClient
from .deepseek_client import DeepSeekClient
from .textops import flatten_snippets, chunk_texts
from .vectorstore import Embedding, FaissStore, PGVectorStore
from . import db

class Orchestrator:
    def __init__(self):
        self.mcp = MCPClient(os.getenv("MCP_BASE", "http://localhost:8000"))
        self.ds = DeepSeekClient(os.getenv("DEEPSEEK_BASE", "https://api.deepseek.com"), os.getenv("DEEPSEEK_API_KEY", ""))
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
    async def step3_content(self, task_id: str):
        t = await db.get_task(task_id)
        if not t:
            raise ValueError("task not found")
        outline = await db.latest_step(task_id, "outline")
        if not outline:
            raise ValueError("run step2 first")
        outline_list = outline.get("研究大纲") or []
        section_results: Dict[str, Any] = {}
        for block in outline_list:
            h1 = block.get("一级标题")
            for h2 in block.get("二级标题", []):
                query = f"{t['project_name']} {t['research_content']} {h1} {h2}"
                r = await self.mcp.invoke("arxiv_search", {"query": query, "max_results": 8})
                items = r.get("items", [])
                texts = flatten_snippets(items)
                metas = [{"url": it.get("url"), "title": it.get("title") or it.get("id") } for it in items]
                if texts:
                    embs = self.embed.encode(texts)
                    self.store.add(embs, texts, metas)
                q_emb = self.embed.encode([query])[0]
                retrieved = self.store.search(q_emb, top_k=6)
                retrieved_texts = [rt[0] for rt in retrieved]
                refs = [rt[1].get("url") for rt in retrieved if rt[1].get("url")]
                context = "\n\n".join(chunk_texts(retrieved_texts)[:12])
                system = "你是学术写作助手，请基于证据撰写严谨内容，并给出参考网址。"
                prompt = (
                    f"【章节】{h1} / {h2}\n【主题】{t['project_name']}\n【研究方向】{t['research_content']}\n【证据】\n{context}\n"
                )
                instruction = "输出 JSON：{\n  \"研究内容\": \"...\",\n  \"参考网址\": [\"https://...\"]\n}"
                ds = await self.ds.chat_json(system, prompt, instruction)
                # 保障包含 refs（双通道：模型给的 + 我们检索的）
                merged_refs = list({*(ds.get("参考网址", []) or []), *[u for u in refs if u]})
                section_results[f"{h1}::{h2}"] = {"研究内容": ds.get("研究内容") or ds.get("content"), "参考网址": merged_refs}
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
            body_lines.append(f"### {h1} / {h2}\n{val.get('研究内容', '')}\n")
            for u in val.get("参考网址", []) or []:
                ref_set.add(u)
        draft = f"# {t['project_name']}\n\n" + "\n".join(body_lines) + "\n\n## 参考文献\n" + "\n".join(f"- {u}" for u in sorted(ref_set))
        system = "你是学术润色师，请优化行文与结构，保持事实与引用。"
        instruction = "输出润色后的完整 Markdown 正文（包含分章与参考文献）。"
        res = await self.ds.chat_json(system, draft, instruction)
        await db.save_step(task_id, "report", res)
        await db.update_task_status(task_id, "step4_done")
        return res

    # Step5: 摘要+关键词 → 存 MySQL
    async def step5_finalize(self, task_id: str):
        report = await db.latest_step(task_id, "report")
        if not report:
            raise ValueError("run step4 first")
        system = "你是文摘机器人，请在不丢失信息的情况下生成摘要与关键词。"
        instruction = "输出 JSON：{\n  \"摘要\": \"...\", \n  \"关键词\": [\"..\"], \n  \"完整文章\": \"...（在文首添加 摘要/关键词 段落）\"\n}"
        res = await self.ds.chat_json(system, str(report), instruction)
        await db.save_step(task_id, "final", res)
        await db.update_task_status(task_id, "step5_done")
        return res
