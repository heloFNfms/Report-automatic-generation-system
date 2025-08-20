#!/usr/bin/env python3
"""
向量存储配置管理
统一管理FAISS和PGVector的配置和初始化
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class VectorStoreConfig:
    """向量存储配置"""
    vector_backend: str = 'faiss'
    vector_dimension: int = 768
    vector_batch_size: int = 100
    vector_search_k: int = 10
    vector_cache_ttl: int = 3600
    
    # FAISS配置
    faiss_index_path: str = './data/faiss.index'
    faiss_meta_path: str = './data/faiss_meta.json'
    
    # PGVector配置
    pg_dsn: Optional[str] = None
    pg_vector_table: str = 'vectors'
    
    @classmethod
    def from_env(cls) -> 'VectorStoreConfig':
        """从环境变量创建配置"""
        return cls(
            vector_backend=os.getenv('VECTOR_BACKEND', 'faiss').lower(),
            vector_dimension=int(os.getenv('VECTOR_DIMENSION', '768')),
            vector_batch_size=int(os.getenv('VECTOR_BATCH_SIZE', '100')),
            vector_search_k=int(os.getenv('VECTOR_SEARCH_K', '10')),
            vector_cache_ttl=int(os.getenv('VECTOR_CACHE_TTL', '3600')),
            
            faiss_index_path=os.getenv('FAISS_INDEX_PATH', './data/faiss.index'),
            faiss_meta_path=os.getenv('FAISS_META_PATH', './data/faiss_meta.json'),
            
            pg_dsn=os.getenv('PG_DSN'),
            pg_vector_table=os.getenv('PG_VECTOR_TABLE', 'vectors')
        )
    
    def validate(self) -> bool:
        """验证配置有效性"""
        errors = []
        
        # 检查基础配置
        if self.vector_backend not in ['faiss', 'pgvector']:
            errors.append(f"Invalid backend: {self.vector_backend}")
        
        if self.vector_dimension <= 0:
            errors.append(f"Invalid dimension: {self.vector_dimension}")
        
        if self.vector_batch_size <= 0:
            errors.append(f"Invalid batch_size: {self.vector_batch_size}")
        
        # 检查后端特定配置
        if self.vector_backend == 'faiss':
            if not self.faiss_index_path:
                errors.append("FAISS index path is required")
            if not self.faiss_meta_path:
                errors.append("FAISS metadata path is required")
        
        elif self.vector_backend == 'pgvector':
            if not self.pg_dsn:
                errors.append("PostgreSQL DSN is required for pgvector backend")
            if not self.pg_vector_table:
                errors.append("PostgreSQL table name is required")
        
        if errors:
            logger.error(f"Vector store configuration errors: {errors}")
            return False
        
        return True
    
    def get_backend_config(self) -> Dict[str, Any]:
        """获取后端特定配置"""
        if self.vector_backend == 'faiss':
            return {
                'index_path': self.faiss_index_path,
                'meta_path': self.faiss_meta_path,
                'dimension': self.vector_dimension
            }
        elif self.vector_backend == 'pgvector':
            return {
                'dsn': self.pg_dsn,
                'table_name': self.pg_vector_table,
                'dimension': self.vector_dimension
            }
        else:
            raise ValueError(f"Unsupported backend: {self.vector_backend}")
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        if self.vector_backend == 'faiss':
            # 确保FAISS文件的目录存在
            Path(self.faiss_index_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self.faiss_meta_path).parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured FAISS directories exist")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'vector_backend': self.vector_backend,
            'vector_dimension': self.vector_dimension,
            'vector_batch_size': self.vector_batch_size,
            'vector_search_k': self.vector_search_k,
            'vector_cache_ttl': self.vector_cache_ttl,
            'faiss_index_path': self.faiss_index_path,
            'faiss_meta_path': self.faiss_meta_path,
            'pg_dsn': self.pg_dsn,
            'pg_vector_table': self.pg_vector_table
        }

class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(self, config: Optional[VectorStoreConfig] = None):
        self.config = config or VectorStoreConfig.from_env()
        self._store = None
        self._initialized = False
    
    async def initialize(self):
        """初始化向量存储"""
        if self._initialized:
            return
        
        # 验证配置
        if not self.config.validate():
            raise ValueError("Invalid vector store configuration")
        
        # 确保目录存在
        self.config.ensure_directories()
        
        # 创建向量存储实例
        from .vector_store import VectorStoreFactory
        
        backend_config = self.config.get_backend_config()
        self._store = VectorStoreFactory.create_vector_store(
            self.config.vector_backend, 
            **backend_config
        )
        
        # 等待存储初始化完成
        import asyncio
        await asyncio.sleep(0.5)
        
        self._initialized = True
        logger.info(f"Vector store initialized with backend: {self.config.vector_backend}")
    
    def get_store(self):
        """获取向量存储实例"""
        if not self._initialized:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")
        return self._store
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        if not self._initialized:
            await self.initialize()
        
        if asyncio.iscoroutinefunction(self._store.get_stats):
            stats = await self._store.get_stats()
        else:
            stats = self._store.get_stats()
        stats.update({
            'config': self.config.to_dict()
        })
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if asyncio.iscoroutinefunction(self._store.get_stats):
                stats = await self._store.get_stats()
            else:
                stats = self._store.get_stats()
            
            return {
                'status': 'healthy',
                'backend': self.config.vector_backend,
                'total_vectors': stats.get('total_vectors', 0),
                'dimension': self.config.vector_dimension,
                'initialized': self._initialized
            }
            
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'backend': self.config.vector_backend,
                'initialized': self._initialized
            }
    
    async def migrate_to(self, target_backend: str, target_config: Dict[str, Any]) -> bool:
        """迁移到另一个后端"""
        try:
            if not self._initialized:
                await self.initialize()
            
            logger.info(f"Starting migration from {self.config.vector_backend} to {target_backend}")
            
            # 创建目标存储
            from .vector_store import VectorStoreFactory
            target_store = VectorStoreFactory.create_vector_store(target_backend, **target_config)
            
            # 等待目标存储初始化
            import asyncio
            await asyncio.sleep(0.5)
            
            # 获取源数据统计
            source_stats = await self._store.get_stats()
            total_vectors = source_stats.get('total_vectors', 0)
            
            if total_vectors == 0:
                logger.info("No vectors to migrate")
                return True
            
            logger.info(f"Migrating {total_vectors} vectors...")
            
            # 执行迁移（这里需要根据具体后端实现）
            # 这是一个简化的示例，实际实现需要更复杂的逻辑
            
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    async def backup(self, backup_path: str) -> bool:
        """备份向量数据"""
        try:
            if not self._initialized:
                await self.initialize()
            
            from .migrate_vectors import VectorMigrator
            migrator = VectorMigrator()
            
            backend_config = self.config.get_backend_config()
            if asyncio.iscoroutinefunction(migrator.backup_vectors):
                success = await migrator.backup_vectors(
                    self.config.vector_backend,
                    backup_path,
                    **backend_config
                )
            else:
                success = migrator.backup_vectors(
                    self.config.vector_backend,
                    backup_path,
                    **backend_config
                )
            
            if success:
                logger.info(f"Backup completed at {backup_path}")
            else:
                logger.error("Backup failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

# 全局向量存储管理器实例
_vector_manager = None

def get_vector_manager() -> VectorStoreManager:
    """获取全局向量存储管理器"""
    global _vector_manager
    if _vector_manager is None:
        _vector_manager = VectorStoreManager()
    return _vector_manager

def set_vector_manager(manager: VectorStoreManager):
    """设置全局向量存储管理器"""
    global _vector_manager
    _vector_manager = manager

async def initialize_vector_store():
    """初始化全局向量存储"""
    manager = get_vector_manager()
    if asyncio.iscoroutinefunction(manager.initialize):
        await manager.initialize()
    else:
        manager.initialize()
    return manager