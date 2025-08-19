import feedparser
from .base import ToolBase


class ArxivTool(ToolBase):
    def __init__(self):
        self.name = "arxiv_search"
        self.description = "Search papers from arXiv. Args: query (str), max_results (int, default=5)."
        self.metadata = {"name": self.name, "description": self.description, "args": {"query": "string", "max_results": "int"}}


    async def run(self, query: str, max_results: int = 5):
        if not query:
            return {"error": "empty query"}
        base = "http://export.arxiv.org/api/query"
        params = f"?search_query=all:{query}&start=0&max_results={max_results}"
        url = base + params
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries:
            authors = [a.name for a in entry.authors] if hasattr(entry, 'authors') else []
            summary = entry.summary if hasattr(entry, 'summary') else ""
            items.append({
                "id": entry.get('id'),
                "title": entry.get('title'),
                "authors": authors,
                "summary": summary,
                "published": entry.get('published'),
                "link": entry.get('link')
            })
        return {"query": query, "count": len(items), "items": items}
