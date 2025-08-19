import feedparser

class ArxivTool:
    name = "arxiv_search"
    description = "Search papers from arXiv. Args: query (str), max_results(int)=5"

    @staticmethod
    def metadata():
        return {"name": ArxivTool.name, "description": ArxivTool.description, "args": {"query": "string", "max_results": "int"}}

    @staticmethod
    async def run(query: str, max_results: int = 5):
        if not query:
            return {"error": "empty query"}
        base = "http://export.arxiv.org/api/query"
        q = f"?search_query=all:{query}&start=0&max_results={max_results}"
        feed = feedparser.parse(base + q)
        items = []
        for e in feed.entries:
            authors = [a.name for a in getattr(e, 'authors', [])]
            items.append({
                "id": e.get('id'),
                "title": e.get('title'),
                "summary": e.get('summary', ''),
                "authors": authors,
                "published": e.get('published'),
                "url": e.get('link')
            })
        return {"query": query, "count": len(items), "items": items}
