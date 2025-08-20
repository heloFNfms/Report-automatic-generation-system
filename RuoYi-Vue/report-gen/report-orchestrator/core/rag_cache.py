import os
import json
import hashlib
import asyncio
from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass, asdict
import logging
from sentence_transformers import SentenceTransformer
import faiss
from .vectorstore import Embedding, FaissStore

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """缓存条目"""
    query_hash: str
    query_text: str
    query_embedding: List[float]
    results: List[Dict[str, Any]]
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_hours: int = 24
    similarity_threshold: float = 0.85
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() > self.created_at + timedelta(hours=self.ttl_hours)
    
    def update_access(self):
        """更新访问信息"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query_hash": self.query_hash,
            "query_text": self.query_text,
            "query_embedding": self.query_embedding,
            "results": self.results,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "ttl_hours": self.ttl_hours,
            "similarity_threshold": self.similarity_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """从字典创建"""
        return cls(
            query_hash=data["query_hash"],
            query_text=data["query_text"],
            query_embedding=data["query_embedding"],
            results=data["results"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data["access_count"],
            ttl_hours=data.get("ttl_hours", 24),
            similarity_threshold=data.get("similarity_threshold", 0.85)
        )

class RAGCache:
    """RAG缓存系统"""
    
    def __init__(self, 
                 cache_dir: str = "./cache",
                 max_cache_size: int = 10000,
                 default_ttl_hours: int = 24,
                 similarity_threshold: float = 0.85,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size
        self.default_ttl_hours = default_ttl_hours
        self.similarity_threshold = similarity_threshold
        
        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)
        
        # 初始化embedding模型
        self.embedding = Embedding(embedding_model)
        
        # 缓存文件路径
        self.cache_file = os.path.join(cache_dir, "rag_cache.json")
        self.query_index_file = os.path.join(cache_dir, "query_index.faiss")
        self.query_meta_file = os.path.join(cache_dir, "query_meta.json")
        
        # 内存缓存
        self.cache: Dict[str, CacheEntry] = {}
        
        # 查询向量索引（用于相似度搜索）
        self.query_store = FaissStore(
            dim=384,  # all-MiniLM-L6-v2的维度
            index_path=self.query_index_file,
            meta_path=self.query_meta_file
        )
        
        # 加载缓存
        self.load_cache()
        
        # 启动清理任务
        self._cleanup_task = None
        self.start_cleanup_task()
    
    def _get_query_hash(self, query: str) -> str:
        """生成查询哈希"""
        return hashlib.sha256(query.encode('utf-8')).hexdigest()
    
    async def get(self, query: str, 
                  similarity_threshold: Optional[float] = None) -> Optional[List[Dict[str, Any]]]:
        """获取缓存结果"""
        threshold = similarity_threshold or self.similarity_threshold
        query_hash = self._get_query_hash(query)
        
        # 1. 精确匹配
        if query_hash in self.cache:
            entry = self.cache[query_hash]
            if not entry.is_expired():
                entry.update_access()
                logger.info(f"缓存精确命中: {query[:50]}...")
                return entry.results
            else:
                # 删除过期条目
                await self._remove_entry(query_hash)
        
        # 2. 相似度匹配
        similar_entry = await self._find_similar_query(query, threshold)
        if similar_entry:
            similar_entry.update_access()
            logger.info(f"缓存相似命中: {query[:50]}... -> {similar_entry.query_text[:50]}...")
            return similar_entry.results
        
        logger.debug(f"缓存未命中: {query[:50]}...")
        return None
    
    async def set(self, query: str, results: List[Dict[str, Any]], 
                  ttl_hours: Optional[int] = None) -> None:
        """设置缓存"""
        ttl = ttl_hours or self.default_ttl_hours
        query_hash = self._get_query_hash(query)
        
        # 生成查询embedding
        query_embedding = self.embedding.encode([query])[0].tolist()
        
        # 创建缓存条目
        entry = CacheEntry(
            query_hash=query_hash,
            query_text=query,
            query_embedding=query_embedding,
            results=results,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            ttl_hours=ttl,
            similarity_threshold=self.similarity_threshold
        )
        
        # 添加到内存缓存
        self.cache[query_hash] = entry
        
        # 添加到向量索引
        try:
            self.query_store.add(
                np.array([query_embedding]),
                [query],
                [{"query_hash": query_hash, "query_text": query}]
            )
        except Exception as e:
            logger.warning(f"向量索引添加失败: {e}")
        
        # 检查缓存大小限制
        if len(self.cache) > self.max_cache_size:
            await self._evict_lru()
        
        # 保存缓存
        await self.save_cache()
        
        logger.info(f"缓存已设置: {query[:50]}... (TTL: {ttl}h)")
    
    async def _find_similar_query(self, query: str, threshold: float) -> Optional[CacheEntry]:
        """查找相似查询"""
        try:
            query_embedding = self.embedding.encode([query])[0]
            
            # 在向量索引中搜索
            results = self.query_store.search(query_embedding, top_k=5)
            
            for text, meta in results:
                query_hash = meta.get("query_hash")
                if query_hash and query_hash in self.cache:
                    entry = self.cache[query_hash]
                    
                    # 检查是否过期
                    if entry.is_expired():
                        await self._remove_entry(query_hash)
                        continue
                    
                    # 计算相似度
                    similarity = self._calculate_similarity(
                        query_embedding, 
                        np.array(entry.query_embedding)
                    )
                    
                    if similarity >= threshold:
                        return entry
            
            return None
            
        except Exception as e:
            logger.warning(f"相似度搜索失败: {e}")
            return None
    
    def _calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """计算余弦相似度"""
        # 归一化
        emb1_norm = emb1 / np.linalg.norm(emb1)
        emb2_norm = emb2 / np.linalg.norm(emb2)
        
        # 计算余弦相似度
        similarity = np.dot(emb1_norm, emb2_norm)
        return float(similarity)
    
    async def _remove_entry(self, query_hash: str) -> None:
        """删除缓存条目"""
        if query_hash in self.cache:
            del self.cache[query_hash]
            logger.debug(f"删除缓存条目: {query_hash}")
    
    async def _evict_lru(self) -> None:
        """LRU淘汰策略"""
        if not self.cache:
            return
        
        # 按最后访问时间排序，删除最旧的条目
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # 删除最旧的10%
        evict_count = max(1, len(sorted_entries) // 10)
        for i in range(evict_count):
            query_hash, _ = sorted_entries[i]
            await self._remove_entry(query_hash)
        
        logger.info(f"LRU淘汰了 {evict_count} 个缓存条目")
    
    async def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_hashes = []
        
        for query_hash, entry in self.cache.items():
            if entry.is_expired():
                expired_hashes.append(query_hash)
        
        for query_hash in expired_hashes:
            await self._remove_entry(query_hash)
        
        if expired_hashes:
            await self.save_cache()
            logger.info(f"清理了 {len(expired_hashes)} 个过期缓存条目")
        
        return len(expired_hashes)
    
    def load_cache(self) -> None:
        """加载缓存"""
        if not os.path.exists(self.cache_file):
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for entry_data in data.get("entries", []):
                entry = CacheEntry.from_dict(entry_data)
                if not entry.is_expired():
                    self.cache[entry.query_hash] = entry
            
            logger.info(f"加载了 {len(self.cache)} 个缓存条目")
            
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
    
    async def save_cache(self) -> None:
        """保存缓存"""
        try:
            data = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "total_entries": len(self.cache),
                "entries": [entry.to_dict() for entry in self.cache.values()]
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"保存了 {len(self.cache)} 个缓存条目")
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def start_cleanup_task(self) -> None:
        """启动清理任务"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(3600)  # 每小时清理一次
                    await self.cleanup_expired()
                except Exception as e:
                    logger.error(f"清理任务异常: {e}")
        
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    def stop_cleanup_task(self) -> None:
        """停止清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        now = datetime.now()
        expired_count = sum(1 for entry in self.cache.values() if entry.is_expired())
        
        access_counts = [entry.access_count for entry in self.cache.values()]
        avg_access = sum(access_counts) / len(access_counts) if access_counts else 0
        
        return {
            "total_entries": len(self.cache),
            "expired_entries": expired_count,
            "active_entries": len(self.cache) - expired_count,
            "max_cache_size": self.max_cache_size,
            "cache_usage_percent": (len(self.cache) / self.max_cache_size) * 100,
            "average_access_count": avg_access,
            "similarity_threshold": self.similarity_threshold,
            "default_ttl_hours": self.default_ttl_hours,
            "vector_store_stats": self.query_store.get_stats()
        }
    
    async def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        
        # 清空向量索引
        try:
            self.query_store = FaissStore(
                dim=384,
                index_path=self.query_index_file,
                meta_path=self.query_meta_file
            )
        except Exception as e:
            logger.warning(f"重置向量索引失败: {e}")
        
        await self.save_cache()
        logger.info("缓存已清空")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.stop_cleanup_task()
        await self.save_cache()

# 全局缓存实例
_global_cache: Optional[RAGCache] = None

def get_rag_cache(cache_dir: str = "./cache", **kwargs) -> RAGCache:
    """获取全局RAG缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = RAGCache(cache_dir=cache_dir, **kwargs)
    return _global_cache

def set_rag_cache(cache: RAGCache) -> None:
    """设置全局RAG缓存实例"""
    global _global_cache
    _global_cache = cache