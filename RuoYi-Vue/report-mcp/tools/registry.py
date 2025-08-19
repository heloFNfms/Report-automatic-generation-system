from typing import Dict
from tools.base import ToolBase
from tools.arxiv_tool import ArxivTool
from tools.bing_tool import BingWebTool

TOOL_REGISTRY: Dict[str, ToolBase] = {}

# 注册工具（可扩展）
for t in [ArxivTool(), BingWebTool()]:
    TOOL_REGISTRY[t.name] = t