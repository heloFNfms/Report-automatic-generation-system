#解析Arxiv返回的数据
import feedparser
import aiohttp
import asyncio
from urllib.parse import quote_plus

class ArxivTool:
    name = "arxiv_search"
    description = "Search papers from arXiv. Args: query (str), max_results(int)=5"
    
    #静态方法，可以直接调用，不需要实例化，如 ArxivTool.metadata()。
    #元数据说明
    @staticmethod
    def metadata():
        return {"name": ArxivTool.name, "description": ArxivTool.description, "args": {"query": "string", "max_results": "int"}}

    @staticmethod
    async def run(query: str, max_results: int = 5):
        if not query:
            return {"error": "empty query"}
        base = "http://export.arxiv.org/api/query"
        encoded_query = quote_plus(query)
        q = f"?search_query=all:{encoded_query}&start=0&max_results={max_results}"
        url = base + q
        
        try:
            timeout = aiohttp.ClientTimeout(total=15.0)  # 15秒超时
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return {"error": f"HTTP {response.status}: {response.reason}"}
                    content = await response.text()
                    
            # 使用 feedparser 解析获取的内容
            feed = feedparser.parse(content)
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
        except asyncio.TimeoutError:
            return {"error": "arXiv search timeout (15s)"}
        except Exception as e:
            return {"error": f"arXiv search failed: {str(e)}"}


'''
async def,计划后期异步调用
'''