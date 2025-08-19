import aiohttp
import asyncio
from typing import List, Dict, Any
import re
from urllib.parse import quote

class CrossrefTool:
    name = "crossref_search"
    description = "Search academic papers using Crossref API. Args: query (str), max_results(int)=10, sort(str)='relevance'"
    
    @staticmethod
    def metadata():
        return {
            "name": CrossrefTool.name, 
            "description": CrossrefTool.description, 
            "args": {
                "query": "string", 
                "max_results": "int",
                "sort": "string"
            }
        }

    @staticmethod
    async def run(query: str, max_results: int = 10, sort: str = 'relevance'):
        if not query:
            return {"error": "empty query"}
        
        try:
            # Crossref API 搜索
            base_url = "https://api.crossref.org/works"
            params = {
                'query': query,
                'rows': min(max_results, 20),  # Crossref 限制
                'sort': sort,
                'select': 'DOI,title,author,published-print,published-online,container-title,abstract,URL,type,publisher,subject'
            }
            
            headers = {
                'User-Agent': 'ReportGenerator/1.0 (mailto:admin@example.com)'
            }
            
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
                url = f"{base_url}?" + "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('message', {}).get('items', [])
                        
                        results = []
                        for item in items:
                            result = CrossrefTool._parse_crossref_item(item)
                            results.append(result)
                        
                        return {
                            "query": query,
                            "count": len(results),
                            "total_results": data.get('message', {}).get('total-results', 0),
                            "results": results
                        }
                    else:
                        return {"error": f"Crossref API error: HTTP {response.status}"}
        except Exception as e:
            return {"error": f"Crossref search failed: {str(e)}"}
    
    @staticmethod
    def _parse_crossref_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """解析 Crossref API 返回的单个条目"""
        # 提取标题
        title = ''
        if 'title' in item and item['title']:
            title = item['title'][0] if isinstance(item['title'], list) else str(item['title'])
        
        # 提取作者
        authors = []
        if 'author' in item:
            for author in item['author']:
                given = author.get('given', '')
                family = author.get('family', '')
                if given and family:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)
        
        # 提取发表日期
        published_date = ''
        if 'published-print' in item:
            date_parts = item['published-print'].get('date-parts', [])
            if date_parts and date_parts[0]:
                published_date = '-'.join(map(str, date_parts[0]))
        elif 'published-online' in item:
            date_parts = item['published-online'].get('date-parts', [])
            if date_parts and date_parts[0]:
                published_date = '-'.join(map(str, date_parts[0]))
        
        # 提取期刊名称
        journal = ''
        if 'container-title' in item and item['container-title']:
            journal = item['container-title'][0] if isinstance(item['container-title'], list) else str(item['container-title'])
        
        # 提取摘要
        abstract = item.get('abstract', '')
        if abstract:
            # 清理 HTML 标签
            abstract = re.sub(r'<[^>]+>', '', abstract)
        
        # 提取学科分类
        subjects = item.get('subject', [])
        
        return {
            'doi': item.get('DOI', ''),
            'title': title,
            'authors': authors,
            'journal': journal,
            'published_date': published_date,
            'abstract': abstract,
            'url': item.get('URL', ''),
            'type': item.get('type', ''),
            'publisher': item.get('publisher', ''),
            'subjects': subjects,
            'citation_count': item.get('is-referenced-by-count', 0)
        }

class DOITool:
    name = "doi_lookup"
    description = "Look up paper details by DOI. Args: doi (str)"
    
    @staticmethod
    def metadata():
        return {
            "name": DOITool.name, 
            "description": DOITool.description, 
            "args": {
                "doi": "string"
            }
        }

    @staticmethod
    async def run(doi: str):
        if not doi:
            return {"error": "empty doi"}
        
        # 清理 DOI
        doi = doi.strip()
        if doi.startswith('http'):
            # 从 URL 中提取 DOI
            doi_match = re.search(r'10\.[0-9]+/[^\s]+', doi)
            if doi_match:
                doi = doi_match.group()
            else:
                return {"error": "Invalid DOI URL"}
        
        try:
            # 使用 Crossref API 查询 DOI
            url = f"https://api.crossref.org/works/{doi}"
            headers = {
                'User-Agent': 'ReportGenerator/1.0 (mailto:admin@example.com)'
            }
            
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        item = data.get('message', {})
                        result = CrossrefTool._parse_crossref_item(item)
                        return {
                            "doi": doi,
                            "found": True,
                            "result": result
                        }
                    elif response.status == 404:
                        return {
                            "doi": doi,
                            "found": False,
                            "error": "DOI not found"
                        }
                    else:
                        return {
                            "doi": doi,
                            "found": False,
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "doi": doi,
                "found": False,
                "error": str(e)
            }

