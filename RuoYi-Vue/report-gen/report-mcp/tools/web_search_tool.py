import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Any

class WebSearchTool:
    name = "web_search"
    description = "Search and extract content from web pages. Args: query (str), max_results(int)=5, extract_content(bool)=True"
    
    @staticmethod
    def metadata():
        return {
            "name": WebSearchTool.name, 
            "description": WebSearchTool.description, 
            "args": {
                "query": "string", 
                "max_results": "int",
                "extract_content": "bool"
            }
        }

    @staticmethod
    async def run(query: str, max_results: int = 5, extract_content: bool = True):
        if not query:
            return {"error": "empty query"}
        
        try:
            # 使用 DuckDuckGo 搜索（无需 API key）
            search_results = await WebSearchTool._search_duckduckgo(query, max_results)
            
            if extract_content:
                # 提取每个页面的内容
                for result in search_results:
                    content = await WebSearchTool._extract_page_content(result['url'])
                    result.update(content)
            
            return {
                "query": query,
                "count": len(search_results),
                "results": search_results
            }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    @staticmethod
    async def _search_duckduckgo(query: str, max_results: int) -> List[Dict[str, Any]]:
        """使用 DuckDuckGo 进行搜索"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
            # DuckDuckGo 即时答案 API
            search_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
            
            try:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        # 处理相关主题
                        if 'RelatedTopics' in data:
                            for topic in data['RelatedTopics'][:max_results]:
                                if isinstance(topic, dict) and 'FirstURL' in topic:
                                    results.append({
                                        'title': topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                                        'url': topic['FirstURL'],
                                        'snippet': topic.get('Text', '')
                                    })
                        
                        # 如果没有足够的结果，使用备用搜索方法
                        if len(results) < max_results:
                            backup_results = await WebSearchTool._backup_search(session, query, max_results - len(results))
                            results.extend(backup_results)
                        
                        return results[:max_results]
            except Exception as e:
                # 如果 DuckDuckGo API 失败，使用备用方法
                return await WebSearchTool._backup_search(session, query, max_results)
    
    @staticmethod
    async def _backup_search(session: aiohttp.ClientSession, query: str, max_results: int) -> List[Dict[str, Any]]:
        """备用搜索方法"""
        # 使用一些公开的搜索引擎或者返回预定义的学术资源
        academic_sources = [
            {
                'title': f'Google Scholar search for: {query}',
                'url': f'https://scholar.google.com/scholar?q={query.replace(" ", "+")}',
                'snippet': f'Academic search results for {query}'
            },
            {
                'title': f'PubMed search for: {query}',
                'url': f'https://pubmed.ncbi.nlm.nih.gov/?term={query.replace(" ", "+")}',
                'snippet': f'Medical literature search for {query}'
            },
            {
                'title': f'IEEE Xplore search for: {query}',
                'url': f'https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={query.replace(" ", "+")}',
                'snippet': f'Engineering and technology papers for {query}'
            },
            {
                'title': f'ResearchGate search for: {query}',
                'url': f'https://www.researchgate.net/search?q={query.replace(" ", "+")}',
                'snippet': f'Research publications and profiles for {query}'
            },
            {
                'title': f'Semantic Scholar search for: {query}',
                'url': f'https://www.semanticscholar.org/search?q={query.replace(" ", "+")}',
                'snippet': f'AI-powered academic search for {query}'
            }
        ]
        
        return academic_sources[:max_results]
    
    @staticmethod
    async def _extract_page_content(url: str) -> Dict[str, Any]:
        """提取网页内容"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 移除脚本和样式元素
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # 提取标题
                        title = soup.find('title')
                        title_text = title.get_text().strip() if title else ''
                        
                        # 提取主要内容
                        content_selectors = [
                            'article', 'main', '.content', '#content', 
                            '.post-content', '.entry-content', '.article-content'
                        ]
                        
                        content_text = ''
                        for selector in content_selectors:
                            content_elem = soup.select_one(selector)
                            if content_elem:
                                content_text = content_elem.get_text()
                                break
                        
                        # 如果没有找到主要内容，使用 body
                        if not content_text:
                            body = soup.find('body')
                            content_text = body.get_text() if body else ''
                        
                        # 清理文本
                        content_text = re.sub(r'\s+', ' ', content_text).strip()
                        
                        # 提取元数据
                        meta_description = ''
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        if meta_desc:
                            meta_description = meta_desc.get('content', '')
                        
                        # 提取关键词
                        meta_keywords = ''
                        meta_kw = soup.find('meta', attrs={'name': 'keywords'})
                        if meta_kw:
                            meta_keywords = meta_kw.get('content', '')
                        
                        return {
                            'page_title': title_text,
                            'content': content_text[:2000],  # 限制内容长度
                            'meta_description': meta_description,
                            'meta_keywords': meta_keywords,
                            'content_length': len(content_text),
                            'status': 'success'
                        }
                    else:
                        return {
                            'status': 'error',
                            'error': f'HTTP {response.status}'
                        }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

class WebContentTool:
    name = "web_content"
    description = "Extract content from a specific URL. Args: url (str), extract_links(bool)=False"
    
    @staticmethod
    def metadata():
        return {
            "name": WebContentTool.name, 
            "description": WebContentTool.description, 
            "args": {
                "url": "string", 
                "extract_links": "bool"
            }
        }

    @staticmethod
    async def run(url: str, extract_links: bool = False):
        if not url:
            return {"error": "empty url"}
        
        try:
            content = await WebSearchTool._extract_page_content(url)
            
            if extract_links and content.get('status') == 'success':
                links = await WebContentTool._extract_links(url)
                content['links'] = links
            
            content['url'] = url
            return content
        except Exception as e:
            return {"error": f"Content extraction failed: {str(e)}"}
    
    @staticmethod
    async def _extract_links(url: str) -> List[Dict[str, str]]:
        """提取页面中的链接"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        links = []
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            text = link.get_text().strip()
                            
                            # 转换相对链接为绝对链接
                            absolute_url = urljoin(url, href)
                            
                            # 过滤有效的 HTTP/HTTPS 链接
                            if absolute_url.startswith(('http://', 'https://')):
                                links.append({
                                    'url': absolute_url,
                                    'text': text,
                                    'domain': urlparse(absolute_url).netloc
                                })
                        
                        return links[:50]  # 限制链接数量
        except Exception:
            return []
        
        return []