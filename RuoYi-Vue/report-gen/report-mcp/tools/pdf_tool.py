import aiohttp
import asyncio
import io
import re
from typing import Dict, Any, List
from urllib.parse import urlparse
import hashlib
import os
import tempfile

try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class PDFTool:
    name = "pdf_extract"
    description = "Extract text and metadata from PDF files. Args: url (str), extract_images(bool)=False, max_pages(int)=50"
    
    @staticmethod
    def metadata():
        return {
            "name": PDFTool.name, 
            "description": PDFTool.description, 
            "args": {
                "url": "string", 
                "extract_images": "bool",
                "max_pages": "int"
            }
        }

    @staticmethod
    async def run(url: str, extract_images: bool = False, max_pages: int = 50):
        if not url:
            return {"error": "empty url"}
        
        if not PDF_AVAILABLE:
            return {"error": "PDF processing libraries not available. Please install PyPDF2 and pdfplumber."}
        
        try:
            # 下载 PDF 文件
            pdf_content = await PDFTool._download_pdf(url)
            if 'error' in pdf_content:
                return pdf_content
            
            # 提取文本和元数据
            result = await PDFTool._extract_pdf_content(
                pdf_content['content'], 
                extract_images, 
                max_pages
            )
            
            result['url'] = url
            result['file_size'] = pdf_content['size']
            
            return result
        except Exception as e:
            return {"error": f"PDF processing failed: {str(e)}"}
    
    @staticmethod
    async def _download_pdf(url: str) -> Dict[str, Any]:
        """下载 PDF 文件"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        if 'pdf' not in content_type:
                            # 检查 URL 是否以 .pdf 结尾
                            if not url.lower().endswith('.pdf'):
                                return {"error": "URL does not appear to be a PDF file"}
                        
                        content = await response.read()
                        
                        # 检查文件大小（限制为 50MB）
                        if len(content) > 50 * 1024 * 1024:
                            return {"error": "PDF file too large (>50MB)"}
                        
                        return {
                            "content": content,
                            "size": len(content)
                        }
                    else:
                        return {"error": f"Failed to download PDF: HTTP {response.status}"}
        except Exception as e:
            return {"error": f"Download failed: {str(e)}"}
    
    @staticmethod
    async def _extract_pdf_content(pdf_content: bytes, extract_images: bool, max_pages: int) -> Dict[str, Any]:
        """提取 PDF 内容"""
        try:
            # 使用 io.BytesIO 创建文件对象
            pdf_file = io.BytesIO(pdf_content)
            
            # 使用 PyPDF2 提取基本信息
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # 获取元数据
            metadata = {}
            if pdf_reader.metadata:
                metadata = {
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'subject': pdf_reader.metadata.get('/Subject', ''),
                    'creator': pdf_reader.metadata.get('/Creator', ''),
                    'producer': pdf_reader.metadata.get('/Producer', ''),
                    'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                    'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
                }
            
            total_pages = len(pdf_reader.pages)
            pages_to_process = min(total_pages, max_pages)
            
            # 使用 pdfplumber 提取文本（更准确）
            pdf_file.seek(0)  # 重置文件指针
            
            text_content = []
            tables = []
            
            with pdfplumber.open(pdf_file) as pdf:
                for i, page in enumerate(pdf.pages[:pages_to_process]):
                    # 提取文本
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(f"--- Page {i+1} ---\n{page_text}")
                    
                    # 提取表格
                    page_tables = page.extract_tables()
                    if page_tables:
                        for j, table in enumerate(page_tables):
                            tables.append({
                                'page': i+1,
                                'table_index': j+1,
                                'data': table
                            })
            
            # 合并所有文本
            full_text = '\n\n'.join(text_content)
            
            # 生成摘要
            summary = PDFTool._generate_summary(full_text)
            
            # 提取关键信息
            key_info = PDFTool._extract_key_information(full_text)
            
            result = {
                'status': 'success',
                'metadata': metadata,
                'total_pages': total_pages,
                'processed_pages': pages_to_process,
                'text_length': len(full_text),
                'text_content': full_text[:5000],  # 限制返回的文本长度
                'full_text_available': len(full_text) > 5000,
                'summary': summary,
                'key_information': key_info,
                'tables_count': len(tables),
                'tables': tables[:5] if tables else []  # 只返回前5个表格
            }
            
            return result
            
        except Exception as e:
            return {"error": f"PDF content extraction failed: {str(e)}"}
    
    @staticmethod
    def _generate_summary(text: str) -> str:
        """生成文档摘要"""
        if not text or len(text) < 100:
            return "Document too short to summarize"
        
        # 简单的摘要生成：提取前几句话
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # 取前3句作为摘要
        summary_sentences = sentences[:3]
        summary = '. '.join(summary_sentences)
        
        if len(summary) > 500:
            summary = summary[:500] + '...'
        
        return summary
    
    @staticmethod
    def _extract_key_information(text: str) -> Dict[str, List[str]]:
        """提取关键信息"""
        key_info = {
            'emails': [],
            'urls': [],
            'dates': [],
            'numbers': [],
            'keywords': []
        }
        
        # 提取邮箱
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        key_info['emails'] = list(set(re.findall(email_pattern, text)))[:10]
        
        # 提取 URL
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        key_info['urls'] = list(set(re.findall(url_pattern, text)))[:10]
        
        # 提取日期
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4}\b'
        ]
        for pattern in date_patterns:
            dates = re.findall(pattern, text, re.IGNORECASE)
            key_info['dates'].extend(dates)
        key_info['dates'] = list(set(key_info['dates']))[:10]
        
        # 提取重要数字
        number_pattern = r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b'
        numbers = re.findall(number_pattern, text)
        # 过滤掉太小的数字
        key_info['numbers'] = [n for n in set(numbers) if float(n.replace(',', '')) > 100][:10]
        
        # 提取关键词（简单的词频分析）
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        word_freq = {}
        for word in words:
            if word not in ['this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'much', 'some', 'these', 'many', 'would', 'there']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 取频率最高的词作为关键词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        key_info['keywords'] = [word for word, freq in sorted_words[:15] if freq > 2]
        
        return key_info

class PDFSummaryTool:
    name = "pdf_summarize"
    description = "Generate detailed summary of PDF content. Args: url (str), summary_length(str)='medium'"
    
    @staticmethod
    def metadata():
        return {
            "name": PDFSummaryTool.name, 
            "description": PDFSummaryTool.description, 
            "args": {
                "url": "string", 
                "summary_length": "string"
            }
        }

    @staticmethod
    async def run(url: str, summary_length: str = 'medium'):
        if not url:
            return {"error": "empty url"}
        
        try:
            # 首先提取 PDF 内容
            pdf_result = await PDFTool.run(url, extract_images=False, max_pages=20)
            
            if 'error' in pdf_result:
                return pdf_result
            
            text_content = pdf_result.get('text_content', '')
            if not text_content:
                return {"error": "No text content found in PDF"}
            
            # 根据长度要求生成摘要
            if summary_length == 'short':
                summary = PDFSummaryTool._generate_short_summary(text_content)
            elif summary_length == 'long':
                summary = PDFSummaryTool._generate_long_summary(text_content)
            else:  # medium
                summary = PDFSummaryTool._generate_medium_summary(text_content)
            
            return {
                'url': url,
                'summary_length': summary_length,
                'summary': summary,
                'original_length': len(text_content),
                'compression_ratio': len(summary) / len(text_content) if text_content else 0,
                'metadata': pdf_result.get('metadata', {}),
                'key_information': pdf_result.get('key_information', {})
            }
        except Exception as e:
            return {"error": f"PDF summarization failed: {str(e)}"}
    
    @staticmethod
    def _generate_short_summary(text: str) -> str:
        """生成简短摘要"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        # 选择最重要的2-3句
        important_sentences = sentences[:3]
        summary = '. '.join(important_sentences)
        
        if len(summary) > 300:
            summary = summary[:300] + '...'
        
        return summary
    
    @staticmethod
    def _generate_medium_summary(text: str) -> str:
        """生成中等长度摘要"""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]
        
        # 选择前几个段落的关键句子
        summary_parts = []
        for para in paragraphs[:5]:
            sentences = re.split(r'[.!?]+', para)
            if sentences:
                # 取每个段落的第一句
                first_sentence = sentences[0].strip()
                if len(first_sentence) > 20:
                    summary_parts.append(first_sentence)
        
        summary = '. '.join(summary_parts)
        
        if len(summary) > 800:
            summary = summary[:800] + '...'
        
        return summary
    
    @staticmethod
    def _generate_long_summary(text: str) -> str:
        """生成详细摘要"""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 30]
        
        # 选择更多内容
        summary_parts = []
        for para in paragraphs[:10]:
            sentences = re.split(r'[.!?]+', para)
            # 取每个段落的前两句
            for sentence in sentences[:2]:
                sentence = sentence.strip()
                if len(sentence) > 20:
                    summary_parts.append(sentence)
        
        summary = '. '.join(summary_parts)
        
        if len(summary) > 1500:
            summary = summary[:1500] + '...'
        
        return summary