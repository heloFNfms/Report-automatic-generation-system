import json
from fastapi import FastAPI, HTTPException
from typing import List
from schemas import *
from mcp_tools import aliyun_search, arxiv_search
from rag import simple_rerank, compress, to_bullets
from deepseek import ask_deepseek

app = FastAPI(title="Report Orchestrator")

@app.get("/health")
def health(): return {"ok": True}

@app.post("/step2", response_model=Step2Resp)
async def step2(req: Step2Req):
    q = f"{req.project} {req.topic}"
    web = await aliyun_search(q)
    aca = await arxiv_search(q)
    merged = web + aca
    ranked = simple_rerank(merged, q)
    compact = compress(ranked)
    bullets = to_bullets(compact)
    urls = [it["url"] for it in compact if it.get("url")]
    system = "你是研究助理。请基于要点生成JSON：{摘要, 关键词[], 参考网址[]}"
    user = f"主题: {q}\n要点:\n{bullets}\n只输出 JSON，不要额外文字。"
    try:
        content = await ask_deepseek(system, user)
        data = json.loads(content)
        data["参考网址"] = urls  # 强制用真实URL覆盖
        return data
    except Exception as e:
        raise HTTPException(500, f"DeepSeek解析失败: {e}")

@app.post("/step3", response_model=Step3Resp)
async def step3(req: Step3Req):
    q = f"{' '.join(req.关键词)} {req.摘要[:80]}"
    merged = (await aliyun_search(q)) + (await arxiv_search(q))
    ranked = simple_rerank(merged, q)
    compact = compress(ranked)
    bullets = to_bullets(compact)
    urls = [it["url"] for it in compact if it.get("url")]
    system = "你是资深学术秘书。输出JSON: {研究大纲[ {一级标题, 二级标题[]} ], 参考网址[] }"
    user = f"摘要:{req.摘要}\n关键词:{req.关键词}\n要点:\n{bullets}\n只输出 JSON。"
    content = await ask_deepseek(system, user)
    data = json.loads(content)
    data["参考网址"] = urls
    return data

@app.post("/step4", response_model=Step4Resp)
async def step4(req: Step4Req):
    urls_acc, chapters = [], {}
    for item in req.研究大纲:
        sect = {}
        for sub in item.二级标题:
            q = f"{item.一级标题} {sub}"
            merged = (await aliyun_search(q)) + (await arxiv_search(q))
            ranked = simple_rerank(merged, q)
            compact = compress(ranked)
            bullets = to_bullets(compact)
            urls_acc += [it["url"] for it in compact if it.get("url")]
            system = "你是写作助理。根据要点写一小节，客观、可引用。只返回纯文本。"
            user = f"章节:{item.一级标题}/{sub}\n要点:\n{bullets}"
            sect[sub] = await ask_deepseek(system, user)
        chapters[item.一级标题] = sect
    return {"研究内容": chapters, "参考网址": list(dict.fromkeys(urls_acc))}

@app.post("/step5", response_model=Step5Resp)
async def step5(req: Step5Req):
    system = "你是学术润色师。根据结构生成完整报告，引用统一，格式整洁。"
    user = (
        f"摘要:{req.摘要}\n关键词:{req.关键词}\n大纲:{[i.dict() for i in req.研究大纲]}\n"
        f"内容:{json.dumps(req.研究内容, ensure_ascii=False)[:8000]}"
        "\n请生成：标题、摘要、关键词、正文（分章）、参考文献（用URL列表）。只输出JSON。"
    )
    content = await ask_deepseek(system, user)
    data = json.loads(content)
    return data
