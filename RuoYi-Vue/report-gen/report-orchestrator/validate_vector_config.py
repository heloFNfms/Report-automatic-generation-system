#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量存储配置验证脚本
用于验证向量存储配置的正确性和连通性
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"已加载环境变量文件: {env_path}")
    else:
        print(f"环境变量文件不存在: {env_path}")
except ImportError:
    print("警告: python-dotenv 未安装，无法自动加载 .env 文件")

from core.vector_config import VectorStoreConfig, get_vector_manager, initialize_vector_store
from core.vector_store import VectorStoreFactory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_environment():
    """验证环境变量配置"""
    logger.info("=== 环境变量配置验证 ===")
    
    required_vars = [
        'VECTOR_BACKEND',
        'VECTOR_DIMENSION'
    ]
    
    optional_vars = [
        'FAISS_INDEX_PATH',
        'FAISS_META_PATH',
        'PG_DSN',
        'PG_VECTOR_TABLE',
        'VECTOR_BATCH_SIZE',
        'VECTOR_SEARCH_K',
        'VECTOR_CACHE_TTL'
    ]
    
    # 检查必需变量
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✓ {var}: {value}")
        else:
            logger.error(f"✗ {var}: 未设置")
            missing_vars.append(var)
    
    # 检查可选变量
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✓ {var}: {value}")
        else:
            logger.info(f"- {var}: 未设置（可选）")
    
    if missing_vars:
        logger.error(f"缺少必需的环境变量: {missing_vars}")
        return False
    
    return True

def validate_config():
    """验证配置对象"""
    logger.info("\n=== 配置对象验证 ===")
    
    try:
        config = VectorStoreConfig.from_env()
        logger.info(f"✓ 配置加载成功")
        logger.info(f"  - 后端: {config.vector_backend}")
        logger.info(f"  - 维度: {config.vector_dimension}")
        logger.info(f"  - 批次大小: {config.vector_batch_size}")
        logger.info(f"  - 搜索K值: {config.vector_search_k}")
        logger.info(f"  - 缓存TTL: {config.vector_cache_ttl}")
        
        # 验证配置
        config.validate()
        logger.info("✓ 配置验证通过")
        
        # 获取后端特定配置
        backend_config = config.get_backend_config()
        logger.info(f"✓ 后端配置: {backend_config}")
        
        return config
    except Exception as e:
        logger.error(f"✗ 配置验证失败: {e}")
        return None

def validate_factory(config):
    """验证工厂类"""
    logger.info("\n=== 工厂类验证 ===")
    
    try:
        store = VectorStoreFactory.create_vector_store(config.vector_backend, **config.get_backend_config())
        logger.info(f"✓ 向量存储创建成功: {type(store).__name__}")
        return store
    except Exception as e:
        logger.error(f"✗ 向量存储创建失败: {e}")
        return None

async def validate_manager():
    """验证管理器"""
    logger.info("\n=== 管理器验证 ===")
    
    try:
        # 获取管理器
        manager = get_vector_manager()
        logger.info("✓ 管理器获取成功")
        
        # 初始化管理器
        await initialize_vector_store()
        logger.info("✓ 管理器初始化成功")
        
        # 健康检查
        health = await manager.health_check()
        logger.info(f"✓ 健康检查: {health}")
        
        # 获取统计信息
        stats = await manager.get_stats()
        logger.info(f"✓ 统计信息: {stats}")
        
        return manager
    except Exception as e:
        logger.error(f"✗ 管理器验证失败: {e}")
        return None

async def validate_basic_operations(manager):
    """验证基本操作"""
    logger.info("\n=== 基本操作验证 ===")
    
    try:
        store = manager.get_store()
        
        # 测试向量 - 使用配置的维度
        import numpy as np
        dimension = manager.config.vector_dimension
        test_vectors = np.random.rand(2, dimension).astype(np.float32)
        test_metadata = [
            {"text": "测试文档1", "source": "test"},
            {"text": "测试文档2", "source": "test"}
        ]
        test_ids = ["test_1", "test_2"]
        
        # 添加向量
        if hasattr(store, 'add_vectors'):
            if asyncio.iscoroutinefunction(store.add_vectors):
                success = await store.add_vectors(test_vectors, test_metadata, test_ids)
            else:
                success = store.add_vectors(test_vectors, test_metadata, test_ids)
            
            if success:
                logger.info("✓ 向量添加成功")
            else:
                logger.warning("- 向量添加失败")
        
        # 搜索向量
        if hasattr(store, 'search'):
            query_vector = np.random.rand(dimension).astype(np.float32)
            
            if asyncio.iscoroutinefunction(store.search):
                results = await store.search(query_vector, k=2)
            else:
                results = store.search(query_vector, k=2)
            
            logger.info(f"✓ 搜索结果: {len(results)} 个")
            for i, result in enumerate(results):
                if isinstance(result, tuple) and len(result) >= 3:
                    vec_id, score, metadata = result
                    logger.info(f"  结果 {i+1}: id={vec_id}, score={score}, metadata={metadata}")
                else:
                    logger.info(f"  结果 {i+1}: {result}")
        
        # 清理测试数据
        if hasattr(store, 'delete'):
            if asyncio.iscoroutinefunction(store.delete):
                await store.delete(test_ids)
            else:
                store.delete(test_ids)
            logger.info("✓ 测试数据清理完成")
        
        return True
    except Exception as e:
        logger.error(f"✗ 基本操作验证失败: {e}")
        return False

async def main():
    """主函数"""
    logger.info("开始向量存储配置验证...")
    
    # 1. 验证环境变量
    if not validate_environment():
        logger.error("环境变量验证失败，退出")
        return False
    
    # 2. 验证配置对象
    config = validate_config()
    if not config:
        logger.error("配置对象验证失败，退出")
        return False
    
    # 3. 验证工厂类
    store = validate_factory(config)
    if not store:
        logger.error("工厂类验证失败，退出")
        return False
    
    # 4. 验证管理器
    manager = await validate_manager()
    if not manager:
        logger.error("管理器验证失败，退出")
        return False
    
    # 5. 验证基本操作
    if not await validate_basic_operations(manager):
        logger.error("基本操作验证失败")
        return False
    
    logger.info("\n=== 验证完成 ===")
    logger.info("✓ 所有验证项目通过")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            logger.info("向量存储配置验证成功")
            sys.exit(0)
        else:
            logger.error("向量存储配置验证失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("验证被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"验证过程中发生错误: {e}")
        sys.exit(1)