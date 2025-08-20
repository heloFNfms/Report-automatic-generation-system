#!/usr/bin/env python3
"""
向量存储抽象层
支持FAISS（本地）和PGVector（PostgreSQL）后端的可插拔架构
"""

import os
import json
import asyncio
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]], ids: Optional[List[str]] = None) -> List[str]:
        """添加向量和元数据"""
        pass
    
    @abstractmethod
    async def search(self, query_vector: np.ndarray, k: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """搜索最相似的向量"""
        pass
    
    @abstractmethod
    async def backup(self, backup_path: str) -> bool:
        """备份向量数据"""
        pass
    
    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """删除向量"""
        pass
    
    @abstractmethod
    async def update_metadata(self, id: str, metadata: Dict[str, Any]) -> bool:
        """更新元数据"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """清空所有数据"""
        pass

class FAISSVectorStore(VectorStore):
    """FAISS向量存储实现"""
    
    def __init__(self, index_path: str, meta_path: str, dimension: int = 768):
        self.index_path = Path(index_path)
        self.meta_path = Path(meta_path)
        self.dimension = dimension
        self.index = None
        self.metadata = {}
        self.id_to_index = {}
        self.index_to_id = {}
        self.next_index = 0
        
        # 确保目录存在
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 延迟导入FAISS
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("FAISS not installed. Run: pip install faiss-cpu")
        
        # 初始化或加载索引
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """初始化或加载现有索引"""
        try:
            if self.index_path.exists() and self.meta_path.exists():
                await self._load_index()
                logger.info(f"Loaded FAISS index from {self.index_path}")
            else:
                await self._create_new_index()
                logger.info(f"Created new FAISS index at {self.index_path}")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            await self._create_new_index()
    
    async def _create_new_index(self):
        """创建新的索引"""
        # 使用L2距离的平面索引
        self.index = self.faiss.IndexFlatL2(self.dimension)
        self.metadata = {}
        self.id_to_index = {}
        self.index_to_id = {}
        self.next_index = 0
        await self._save_index()
    
    async def _load_index(self):
        """加载现有索引"""
        # 加载FAISS索引
        self.index = self.faiss.read_index(str(self.index_path))
        
        # 加载元数据
        with open(self.meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.metadata = data.get('metadata', {})
            self.id_to_index = data.get('id_to_index', {})
            self.index_to_id = {v: k for k, v in self.id_to_index.items()}
            self.next_index = data.get('next_index', 0)
    
    async def _save_index(self):
        """保存索引和元数据"""
        # 保存FAISS索引
        self.faiss.write_index(self.index, str(self.index_path))
        
        # 保存元数据
        data = {
            'metadata': self.metadata,
            'id_to_index': self.id_to_index,
            'next_index': self.next_index
        }
        
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]], ids: Optional[List[str]] = None) -> List[str]:
        """添加向量和元数据"""
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension {vectors.shape[1]} doesn't match index dimension {self.dimension}")
        
        if ids is None:
            ids = [f"vec_{self.next_index + i}" for i in range(len(vectors))]
        
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length mismatch between vectors, metadata, and ids")
        
        # 添加向量到索引
        start_index = self.index.ntotal
        self.index.add(vectors.astype(np.float32))
        
        # 更新映射和元数据
        for i, (vec_id, meta) in enumerate(zip(ids, metadata)):
            index_pos = start_index + i
            self.id_to_index[vec_id] = index_pos
            self.index_to_id[index_pos] = vec_id
            self.metadata[vec_id] = meta
        
        self.next_index = max(self.next_index, self.index.ntotal)
        
        # 保存更改
        await self._save_index()
        
        logger.info(f"Added {len(vectors)} vectors to FAISS index")
        return ids
    
    async def search(self, query_vector: np.ndarray, k: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """搜索最相似的向量"""
        if query_vector.shape[0] != self.dimension:
            raise ValueError(f"Query vector dimension {query_vector.shape[0]} doesn't match index dimension {self.dimension}")
        
        if self.index.ntotal == 0:
            return []
        
        # 执行搜索
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        distances, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS返回-1表示无效结果
                continue
                
            vec_id = self.index_to_id.get(idx)
            if vec_id is None:
                continue
                
            meta = self.metadata.get(vec_id, {})
            
            # 应用过滤器
            if filter_dict:
                if not self._matches_filter(meta, filter_dict):
                    continue
            
            results.append((vec_id, float(dist), meta))
        
        return results[:k]
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """检查元数据是否匹配过滤条件"""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True
    
    async def delete(self, ids: List[str]) -> bool:
        """删除向量（FAISS不支持直接删除，需要重建索引）"""
        try:
            # 收集要保留的向量
            vectors_to_keep = []
            metadata_to_keep = []
            ids_to_keep = []
            
            for vec_id, index_pos in self.id_to_index.items():
                if vec_id not in ids:
                    # 从索引中获取向量
                    vector = self.index.reconstruct(index_pos)
                    vectors_to_keep.append(vector)
                    metadata_to_keep.append(self.metadata[vec_id])
                    ids_to_keep.append(vec_id)
            
            # 重建索引
            await self._create_new_index()
            
            if vectors_to_keep:
                vectors_array = np.array(vectors_to_keep)
                await self.add_vectors(vectors_array, metadata_to_keep, ids_to_keep)
            
            logger.info(f"Deleted {len(ids)} vectors from FAISS index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False
    
    async def update_metadata(self, id: str, metadata: Dict[str, Any]) -> bool:
        """更新元数据"""
        if id in self.metadata:
            self.metadata[id].update(metadata)
            await self._save_index()
            return True
        return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            'backend': 'faiss',
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'index_path': str(self.index_path),
            'meta_path': str(self.meta_path),
            'index_size_mb': self.index_path.stat().st_size / 1024 / 1024 if self.index_path.exists() else 0
        }
    
    async def clear(self) -> bool:
        """清空所有数据"""
        try:
            await self._create_new_index()
            logger.info("Cleared FAISS index")
            return True
        except Exception as e:
            logger.error(f"Failed to clear FAISS index: {e}")
            return False
    
    async def backup(self, backup_path: str) -> bool:
        """备份向量数据"""
        try:
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            if self.index is not None:
                index_backup_path = backup_dir / "faiss_index.bin"
                self.faiss.write_index(self.index, str(index_backup_path))
            
            metadata_backup_path = backup_dir / "faiss_metadata.json"
            with open(metadata_backup_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": self.metadata,
                    "id_to_index": self.id_to_index,
                    "next_index": self.next_index
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"FAISS向量数据备份完成: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"备份FAISS向量数据失败: {e}")
            return False

class PGVectorStore(VectorStore):
    """PostgreSQL + pgvector 向量存储实现"""
    
    def __init__(self, dsn: str, table_name: str = 'vectors', dimension: int = 768):
        self.dsn = dsn
        self.table_name = table_name
        self.dimension = dimension
        self.pool = None
        
        # 延迟导入
        try:
            import asyncpg
            self.asyncpg = asyncpg
        except ImportError:
            raise ImportError("asyncpg not installed. Run: pip install asyncpg")
        
        # 初始化连接池
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """初始化数据库连接和表结构"""
        try:
            self.pool = await self.asyncpg.create_pool(self.dsn)
            await self._create_table()
            logger.info(f"Initialized PGVector store with table {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize PGVector store: {e}")
            raise
    
    async def _create_table(self):
        """创建向量表"""
        async with self.pool.acquire() as conn:
            # 启用pgvector扩展
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # 创建表
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    vector vector({self.dimension}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # 创建向量索引
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_vector_idx 
                ON {self.table_name} USING ivfflat (vector vector_l2_ops)
            """)
    
    async def add_vectors(self, vectors: np.ndarray, metadata: List[Dict[str, Any]], ids: Optional[List[str]] = None) -> List[str]:
        """添加向量和元数据"""
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension {vectors.shape[1]} doesn't match expected dimension {self.dimension}")
        
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
        
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length mismatch between vectors, metadata, and ids")
        
        async with self.pool.acquire() as conn:
            # 批量插入
            records = [
                (vec_id, vectors[i].tolist(), json.dumps(meta))
                for i, (vec_id, meta) in enumerate(zip(ids, metadata))
            ]
            
            await conn.executemany(f"""
                INSERT INTO {self.table_name} (id, vector, metadata)
                VALUES ($1, $2, $3)
                ON CONFLICT (id) DO UPDATE SET
                    vector = EXCLUDED.vector,
                    metadata = EXCLUDED.metadata
            """, records)
        
        logger.info(f"Added {len(vectors)} vectors to PGVector store")
        return ids
    
    async def search(self, query_vector: np.ndarray, k: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """搜索最相似的向量"""
        if query_vector.shape[0] != self.dimension:
            raise ValueError(f"Query vector dimension {query_vector.shape[0]} doesn't match expected dimension {self.dimension}")
        
        async with self.pool.acquire() as conn:
            # 构建查询
            where_clause = ""
            params = [query_vector.tolist(), k]
            
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(f"metadata->>{len(params)} = ${len(params) + 1}")
                    params.extend([key, str(value)])
                
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                SELECT id, vector <-> $1 as distance, metadata
                FROM {self.table_name}
                {where_clause}
                ORDER BY vector <-> $1
                LIMIT $2
            """
            
            rows = await conn.fetch(query, *params)
            
            results = []
            for row in rows:
                vec_id = row['id']
                distance = float(row['distance'])
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                results.append((vec_id, distance, metadata))
            
            return results
    
    async def delete(self, ids: List[str]) -> bool:
        """删除向量"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(f"""
                    DELETE FROM {self.table_name}
                    WHERE id = ANY($1)
                """, ids)
            
            logger.info(f"Deleted {len(ids)} vectors from PGVector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False
    
    async def update_metadata(self, id: str, metadata: Dict[str, Any]) -> bool:
        """更新元数据"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(f"""
                    UPDATE {self.table_name}
                    SET metadata = metadata || $2
                    WHERE id = $1
                """, id, json.dumps(metadata))
                
                return result != "UPDATE 0"
                
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(f"""
                SELECT 
                    COUNT(*) as total_vectors,
                    pg_size_pretty(pg_total_relation_size('{self.table_name}')) as table_size
                FROM {self.table_name}
            """)
            
            return {
                'backend': 'pgvector',
                'total_vectors': row['total_vectors'],
                'dimension': self.dimension,
                'table_name': self.table_name,
                'table_size': row['table_size']
            }
    
    async def clear(self) -> bool:
        """清空所有数据"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(f"TRUNCATE TABLE {self.table_name}")
            
            logger.info(f"Cleared PGVector table {self.table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear PGVector table: {e}")
            return False
    
    async def backup(self, backup_path: str) -> bool:
        """备份向量数据"""
        try:
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(f"SELECT * FROM {self.table_name}")
                
                backup_file = backup_dir / f"{self.table_name}_backup.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    backup_data = []
                    for row in rows:
                        backup_data.append({
                            "id": row['id'],
                            "vector": row['vector'],
                            "metadata": json.loads(row['metadata']) if row['metadata'] else {},
                            "created_at": row['created_at'].isoformat() if row['created_at'] else None
                        })
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"PGVector数据备份完成: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"备份PGVector数据失败: {e}")
            return False

class VectorStoreFactory:
    """向量存储工厂类"""
    
    @staticmethod
    def create_vector_store(backend: str = None, **kwargs) -> VectorStore:
        """创建向量存储实例"""
        if backend is None:
            backend = os.getenv('VECTOR_BACKEND', 'faiss')
        
        backend = backend.lower()
        
        if backend == 'faiss':
            index_path = kwargs.get('index_path') or os.getenv('FAISS_INDEX_PATH', './data/faiss.index')
            meta_path = kwargs.get('meta_path') or os.getenv('FAISS_META_PATH', './data/faiss_meta.json')
            dimension = kwargs.get('dimension', 768)
            
            return FAISSVectorStore(index_path, meta_path, dimension)
            
        elif backend == 'pgvector':
            dsn = kwargs.get('dsn') or os.getenv('PG_DSN')
            if not dsn:
                raise ValueError("PG_DSN environment variable is required for pgvector backend")
            
            table_name = kwargs.get('table_name', 'vectors')
            dimension = kwargs.get('dimension', 768)
            
            return PGVectorStore(dsn, table_name, dimension)
            
        else:
            raise ValueError(f"Unsupported vector backend: {backend}")

# 全局向量存储实例
_vector_store = None

def get_vector_store() -> VectorStore:
    """获取全局向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreFactory.create_vector_store()
    return _vector_store

def set_vector_store(store: VectorStore):
    """设置全局向量存储实例"""
    global _vector_store
    _vector_store = store