import asyncio
import hashlib
import re
from typing import Dict, Any, List, Set, Tuple
from difflib import SequenceMatcher
from collections import defaultdict
import json

class DedupTool:
    name = "content_dedup"
    description = "Remove duplicate content from text or list of documents. Args: content (str|list), similarity_threshold(float)=0.8, method(str)='hash'"
    
    @staticmethod
    def metadata():
        return {
            "name": DedupTool.name, 
            "description": DedupTool.description, 
            "args": {
                "content": "string|array", 
                "similarity_threshold": "float",
                "method": "string"
            }
        }

    @staticmethod
    async def run(content, similarity_threshold: float = 0.8, method: str = 'hash'):
        if not content:
            return {"error": "empty content"}
        
        try:
            if isinstance(content, str):
                # 单个文档去重
                result = await DedupTool._dedup_single_document(content, similarity_threshold, method)
            elif isinstance(content, list):
                # 多文档去重
                result = await DedupTool._dedup_multiple_documents(content, similarity_threshold, method)
            else:
                return {"error": "content must be string or list"}
            
            return result
        except Exception as e:
            return {"error": f"Deduplication failed: {str(e)}"}
    
    @staticmethod
    async def _dedup_single_document(content: str, similarity_threshold: float, method: str) -> Dict[str, Any]:
        """单个文档内部去重"""
        original_length = len(content)
        
        if method == 'hash':
            deduplicated = DedupTool._hash_based_dedup(content)
        elif method == 'similarity':
            deduplicated = DedupTool._similarity_based_dedup(content, similarity_threshold)
        elif method == 'semantic':
            deduplicated = DedupTool._semantic_dedup(content, similarity_threshold)
        else:
            return {"error": f"Unknown method: {method}"}
        
        return {
            'method': method,
            'original_length': original_length,
            'deduplicated_length': len(deduplicated),
            'reduction_ratio': (original_length - len(deduplicated)) / original_length if original_length > 0 else 0,
            'deduplicated_content': deduplicated,
            'duplicates_found': original_length != len(deduplicated)
        }
    
    @staticmethod
    async def _dedup_multiple_documents(documents: List[str], similarity_threshold: float, method: str) -> Dict[str, Any]:
        """多文档间去重"""
        if not documents:
            return {"error": "empty document list"}
        
        original_count = len(documents)
        
        if method == 'hash':
            unique_docs, duplicates = DedupTool._hash_based_multi_dedup(documents)
        elif method == 'similarity':
            unique_docs, duplicates = DedupTool._similarity_based_multi_dedup(documents, similarity_threshold)
        elif method == 'semantic':
            unique_docs, duplicates = DedupTool._semantic_multi_dedup(documents, similarity_threshold)
        else:
            return {"error": f"Unknown method: {method}"}
        
        return {
            'method': method,
            'original_count': original_count,
            'unique_count': len(unique_docs),
            'duplicates_count': len(duplicates),
            'reduction_ratio': len(duplicates) / original_count if original_count > 0 else 0,
            'unique_documents': unique_docs,
            'duplicate_groups': duplicates,
            'duplicates_found': len(duplicates) > 0
        }
    
    @staticmethod
    def _hash_based_dedup(content: str) -> str:
        """基于哈希的去重"""
        lines = content.split('\n')
        seen_hashes = set()
        unique_lines = []
        
        for line in lines:
            line_hash = hashlib.md5(line.strip().encode()).hexdigest()
            if line_hash not in seen_hashes:
                seen_hashes.add(line_hash)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    @staticmethod
    def _similarity_based_dedup(content: str, threshold: float) -> str:
        """基于相似度的去重"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        unique_sentences = []
        
        for sentence in sentences:
            is_duplicate = False
            for unique_sentence in unique_sentences:
                similarity = SequenceMatcher(None, sentence.lower(), unique_sentence.lower()).ratio()
                if similarity >= threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_sentences.append(sentence)
        
        return '. '.join(unique_sentences)
    
    @staticmethod
    def _semantic_dedup(content: str, threshold: float) -> str:
        """基于语义的去重（简化版）"""
        # 这里使用简化的语义去重，基于关键词重叠
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        unique_sentences = []
        
        for sentence in sentences:
            sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
            is_duplicate = False
            
            for unique_sentence in unique_sentences:
                unique_words = set(re.findall(r'\b\w+\b', unique_sentence.lower()))
                
                # 计算词汇重叠率
                if len(sentence_words) > 0 and len(unique_words) > 0:
                    overlap = len(sentence_words & unique_words)
                    overlap_ratio = overlap / min(len(sentence_words), len(unique_words))
                    
                    if overlap_ratio >= threshold:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_sentences.append(sentence)
        
        return '. '.join(unique_sentences)
    
    @staticmethod
    def _hash_based_multi_dedup(documents: List[str]) -> Tuple[List[str], List[List[int]]]:
        """多文档哈希去重"""
        doc_hashes = {}
        unique_docs = []
        duplicates = []
        
        for i, doc in enumerate(documents):
            doc_hash = hashlib.md5(doc.encode()).hexdigest()
            
            if doc_hash in doc_hashes:
                # 找到重复文档
                original_index = doc_hashes[doc_hash]
                # 查找是否已有重复组
                found_group = False
                for dup_group in duplicates:
                    if original_index in dup_group:
                        dup_group.append(i)
                        found_group = True
                        break
                
                if not found_group:
                    duplicates.append([original_index, i])
            else:
                doc_hashes[doc_hash] = i
                unique_docs.append(doc)
        
        return unique_docs, duplicates
    
    @staticmethod
    def _similarity_based_multi_dedup(documents: List[str], threshold: float) -> Tuple[List[str], List[List[int]]]:
        """多文档相似度去重"""
        unique_docs = []
        unique_indices = []
        duplicates = []
        
        for i, doc in enumerate(documents):
            is_duplicate = False
            duplicate_of = -1
            
            for j, unique_doc in enumerate(unique_docs):
                similarity = SequenceMatcher(None, doc.lower(), unique_doc.lower()).ratio()
                if similarity >= threshold:
                    is_duplicate = True
                    duplicate_of = unique_indices[j]
                    break
            
            if is_duplicate:
                # 查找是否已有重复组
                found_group = False
                for dup_group in duplicates:
                    if duplicate_of in dup_group:
                        dup_group.append(i)
                        found_group = True
                        break
                
                if not found_group:
                    duplicates.append([duplicate_of, i])
            else:
                unique_docs.append(doc)
                unique_indices.append(i)
        
        return unique_docs, duplicates
    
    @staticmethod
    def _semantic_multi_dedup(documents: List[str], threshold: float) -> Tuple[List[str], List[List[int]]]:
        """多文档语义去重"""
        unique_docs = []
        unique_indices = []
        duplicates = []
        
        for i, doc in enumerate(documents):
            doc_words = set(re.findall(r'\b\w+\b', doc.lower()))
            is_duplicate = False
            duplicate_of = -1
            
            for j, unique_doc in enumerate(unique_docs):
                unique_words = set(re.findall(r'\b\w+\b', unique_doc.lower()))
                
                if len(doc_words) > 0 and len(unique_words) > 0:
                    overlap = len(doc_words & unique_words)
                    overlap_ratio = overlap / min(len(doc_words), len(unique_words))
                    
                    if overlap_ratio >= threshold:
                        is_duplicate = True
                        duplicate_of = unique_indices[j]
                        break
            
            if is_duplicate:
                # 查找是否已有重复组
                found_group = False
                for dup_group in duplicates:
                    if duplicate_of in dup_group:
                        dup_group.append(i)
                        found_group = True
                        break
                
                if not found_group:
                    duplicates.append([duplicate_of, i])
            else:
                unique_docs.append(doc)
                unique_indices.append(i)
        
        return unique_docs, duplicates

class MergeTool:
    name = "content_merge"
    description = "Merge similar content intelligently. Args: contents (list), merge_strategy(str)='smart', similarity_threshold(float)=0.7"
    
    @staticmethod
    def metadata():
        return {
            "name": MergeTool.name, 
            "description": MergeTool.description, 
            "args": {
                "contents": "array", 
                "merge_strategy": "string",
                "similarity_threshold": "float"
            }
        }

    @staticmethod
    async def run(contents: List[str], merge_strategy: str = 'smart', similarity_threshold: float = 0.7):
        if not contents or len(contents) < 2:
            return {"error": "need at least 2 contents to merge"}
        
        try:
            if merge_strategy == 'smart':
                result = MergeTool._smart_merge(contents, similarity_threshold)
            elif merge_strategy == 'longest':
                result = MergeTool._longest_merge(contents)
            elif merge_strategy == 'concatenate':
                result = MergeTool._concatenate_merge(contents)
            elif merge_strategy == 'union':
                result = MergeTool._union_merge(contents)
            else:
                return {"error": f"Unknown merge strategy: {merge_strategy}"}
            
            return result
        except Exception as e:
            return {"error": f"Merge failed: {str(e)}"}
    
    @staticmethod
    def _smart_merge(contents: List[str], threshold: float) -> Dict[str, Any]:
        """智能合并：保留最完整的信息"""
        if not contents:
            return {"merged_content": "", "merge_info": {}}
        
        # 按长度排序，优先保留较长的内容
        sorted_contents = sorted(enumerate(contents), key=lambda x: len(x[1]), reverse=True)
        
        merged_sentences = []
        used_indices = set()
        
        for i, (original_index, content) in enumerate(sorted_contents):
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            for sentence in sentences:
                # 检查是否与已有句子相似
                is_similar = False
                for existing_sentence in merged_sentences:
                    similarity = SequenceMatcher(None, sentence.lower(), existing_sentence.lower()).ratio()
                    if similarity >= threshold:
                        is_similar = True
                        # 如果新句子更长，替换现有句子
                        if len(sentence) > len(existing_sentence):
                            idx = merged_sentences.index(existing_sentence)
                            merged_sentences[idx] = sentence
                        break
                
                if not is_similar:
                    merged_sentences.append(sentence)
            
            used_indices.add(original_index)
        
        merged_content = '. '.join(merged_sentences)
        
        return {
            'merged_content': merged_content,
            'merge_info': {
                'strategy': 'smart',
                'original_count': len(contents),
                'used_indices': list(used_indices),
                'original_total_length': sum(len(c) for c in contents),
                'merged_length': len(merged_content),
                'compression_ratio': 1 - (len(merged_content) / sum(len(c) for c in contents)) if contents else 0
            }
        }
    
    @staticmethod
    def _longest_merge(contents: List[str]) -> Dict[str, Any]:
        """选择最长的内容"""
        longest_content = max(contents, key=len)
        longest_index = contents.index(longest_content)
        
        return {
            'merged_content': longest_content,
            'merge_info': {
                'strategy': 'longest',
                'selected_index': longest_index,
                'selected_length': len(longest_content),
                'original_count': len(contents)
            }
        }
    
    @staticmethod
    def _concatenate_merge(contents: List[str]) -> Dict[str, Any]:
        """简单拼接"""
        merged_content = '\n\n'.join(contents)
        
        return {
            'merged_content': merged_content,
            'merge_info': {
                'strategy': 'concatenate',
                'original_count': len(contents),
                'merged_length': len(merged_content)
            }
        }
    
    @staticmethod
    def _union_merge(contents: List[str]) -> Dict[str, Any]:
        """合并所有唯一句子"""
        all_sentences = []
        
        for content in contents:
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            all_sentences.extend(sentences)
        
        # 去重
        unique_sentences = []
        seen = set()
        
        for sentence in all_sentences:
            sentence_lower = sentence.lower().strip()
            if sentence_lower not in seen:
                seen.add(sentence_lower)
                unique_sentences.append(sentence)
        
        merged_content = '. '.join(unique_sentences)
        
        return {
            'merged_content': merged_content,
            'merge_info': {
                'strategy': 'union',
                'original_count': len(contents),
                'total_sentences': len(all_sentences),
                'unique_sentences': len(unique_sentences),
                'dedup_ratio': 1 - (len(unique_sentences) / len(all_sentences)) if all_sentences else 0,
                'merged_length': len(merged_content)
            }
        }

class TextCleanTool:
    name = "text_clean"
    description = "Clean and normalize text content. Args: text (str), remove_duplicates(bool)=True, normalize_whitespace(bool)=True, remove_empty_lines(bool)=True"
    
    @staticmethod
    def metadata():
        return {
            "name": TextCleanTool.name, 
            "description": TextCleanTool.description, 
            "args": {
                "text": "string", 
                "remove_duplicates": "bool",
                "normalize_whitespace": "bool",
                "remove_empty_lines": "bool"
            }
        }

    @staticmethod
    async def run(text: str, remove_duplicates: bool = True, normalize_whitespace: bool = True, remove_empty_lines: bool = True):
        if not text:
            return {"error": "empty text"}
        
        try:
            original_length = len(text)
            cleaned_text = text
            
            # 标准化空白字符
            if normalize_whitespace:
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
                cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
            
            # 移除空行
            if remove_empty_lines:
                lines = cleaned_text.split('\n')
                lines = [line for line in lines if line.strip()]
                cleaned_text = '\n'.join(lines)
            
            # 移除重复行
            if remove_duplicates:
                lines = cleaned_text.split('\n')
                seen = set()
                unique_lines = []
                
                for line in lines:
                    line_clean = line.strip().lower()
                    if line_clean not in seen:
                        seen.add(line_clean)
                        unique_lines.append(line)
                
                cleaned_text = '\n'.join(unique_lines)
            
            # 清理特殊字符
            cleaned_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', cleaned_text)
            
            return {
                'original_length': original_length,
                'cleaned_length': len(cleaned_text),
                'reduction_ratio': (original_length - len(cleaned_text)) / original_length if original_length > 0 else 0,
                'cleaned_text': cleaned_text,
                'operations_applied': {
                    'normalize_whitespace': normalize_whitespace,
                    'remove_empty_lines': remove_empty_lines,
                    'remove_duplicates': remove_duplicates
                }
            }
        except Exception as e:
            return {"error": f"Text cleaning failed: {str(e)}"}