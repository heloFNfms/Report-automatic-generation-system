import asyncio
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from .mcp_client import MCPClient
from .deepseek_client import DeepSeekClient
from .textops import (
    flatten_snippets, deduplicate_citations, rerank_texts, 
    smart_chunk_by_strategy, budget_context, count_tokens
)
from .vectorstore import Embedding, FaissStore
from .rag_config import RAGConfig
from .rag_cache import RAGCache, get_rag_cache

logger = logging.getLogger(__name__)

class EnhancedRAGPipeline:
    """增强的RAG流水线实现"""
    
    def __init__(self, mcp_client: MCPClient, deepseek_client: DeepSeekClient, 
                 embedding: Embedding, vector_store: FaissStore, config: RAGConfig = None):
        self.mcp = mcp_client
        self.deepseek = deepseek_client
        self.embed = embedding
        self.store = vector_store
        self.config = config or RAGConfig()
        
        # RAG缓存系统
        self.cache = get_rag_cache(
            cache_dir=self.config.cache_dir,
            max_cache_size=self.config.max_cache_size,
            default_ttl_hours=self.config.cache_ttl_hours,
            similarity_threshold=self.config.cache_similarity_threshold,
            embedding_model=self.config.embedding_model
        )
        
    async def generate_section_content(self, task_info: Dict[str, Any], h1: str, h2: str) -> Dict[str, Any]:
        """生成章节内容的完整RAG流水线"""
        try:
            # 构建缓存键
            cache_key = f"{task_info.get('project_name', '')}_{h1}_{h2}"
            
            # Step 1: 检查缓存
            if self.config.enable_cache:
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for {h1} - {h2}")
                    return cached_result[0] if isinstance(cached_result, list) and cached_result else cached_result
            
            # Step 2: 智能查询生成
            queries = await self._generate_search_queries(task_info, h1, h2)
            logger.info(f"Generated {len(queries)} search queries for {h1} - {h2}")
            
            # Step 3: MCP多源检索
            all_documents = await self._multi_source_retrieval(queries)
            logger.info(f"Retrieved {len(all_documents)} documents from MCP sources")
            
            # Step 4: 向量存储和检索
            retrieved_docs = await self._vector_retrieval(queries, all_documents)
            logger.info(f"Vector retrieval returned {len(retrieved_docs)} documents")
            
            # Step 5: 重排序和去重
            reranked_docs = await self._rerank_and_deduplicate(queries[0], retrieved_docs)
            logger.info(f"After reranking and deduplication: {len(reranked_docs)} documents")
            
            # Step 6: 智能压缩
            compressed_context = await self._compress_context(reranked_docs)
            logger.info(f"Compressed context to {count_tokens(compressed_context)} tokens")
            
            # Step 7: 生成内容
            content = await self._generate_content_with_context(task_info, h1, h2, compressed_context, reranked_docs)
            
            result = {
                "h1": h1,
                "h2": h2,
                "content": content["content"],
                "参考网址": content["references"],
                "metadata": {
                    "queries_used": queries,
                    "documents_retrieved": len(all_documents),
                    "documents_after_rerank": len(reranked_docs),
                    "context_tokens": count_tokens(compressed_context),
                    "processing_steps": [
                        "cache_check", "query_generation", "mcp_retrieval", "vector_retrieval", 
                        "rerank_dedup", "compression", "content_generation", "cache_store"
                    ]
                }
            }
            
            # Step 8: 缓存结果
            if self.config.enable_cache and result:
                await self.cache.set(cache_key, [result], ttl_hours=self.config.cache_ttl_hours)
                logger.info(f"Cached result for {h1} - {h2}")
            
            return result
            
        except Exception as e:
            logger.error(f"RAG pipeline failed for {h1}-{h2}: {str(e)}")
            return {
                "h1": h1,
                "h2": h2,
                "content": f"生成内容时出现错误: {str(e)}",
                "参考网址": [],
                "metadata": {"error": str(e)}
            }
    
    async def _generate_search_queries(self, task_info: Dict[str, Any], h1: str, h2: str) -> List[str]:
        """智能生成搜索查询"""
        base_query = f"{task_info['project_name']} {task_info['research_content']} {h1} {h2}"
        queries = [base_query]
        
        if self.config.enable_query_expansion:
            # 使用DeepSeek生成扩展查询
            expansion_prompt = f"""
基于以下信息生成3个不同角度的学术搜索查询，用于检索相关研究文献：

项目名称: {task_info['project_name']}
研究内容: {task_info['research_content']}
章节标题: {h1} - {h2}

请生成3个查询，每个查询应该：
1. 包含核心关键词
2. 从不同角度探索主题
3. 适合学术文献搜索

返回格式：
1. [查询1]
2. [查询2] 
3. [查询3]
"""
            
            try:
                response = await self.deepseek.chat_async(expansion_prompt)
                expanded_queries = self._parse_queries_from_response(response)
                queries.extend(expanded_queries)
                logger.info(f"Query expansion generated {len(expanded_queries)} additional queries")
            except Exception as e:
                logger.warning(f"Query expansion failed: {e}, using base query only")
        
        return queries[:4]  # 限制最多4个查询
    
    def _parse_queries_from_response(self, response: str) -> List[str]:
        """从DeepSeek响应中解析查询"""
        queries = []
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '-', '•')) or len(line) > 10):
                # 清理格式
                query = line.lstrip('123.-•').strip()
                if query and len(query) > 5:
                    queries.append(query)
        return queries
    
    async def _multi_source_retrieval(self, queries: List[str]) -> List[Dict[str, Any]]:
        """多源MCP检索"""
        all_documents = []
        
        # 定义检索源
        sources = [
            ("arxiv_search", {"max_results": self.config.max_search_results}),
            ("crossref_search", {"max_results": self.config.max_search_results}),
        ]
        
        for query in queries:
            for source_name, base_params in sources:
                try:
                    params = {**base_params, "query": query}
                    result = await self.mcp.invoke(source_name, params)
                    
                    if isinstance(result, dict) and "items" in result:
                        documents = result["items"]
                    elif isinstance(result, list):
                        documents = result
                    else:
                        documents = [result] if result else []
                    
                    # 标记文档来源
                    for doc in documents:
                        if isinstance(doc, dict):
                            doc["_source"] = source_name
                            doc["_query"] = query
                    
                    all_documents.extend(documents)
                    logger.debug(f"Retrieved {len(documents)} docs from {source_name} for query: {query[:50]}...")
                    
                except Exception as e:
                    logger.warning(f"Failed to retrieve from {source_name} with query '{query[:50]}...': {e}")
                    continue
        
        return all_documents
    
    async def _vector_retrieval(self, queries: List[str], documents: List[Dict[str, Any]]) -> List[Tuple[str, Dict[str, Any]]]:
        """向量检索和存储"""
        # 提取文本和元数据
        texts = flatten_snippets(documents)
        metas = []
        
        for i, doc in enumerate(documents):
            meta = {
                "url": doc.get("url") or doc.get("link"),
                "title": doc.get("title") or doc.get("id"),
                "source": doc.get("_source", "unknown"),
                "query": doc.get("_query", ""),
                "doc_index": i
            }
            metas.append(meta)
        
        # 存储到向量数据库
        if texts:
            try:
                embeddings = self.embed.encode(texts)
                self.store.add(embeddings, texts, metas)
                logger.info(f"Added {len(texts)} documents to vector store")
            except Exception as e:
                logger.error(f"Failed to add documents to vector store: {e}")
        
        # 检索相关文档
        retrieved_docs = []
        for query in queries:
            try:
                query_embedding = self.embed.encode([query])[0]
                results = self.store.search(query_embedding, top_k=self.config.max_retrieved_docs)
                retrieved_docs.extend(results)
            except Exception as e:
                logger.warning(f"Vector search failed for query '{query[:50]}...': {e}")
        
        # 去重（基于URL和标题）
        seen = set()
        unique_docs = []
        for text, meta in retrieved_docs:
            key = (meta.get("url", ""), meta.get("title", ""))
            if key not in seen:
                seen.add(key)
                unique_docs.append((text, meta))
        
        return unique_docs
    
    async def _rerank_and_deduplicate(self, primary_query: str, documents: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[str, Dict[str, Any]]]:
        """重排序和去重"""
        if not documents:
            return []
        
        # 提取文本进行重排序
        texts = [doc[0] for doc in documents]
        metas = [doc[1] for doc in documents]
        
        # 去重
        deduplicated_texts = deduplicate_citations(texts, self.config.similarity_threshold)
        
        # 重建文档列表
        deduplicated_docs = []
        for dedup_text in deduplicated_texts:
            # 找到对应的元数据
            for i, original_text in enumerate(texts):
                if original_text == dedup_text:
                    deduplicated_docs.append((dedup_text, metas[i]))
                    break
        
        # BM25重排序
        if len(deduplicated_docs) > 1:
            try:
                reranked_results = rerank_texts(primary_query, [doc[0] for doc in deduplicated_docs], self.config.rerank_top_k)
                
                # 重建带元数据的结果
                reranked_docs = []
                for reranked_text, score in reranked_results:
                    for text, meta in deduplicated_docs:
                        if text == reranked_text:
                            meta_with_score = {**meta, "rerank_score": score}
                            reranked_docs.append((text, meta_with_score))
                            break
                
                return reranked_docs
            except Exception as e:
                logger.warning(f"Reranking failed: {e}, using original order")
        
        return deduplicated_docs[:self.config.rerank_top_k]
    
    async def _compress_context(self, documents: List[Tuple[str, Dict[str, Any]]]) -> str:
        """智能压缩上下文"""
        if not documents:
            return ""
        
        # 提取文本
        texts = [doc[0] for doc in documents]
        
        # 智能分块
        all_chunks = []
        for text in texts:
            chunks = smart_chunk_by_strategy(
                text, 
                strategy=self.config.chunk_strategy, 
                max_tokens=self.config.chunk_max_tokens
            )
            all_chunks.extend(chunks)
        
        # 根据token预算选择最佳块
        selected_chunks = budget_context(all_chunks, self.config.max_context_tokens)
        
        # 如果启用语义压缩，使用DeepSeek进一步压缩
        if self.config.enable_semantic_compression and len(selected_chunks) > 3:
            try:
                combined_text = "\n\n".join(selected_chunks)
                compression_prompt = f"""
请对以下学术文献内容进行智能压缩，保留核心信息和关键观点：

{combined_text}

要求：
1. 保留所有重要的研究发现和数据
2. 保持学术表达的准确性
3. 去除冗余信息
4. 控制在{self.config.max_context_tokens}个token以内
"""
                
                compressed = await self.deepseek.chat_async(compression_prompt)
                if compressed and len(compressed) < len(combined_text):
                    return compressed
            except Exception as e:
                logger.warning(f"Semantic compression failed: {e}, using chunk selection")
        
        return "\n\n".join(selected_chunks)
    
    async def _generate_content_with_context(self, task_info: Dict[str, Any], h1: str, h2: str, 
                                           context: str, documents: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """基于上下文生成内容"""
        # 提取参考链接
        references = []
        for _, meta in documents:
            url = meta.get("url")
            title = meta.get("title", "未知标题")
            if url and url not in [ref.get("url") for ref in references]:
                references.append({"url": url, "title": title})
        
        # 构建生成提示
        generation_prompt = f"""
基于以下研究资料，为学术报告撰写「{h1} - {h2}」章节的内容。

## 项目信息
项目名称：{task_info['project_name']}
研究内容：{task_info['research_content']}

## 参考资料
{context}

## 撰写要求
1. 内容应具有学术性和专业性
2. 逻辑清晰，结构完整
3. 适当引用研究发现和数据
4. 字数控制在800-1200字
5. 使用中文撰写

请撰写该章节的内容：
"""
        
        try:
            content = await self.deepseek.chat_async(generation_prompt)
            return {
                "content": content,
                "references": references[:10]  # 限制参考链接数量
            }
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return {
                "content": f"内容生成失败：{str(e)}",
                "references": references[:5]
            }