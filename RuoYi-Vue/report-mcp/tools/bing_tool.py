import os
import httpx
from .base import ToolBase


class BingWebTool(ToolBase):
    def __init__(self):
        self.name = "bing_web_search"
        self.description = "Bing Web Search wrapper. Args: query (str), count (int, default=5). Requires BING_API_KEY env var."
        self.metadata = {"name": self.name, "description": self.description, "args": {"query": "string", "count": "int"}}
        self.api_key = os.getenv('BING_API_KEY')
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"


    async def run(self, query: str, count: int = 5):
        if not query:
            return {"error": "empty query"}
        if not self.api_key:
            return {"error": "BING_API_KEY not configured"}
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": count}
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(self.endpoint, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
# 简单提取 webPages.value
        pages = []
        for p in data.get('webPages', {}).get('value', []):
            pages.append({"name": p.get('name'), "snippet": p.get('snippet'), "url": p.get('url')})
        return {"query": query, "count": len(pages), "items": pages}