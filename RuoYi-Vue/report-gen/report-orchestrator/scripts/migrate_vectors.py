#!/usr/bin/env python3
"""
向量数据迁移脚本
支持FAISS和PGVector之间的数据迁移
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector_store import VectorStoreFactory, FAISSVectorStore, PGVectorStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorMigrator:
    """向量数据迁移器"""
    
    def __init__(self):
        self.batch_size = 100
    
    async def migrate_faiss_to_pgvector(self, 
                                      faiss_index_path: str,
                                      faiss_meta_path: str,
                                      pg_dsn: str,
                                      table_name: str = 'vectors',
                                      dimension: int = 768) -> bool:
        """从FAISS迁移到PGVector"""
        try:
            logger.info("Starting migration from FAISS to PGVector...")
            
            # 创建源和目标存储
            source = FAISSVectorStore(faiss_index_path, faiss_meta_path, dimension)
            target = PGVectorStore(pg_dsn, table_name, dimension)
            
            # 等待初始化完成
            await asyncio.sleep(1)
            
            # 获取源存储统计信息
            source_stats = await source.get_stats()
            total_vectors = source_stats['total_vectors']
            
            if total_vectors == 0:
                logger.info("No vectors to migrate")
                return True
            
            logger.info(f"Found {total_vectors} vectors to migrate")
            
            # 批量迁移
            migrated_count = 0
            
            # 获取所有向量ID
            all_ids = list(source.id_to_index.keys())
            
            for i in range(0, len(all_ids), self.batch_size):
                batch_ids = all_ids[i:i + self.batch_size]
                
                # 从源存储获取向量和元数据
                vectors = []
                metadata = []
                valid_ids = []
                
                for vec_id in batch_ids:
                    try:
                        index_pos = source.id_to_index[vec_id]
                        vector = source.index.reconstruct(index_pos)
                        meta = source.metadata.get(vec_id, {})
                        
                        vectors.append(vector)
                        metadata.append(meta)
                        valid_ids.append(vec_id)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get vector {vec_id}: {e}")
                        continue
                
                if vectors:
                    import numpy as np
                    vectors_array = np.array(vectors)
                    
                    # 添加到目标存储
                    await target.add_vectors(vectors_array, metadata, valid_ids)
                    migrated_count += len(vectors)
                    
                    logger.info(f"Migrated {migrated_count}/{total_vectors} vectors")
            
            # 验证迁移结果
            target_stats = await target.get_stats()
            logger.info(f"Migration completed. Target has {target_stats['total_vectors']} vectors")
            
            return migrated_count == total_vectors
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    async def migrate_pgvector_to_faiss(self,
                                      pg_dsn: str,
                                      table_name: str,
                                      faiss_index_path: str,
                                      faiss_meta_path: str,
                                      dimension: int = 768) -> bool:
        """从PGVector迁移到FAISS"""
        try:
            logger.info("Starting migration from PGVector to FAISS...")
            
            # 创建源和目标存储
            source = PGVectorStore(pg_dsn, table_name, dimension)
            target = FAISSVectorStore(faiss_index_path, faiss_meta_path, dimension)
            
            # 等待初始化完成
            await asyncio.sleep(1)
            
            # 获取源存储统计信息
            source_stats = await source.get_stats()
            total_vectors = source_stats['total_vectors']
            
            if total_vectors == 0:
                logger.info("No vectors to migrate")
                return True
            
            logger.info(f"Found {total_vectors} vectors to migrate")
            
            # 批量迁移
            migrated_count = 0
            offset = 0
            
            while offset < total_vectors:
                # 从源存储批量获取数据
                async with source.pool.acquire() as conn:
                    rows = await conn.fetch(f"""
                        SELECT id, vector, metadata
                        FROM {table_name}
                        ORDER BY id
                        LIMIT $1 OFFSET $2
                    """, self.batch_size, offset)
                
                if not rows:
                    break
                
                # 准备数据
                vectors = []
                metadata = []
                ids = []
                
                for row in rows:
                    import json
                    import numpy as np
                    
                    vec_id = row['id']
                    vector = np.array(row['vector'])
                    meta = json.loads(row['metadata']) if row['metadata'] else {}
                    
                    vectors.append(vector)
                    metadata.append(meta)
                    ids.append(vec_id)
                
                if vectors:
                    vectors_array = np.array(vectors)
                    
                    # 添加到目标存储
                    await target.add_vectors(vectors_array, metadata, ids)
                    migrated_count += len(vectors)
                    
                    logger.info(f"Migrated {migrated_count}/{total_vectors} vectors")
                
                offset += self.batch_size
            
            # 验证迁移结果
            target_stats = await target.get_stats()
            logger.info(f"Migration completed. Target has {target_stats['total_vectors']} vectors")
            
            return migrated_count == total_vectors
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    async def backup_vectors(self, backend: str, backup_path: str, **kwargs) -> bool:
        """备份向量数据"""
        try:
            logger.info(f"Creating backup of {backend} vectors...")
            
            # 创建向量存储
            store = VectorStoreFactory.create_vector_store(backend, **kwargs)
            
            # 等待初始化
            await asyncio.sleep(1)
            
            # 获取统计信息
            stats = await store.get_stats()
            total_vectors = stats['total_vectors']
            
            if total_vectors == 0:
                logger.info("No vectors to backup")
                return True
            
            logger.info(f"Backing up {total_vectors} vectors...")
            
            # 创建备份目录
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 导出数据
            if backend == 'faiss':
                await self._backup_faiss(store, backup_dir)
            elif backend == 'pgvector':
                await self._backup_pgvector(store, backup_dir)
            
            logger.info(f"Backup completed at {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    async def _backup_faiss(self, store: FAISSVectorStore, backup_dir: Path):
        """备份FAISS数据"""
        import shutil
        import json
        
        # 复制索引文件
        if store.index_path.exists():
            shutil.copy2(store.index_path, backup_dir / "faiss.index")
        
        # 复制元数据文件
        if store.meta_path.exists():
            shutil.copy2(store.meta_path, backup_dir / "faiss_meta.json")
        
        # 创建备份信息
        backup_info = {
            'backend': 'faiss',
            'timestamp': str(asyncio.get_event_loop().time()),
            'stats': await store.get_stats()
        }
        
        with open(backup_dir / "backup_info.json", 'w') as f:
            json.dump(backup_info, f, indent=2)
    
    async def _backup_pgvector(self, store: PGVectorStore, backup_dir: Path):
        """备份PGVector数据"""
        import json
        import numpy as np
        
        # 导出所有数据
        all_data = []
        offset = 0
        
        while True:
            async with store.pool.acquire() as conn:
                rows = await conn.fetch(f"""
                    SELECT id, vector, metadata, created_at
                    FROM {store.table_name}
                    ORDER BY id
                    LIMIT $1 OFFSET $2
                """, self.batch_size, offset)
            
            if not rows:
                break
            
            for row in rows:
                data = {
                    'id': row['id'],
                    'vector': row['vector'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'created_at': row['created_at'].isoformat()
                }
                all_data.append(data)
            
            offset += self.batch_size
        
        # 保存数据
        with open(backup_dir / "pgvector_data.json", 'w') as f:
            json.dump(all_data, f, indent=2)
        
        # 创建备份信息
        backup_info = {
            'backend': 'pgvector',
            'timestamp': str(asyncio.get_event_loop().time()),
            'stats': await store.get_stats()
        }
        
        with open(backup_dir / "backup_info.json", 'w') as f:
            json.dump(backup_info, f, indent=2)

async def main():
    parser = argparse.ArgumentParser(description='Vector data migration tool')
    parser.add_argument('command', choices=['migrate', 'backup'], help='Command to execute')
    parser.add_argument('--source', choices=['faiss', 'pgvector'], help='Source backend')
    parser.add_argument('--target', choices=['faiss', 'pgvector'], help='Target backend')
    parser.add_argument('--faiss-index', default='./data/faiss.index', help='FAISS index path')
    parser.add_argument('--faiss-meta', default='./data/faiss_meta.json', help='FAISS metadata path')
    parser.add_argument('--pg-dsn', help='PostgreSQL DSN')
    parser.add_argument('--pg-table', default='vectors', help='PostgreSQL table name')
    parser.add_argument('--dimension', type=int, default=768, help='Vector dimension')
    parser.add_argument('--backup-path', default='./backups', help='Backup directory path')
    
    args = parser.parse_args()
    
    migrator = VectorMigrator()
    
    if args.command == 'migrate':
        if not args.source or not args.target:
            print("Error: --source and --target are required for migration")
            return
        
        if args.source == args.target:
            print("Error: Source and target backends must be different")
            return
        
        if args.source == 'faiss' and args.target == 'pgvector':
            if not args.pg_dsn:
                print("Error: --pg-dsn is required for PGVector target")
                return
            
            success = await migrator.migrate_faiss_to_pgvector(
                args.faiss_index,
                args.faiss_meta,
                args.pg_dsn,
                args.pg_table,
                args.dimension
            )
            
        elif args.source == 'pgvector' and args.target == 'faiss':
            if not args.pg_dsn:
                print("Error: --pg-dsn is required for PGVector source")
                return
            
            success = await migrator.migrate_pgvector_to_faiss(
                args.pg_dsn,
                args.pg_table,
                args.faiss_index,
                args.faiss_meta,
                args.dimension
            )
        
        if success:
            print("Migration completed successfully")
        else:
            print("Migration failed")
            sys.exit(1)
    
    elif args.command == 'backup':
        if not args.source:
            print("Error: --source is required for backup")
            return
        
        kwargs = {}
        if args.source == 'faiss':
            kwargs = {
                'index_path': args.faiss_index,
                'meta_path': args.faiss_meta,
                'dimension': args.dimension
            }
        elif args.source == 'pgvector':
            if not args.pg_dsn:
                print("Error: --pg-dsn is required for PGVector backup")
                return
            kwargs = {
                'dsn': args.pg_dsn,
                'table_name': args.pg_table,
                'dimension': args.dimension
            }
        
        success = await migrator.backup_vectors(args.source, args.backup_path, **kwargs)
        
        if success:
            print("Backup completed successfully")
        else:
            print("Backup failed")
            sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())