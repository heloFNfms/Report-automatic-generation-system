from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import importlib
import os
from tools.registry import TOOL_REGISTRY
from utils.cache import Cache


app = FastAPI(title="report-mcp (MCP Server)")
cache = Cache()


class InvokeRequest(BaseModel):
    tool: str
    args: Dict[str, Any] = {}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/tools")
async def list_tools():
# 返回可用工具的元信息
    return {"tools": [t.metadata for t in TOOL_REGISTRY.values()]}


@app.post("/invoke")
async def invoke(req: InvokeRequest):
    name = req.tool
    args = req.args or {}
    if name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"tool {name} not found")


    tool = TOOL_REGISTRY[name]
    cache_key = f"tool:{name}:{str(args)}"
    cached = cache.get(cache_key)
    if cached:
        return {"from_cache": True, "result": cached}


    try:
        result = await tool.run(**args)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    cache.set(cache_key, result)
    return {"from_cache": False, "result": result}