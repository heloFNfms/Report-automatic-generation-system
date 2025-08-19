from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from utils.cache import Cache
from tools.arxiv_tool import ArxivTool

app = FastAPI(title="report-mcp")
cache = Cache()
TOOLS = {ArxivTool.name: ArxivTool}

class Invoke(BaseModel):
    tool: str
    args: Dict[str, Any] = {}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/tools")
async def tools():
    return {"tools": [t.metadata() for t in TOOLS.values()]}

@app.post("/invoke")
async def invoke(req: Invoke):
    if req.tool not in TOOLS:
        raise HTTPException(404, f"tool {req.tool} not found")
    key = f"tool:{req.tool}:{str(req.args)}"
    cached = cache.get(key)
    if cached:
        return {"from_cache": True, "result": cached}
    try:
        res = await TOOLS[req.tool].run(**req.args)
    except TypeError as e:
        raise HTTPException(400, f"bad args: {e}")
    cache.set(key, res)
    return {"from_cache": False, "result": res}

