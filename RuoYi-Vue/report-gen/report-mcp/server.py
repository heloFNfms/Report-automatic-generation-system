from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from utils.cache import Cache
from tools.arxiv_tool import ArxivTool
from tools.web_search_tool import WebSearchTool, WebContentTool
from tools.crossref_tool import CrossrefTool, DOITool, CitationTool
from tools.pdf_tool import PDFTool, PDFSummaryTool
from tools.dedup_tool import DedupTool, MergeTool, TextCleanTool

app = FastAPI(title="report-mcp")
cache = Cache()
TOOLS = {
    ArxivTool.name: ArxivTool,
    WebSearchTool.name: WebSearchTool,
    WebContentTool.name: WebContentTool,
    CrossrefTool.name: CrossrefTool,
    DOITool.name: DOITool,
    CitationTool.name: CitationTool,
    PDFTool.name: PDFTool,
    PDFSummaryTool.name: PDFSummaryTool,
    DedupTool.name: DedupTool,
    MergeTool.name: MergeTool,
    TextCleanTool.name: TextCleanTool
}

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

