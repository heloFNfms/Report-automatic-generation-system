import os, time, uuid
from typing import Dict, Any, List
from .mcp_client import MCPClient
from .deepseek_client import DeepSeekClient
from .textops import flatten_snippets, chunk_texts
from .vectorstore import Embedding, FaissStore, PGVectorStore

TASKS: Dict[str, Dict[str, Any]] = {}

class Orchestrator:
    def __init__(self):
        self.mcp = MCPClient(os.getenv("MCP_BASE", "http://localhost:8000"))
        self.ds = DeepSeekClient(os.getenv("DEEPSEEK_BASE", "https://api.deepseek.com"), os.getenv("DEEPSEEK_API_KEY", ""))
        backend = os.getenv("VECTOR_BACKEND", "faiss").lower()
        self.embed = Embedding()
        self.store = FaissStore() if backend == "faiss" else PGVectorStore(os.getenv("PG_DSN", ""))

    # Step1: 保存主题
    async def step1(self, project_name: str, company_name: str, research_content: str):
        tid = str(uuid.uuid4())
        TASKS[tid] = {"project_name": project_name, "company_name": company_name, "research_content": research_content, "created_at": time.time(), "steps": {}}
        return {"task_id": tid}

    # Step2: 生成【研究大纲】（不检索，直接 DeepSeek）
    async def step2_outline(self, task_id: str):
        t = TASKS.get(task_id)
        if not t:
            raise ValueError("task not found")
        system = "你是一名严格的学术大纲专家，输出三级结构大纲 JSON。"
        prompt = f"项目名称：{t['project_name']}\n研究内容：{t['research_content']}\n请给出清晰的三级标题大纲。"
        instruction = (
            "请只输出 JSON，格式：\n"
            "{\n  \"研究大纲\": [\n    {\"一级标题\": \"...\", \"二级标题\": [\"..\", \"..\"]},\n    {\"一级标题\": \"...\", \"二级标题\": [\"..\", \"..\"]}\n  ]\n}\n"
        )
        res = await self.ds.chat_json(system, prompt, instruction)
        TASKS[task_id]["steps"]["step2"] = res
        return res

    # Step3: 基于大纲逐点检索（仅此步调用 MCP）→ RAG 生成内容 + 参考网址
    async def step3_content(self, task_id: str):
        t = TASKS.get(task_id)
        if not t or "step2" not in t["steps"]:
            raise ValueError("run step2 first")
        outline = t["steps"]["step2"].get("研究大纲") or []
        section_results: Dict[str, Any] = {}

        for block in outline:
            h1 = block.get("一级标题")
            for h2 in block.get("二级标题", []):
                query = f"{t['project_name']} {t['research_content']} {h1} {h2}"
                # 1) MCP: arxiv 搜索
                r = await self.mcp.invoke("arxiv_search", {"query": query, "max_results": 8})
                items = r.get("items", [])
                # 2) 提取文本 + 向量化 + 入库（向量缓存复用）
                texts = flatten_snippets(items)
                metas = [{"url": it.get("url"), "title": it.get("title") or it.get("id") } for it in items]
                if texts:
                    embs = self.embed.encode(texts)
                    self.store.add(embs, texts, metas)
                # 3) 基于查询的相似检索（TopK 证据）
                q_emb = self.embed.encode([query])[0]
                retrieved = self.store.search(q_emb, top_k=6)
                retrieved_texts = [rt[0] for rt in retrieved]
                refs = [rt[1].get("url") for rt in retrieved if rt[1].get("url")]
                # 4) 压缩拼接 → DeepSeek 生成分章节内容
                chunks = chunk_texts(retrieved_texts)
                context = "\n\n".join(chunks[:12])
                system = "你是学术写作助手，请基于给定证据撰写严谨内容，引用参考链接列表。"
                prompt = (
                    f"【章节】{h1} / {h2}\n"
                    f"【主题】{t['project_name']}\n"
                    f"【研究方向】{t['research_content']}\n"
                    f"【证据（可噪声）】\n{context}\n"
                )
                instruction = (
                    "输出 JSON：\n{\n  \"研究内容\": \"...详细段落...\",\n  \"参考网址\": [\"https://...\"]\n}\n"
                )
                ds = await self.ds.chat_json(system, prompt, instruction)
                section_results[f"{h1}::{h2}"] = ds

        TASKS[task_id]["steps"]["step3"] = section_results
        return section_results

    # Step4: 组装为主要报告并润色
    async def step4_report(self, task_id: str):
        t = TASKS.get(task_id)
        if not t or "step3" not in t["steps"]:
            raise ValueError("run step3 first")
        # 组装正文 + 参考文献
        body_lines, ref_set = [], set()
        for key, val in t["steps"]["step3"].items():
            h1, h2 = key.split("::", 1)
            content = val.get("研究内容") if isinstance(val, dict) else val
            refs = val.get("参考网址", []) if isinstance(val, dict) else []
            body_lines.append(f"### {h1} / {h2}\n{content}\n")
            for u in refs:
                if u:
                    ref_set.add(u)
        draft = f"# {t['project_name']}\n\n" + "\n".join(body_lines) + "\n\n## 参考文献\n" + "\n".join(f"- {u}" for u in sorted(ref_set))
        system = "你是学术润色师，请在保持事实与引用的前提下，提升逻辑、语言与结构。"
        instruction = "请输出润色后的完整 Markdown 正文（包含分章与参考文献）。"
        res = await self.ds.chat_json(system, draft, instruction)
        TASKS[task_id]["steps"]["step4"] = res
        return res

    # Step5: 从报告中提炼摘要与关键词，并返回完整文章（附摘要/关键词）
    async def step5_finalize(self, task_id: str):
        t = TASKS.get(task_id)
        if not t or "step4" not in t["steps"]:
            raise ValueError("run step4 first")
        report = t["steps"]["step4"].get("content") or t["steps"]["step4"]
        system = "你是学术文摘机器人，请在不丢失关键信息的前提下生成摘要与关键词。"
        instruction = (
            "输出 JSON：\n{\n  \"摘要\": \"...\",\n  \"关键词\": [\"..\"],\n  \"完整文章\": \"...（在文首添加 摘要/关键词 段落）\"\n}\n"
        )
        res = await self.ds.chat_json(system, str(report), instruction)
        TASKS[task_id]["steps"]["step5"] = res
        return res