class CitationTool:
    name = "citation_format"
    description = "Format citation from DOI or paper details. Args: doi (str), style(str)='apa'"
    
    @staticmethod
    def metadata():
        return {
            "name": CitationTool.name, 
            "description": CitationTool.description, 
            "args": {
                "doi": "string",
                "style": "string"
            }
        }

    @staticmethod
    async def run(doi: str, style: str = 'apa'):
        if not doi:
            return {"error": "empty doi"}
        
        try:
            # 首先获取论文详情
            paper_details = await DOITool.run(doi)
            
            if not paper_details.get('found'):
                return {"error": "DOI not found"}
            
            result = paper_details['result']
            
            # 根据样式格式化引用
            if style.lower() == 'apa':
                citation = CitationTool._format_apa(result)
            elif style.lower() == 'mla':
                citation = CitationTool._format_mla(result)
            elif style.lower() == 'chicago':
                citation = CitationTool._format_chicago(result)
            else:
                citation = CitationTool._format_apa(result)  # 默认使用 APA
            
            return {
                "doi": doi,
                "style": style,
                "citation": citation,
                "bibtex": CitationTool._format_bibtex(result)
            }
        except Exception as e:
            return {"error": f"Citation formatting failed: {str(e)}"}
    
    @staticmethod
    def _format_apa(result: Dict[str, Any]) -> str:
        """APA 格式引用"""
        authors = result.get('authors', [])
        title = result.get('title', '')
        journal = result.get('journal', '')
        date = result.get('published_date', '')
        doi = result.get('doi', '')
        
        # 格式化作者
        if authors:
            if len(authors) == 1:
                author_str = authors[0]
            elif len(authors) <= 7:
                author_str = ', '.join(authors[:-1]) + ', & ' + authors[-1]
            else:
                author_str = ', '.join(authors[:6]) + ', ... ' + authors[-1]
        else:
            author_str = 'Unknown Author'
        
        # 提取年份
        year = date.split('-')[0] if date else 'n.d.'
        
        citation = f"{author_str} ({year}). {title}"
        if journal:
            citation += f". {journal}"
        if doi:
            citation += f". https://doi.org/{doi}"
        
        return citation
    
    @staticmethod
    def _format_mla(result: Dict[str, Any]) -> str:
        """MLA 格式引用"""
        authors = result.get('authors', [])
        title = result.get('title', '')
        journal = result.get('journal', '')
        date = result.get('published_date', '')
        
        if authors:
            author_str = authors[0]
            if len(authors) > 1:
                author_str += ', et al.'
        else:
            author_str = 'Unknown Author'
        
        citation = f'{author_str}. "{title}."'
        if journal:
            citation += f' {journal}'
        if date:
            citation += f', {date}'
        
        return citation
    
    @staticmethod
    def _format_chicago(result: Dict[str, Any]) -> str:
        """Chicago 格式引用"""
        authors = result.get('authors', [])
        title = result.get('title', '')
        journal = result.get('journal', '')
        date = result.get('published_date', '')
        
        if authors:
            author_str = authors[0]
            if len(authors) > 1:
                author_str += ' et al.'
        else:
            author_str = 'Unknown Author'
        
        citation = f'{author_str}. "{title}."'
        if journal:
            citation += f' {journal}'
        if date:
            citation += f' ({date})'
        
        return citation
    
    @staticmethod
    def _format_bibtex(result: Dict[str, Any]) -> str:
        """BibTeX 格式"""
        doi = result.get('doi', '').replace('/', '_').replace('.', '_')
        title = result.get('title', '')
        authors = result.get('authors', [])
        journal = result.get('journal', '')
        year = result.get('published_date', '').split('-')[0] if result.get('published_date') else ''
        
        author_str = ' and '.join(authors) if authors else 'Unknown Author'
        
        bibtex = f"""@article{{{doi},
  title={{{title}}},
  author={{{author_str}}},
  journal={{{journal}}},
  year={{{year}}},
  doi={{{result.get('doi', '')}}}
}}"""
        
        return bibtex