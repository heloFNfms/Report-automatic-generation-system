import uuid
import json
import time
from typing import Dict, Any, List, Optional
import os
import httpx
from orchestrator.mcp_client import MCPClient
from orchestrator.deepseek_client import DeepSeekClient
from orchestrator.rerank import rerank_bm25
from orchestrator.utils import chunk_texts, compress_chunks

# Simple in-memory task store for prototype. In prod use MySQL / Redis.
TASK_STORE: Dict[str, Dict[str, Any]] = {}

class ReportOrchestrator:
    def __init__(self, mcp_base: str, deepseek_base: str, deepseek_key: str):
        self.mcp = MCPClient(mcp_base)
        self.deepseek = DeepSeekClient(deepseek_base, api_key=deepseek_key)

    async def step1_create(self, project_name: str, company_name: Optional[str], research_content: str):
        task_id = str(uuid.uuid4())
        TASK_STORE[task_id] = {'project_name': project_name, 'company_name': company_name, 'research_content': research_content,'created_at': time.time(), 'steps': {}}
        return {'task_id': task_id}

    async def step2_summary(self, task_id: str):
        task = TASK_STORE.get(task_id)
        if not task:
            raise ValueError('task not found')
        query = f"{task['project_name']} {task['research_content']}"
        results = []
        for tool in ['arxiv_search','bing_web_search']:
            try:
                r = await self.mcp.invoke(tool, {'query': query, 'max_results': 5})
                results.append({'tool':tool,'result':r})
            except Exception as e:
                results.append({'tool':tool,'error':str(e)})
        # flatten text candidates
        candidates = []
        for r in results:
            if 'result' in r and r['result']:
                items = r['result'].get('items') or []
                for it in items:
                    text = it.get('summary') or it.get('snippet') or it.get('title')
                    if text:
                        candidates.append({'text': text, 'meta': it})
        # rerank using BM25
        texts = [c['text'] for c in candidates]
        ranked_idx = rerank_bm25([query], texts) if texts else []
        top_texts = [texts[i] for i in ranked_idx[:6]] if ranked_idx else texts[:6]
        # chunk + compress
        chunks = chunk_texts(top_texts)
        compressed = compress_chunks(chunks)
        # call deepseek to summarize and extract keywords
        prompt = {
        'role':'system','content':'You are a research assistant. Generate JSON with 摘要, 关键词, 参考网址.'
        }
        payload = {
        'prompt': compressed,
        'instruction': 'Please output JSON:\n{ "摘要": "...", "关键词": [".."], "参考网址": ["..."] }'
        }
        ds_res = await self.deepseek.chat_json(payload)
        TASK_STORE[task_id]['steps']['step2'] = {'mcp': results, 'compressed': compressed, 'deepseek': ds_res}
        return TASK_STORE[task_id]['steps']['step2']
    async def step3_outline(self, task_id: str):
        task = TASK_STORE.get(task_id)
        if not task or 'step2' not in task['steps']:
            raise ValueError('please run step2 first')
        summary = task['steps']['step2']['deepseek']
        # build queries from keywords
        keywords = []
        try:
            keywords = summary.get('关键词') or []
        except Exception:
            pass
        queries = [task['project_name']] + keywords
        # call mcp with keywords
        combined_results = []
        for q in queries:
            r = await self.mcp.invoke('bing_web_search', {'query': q, 'count':5})
            combined_results.append({'query':q,'result':r})
        # rerank and compress
        candidates = []
        for cr in combined_results:
            for it in cr['result'].get('items',[]):
                text = it.get('snippet') or it.get('name')
                if text:
                    candidates.append({'text':text,'meta':it})
        texts = [c['text'] for c in candidates]
        ranked = rerank_bm25(queries, texts)
        top = [texts[i] for i in ranked[:8]] if texts else []
        compressed = compress_chunks(chunk_texts(top))
        # ask deepseek to produce a 3-level outline JSON
        payload = {'prompt': compressed, 'instruction': 'Produce a 3-level structured research outline in JSON format.'}
        ds_res = await self.deepseek.chat_json(payload)
        TASK_STORE[task_id]['steps']['step3'] = {'mcp': combined_results, 'compressed': compressed, 'deepseek': ds_res}
        return TASK_STORE[task_id]['steps']['step3']
    async def step4_content(self, task_id: str):
        task = TASK_STORE.get(task_id)
        if not task or 'step3' not in task['steps']:
            raise ValueError('please run step3 first')
        outline = task['steps']['step3']['deepseek']
        # naive extraction of headings
        headings = []
        try:
            for h in outline.get('研究大纲',[]):
                title = h.get('一级标题')
                subs = h.get('二级标题', [])
                for s in subs:
                    headings.append(f"{title} - {s}")
        except Exception:
            headings = [task['project_name']]
        contents = {}
        for hd in headings:
        # search per heading
            r = await self.mcp.invoke('bing_web_search', {'query': hd, 'count':5})
            items = r.get('result', {}).get('items', []) if isinstance(r, dict) else r.get('items', [])
            texts = [it.get('snippet') or it.get('name') for it in items if it.get('snippet') or it.get('name')]
            compressed = compress_chunks(chunk_texts(texts))
            payload = {'prompt': compressed, 'instruction': f'Write a detailed section for: {hd}'}
            ds_res = await self.deepseek.chat_json(payload)
            contents[hd] = ds_res
        TASK_STORE[task_id]['steps']['step4'] = {'per_heading': contents}
        return TASK_STORE[task_id]['steps']['step4']
    async def step5_assemble(self, task_id: str):
        task = TASK_STORE.get(task_id)
        if not task or 'step4' not in task['steps']:
            raise ValueError('please run step4 first')
        summary = task['steps'].get('step2', {}).get('deepseek',{})
        outline = task['steps'].get('step3', {}).get('deepseek',{})
        contents = task['steps'].get('step4', {}).get('per_heading',{})
        full_text = f"# {task['project_name']}\n\n"
        full_text += f"## 摘要\n{summary.get('摘要','')}\n\n"
        full_text += f"## 关键词\n{', '.join(summary.get('关键词',[]))}\n\n"
        for hd, body in contents.items():
            full_text += f"### {hd}\n{body.get('content','') if isinstance(body, dict) else str(body)}\n\n"
        # ask deepseek to polish
        payload = {'prompt': full_text, 'instruction': 'Polish into a formal academic report with references.'}
        ds_res = await self.deepseek.chat_json(payload)
        TASK_STORE[task_id]['steps']['step5'] = {'assembled': full_text, 'deepseek': ds_res}
        return TASK_STORE[task_id]['steps']['step5']