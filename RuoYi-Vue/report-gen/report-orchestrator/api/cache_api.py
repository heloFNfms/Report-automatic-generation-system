from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cache_manager import get_cache_manager
from core.rag_config import get_config
from core.rag_cache import CacheEntry

logger = logging.getLogger(__name__)

cache_router = APIRouter(tags=["cache"])

# 获取缓存管理器
cache_manager = get_cache_manager(get_config())

@cache_router.get("/stats", summary="获取缓存统计信息")
async def get_cache_stats():
    """获取RAG缓存的统计信息"""
    try:
        stats = await cache_manager.get_cache_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.get("/health", summary="获取缓存健康状态")
async def get_cache_health():
    """获取RAG缓存的健康状态"""
    try:
        health = await cache_manager.get_cache_health()
        return {
            "success": True,
            "data": health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取缓存健康状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.get("/entries", summary="搜索缓存条目")
async def search_cache_entries(
    query: Optional[str] = Query(None, description="搜索查询"),
    limit: int = Query(50, ge=1, le=1000, description="返回条目数量限制"),
    include_expired: bool = Query(False, description="是否包含过期条目")
):
    """搜索和列出缓存条目"""
    try:
        entries = await cache_manager.search_cache_entries(
            query=query,
            limit=limit,
            include_expired=include_expired
        )
        return {
            "success": True,
            "data": {
                "entries": entries,
                "total": len(entries),
                "query": query,
                "include_expired": include_expired
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"搜索缓存条目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.get("/entries/{query_hash}", summary="获取缓存条目详情")
async def get_cache_entry_detail(query_hash: str):
    """获取指定缓存条目的详细信息"""
    try:
        entry = await cache_manager.get_cache_entry_detail(query_hash)
        if entry is None:
            raise HTTPException(status_code=404, detail="缓存条目不存在")
        
        return {
            "success": True,
            "data": entry,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缓存条目详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.delete("/entries/{query_hash}", summary="删除缓存条目")
async def delete_cache_entry(query_hash: str):
    """删除指定的缓存条目"""
    try:
        success = await cache_manager.delete_cache_entry(query_hash)
        if not success:
            raise HTTPException(status_code=404, detail="缓存条目不存在")
        
        return {
            "success": True,
            "message": f"缓存条目 {query_hash} 已删除",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除缓存条目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.post("/cleanup", summary="清理过期缓存")
async def cleanup_expired_cache():
    """清理所有过期的缓存条目"""
    try:
        removed_count = await cache_manager.clear_expired_entries()
        return {
            "success": True,
            "data": {
                "removed_count": removed_count,
                "message": f"已清理 {removed_count} 个过期缓存条目"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"清理过期缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.post("/optimize", summary="优化缓存")
async def optimize_cache():
    """执行缓存优化操作"""
    try:
        result = await cache_manager.optimize_cache()
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"缓存优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.delete("/clear", summary="清空所有缓存")
async def clear_all_cache():
    """清空所有缓存数据"""
    try:
        await cache_manager.clear_all_cache()
        return {
            "success": True,
            "message": "所有缓存已清空",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.put("/config", summary="更新缓存配置")
async def update_cache_config(
    config_update: Dict[str, Any] = Body(..., description="缓存配置更新")
):
    """更新缓存配置参数"""
    try:
        # 验证配置参数
        valid_params = {
            "max_cache_size": int,
            "default_ttl_hours": int,
            "similarity_threshold": float
        }
        
        filtered_config = {}
        for key, value in config_update.items():
            if key in valid_params:
                try:
                    filtered_config[key] = valid_params[key](value)
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"参数 {key} 的值 {value} 类型不正确"
                    )
        
        if not filtered_config:
            raise HTTPException(status_code=400, detail="没有有效的配置参数")
        
        # 验证参数范围
        if "max_cache_size" in filtered_config and filtered_config["max_cache_size"] <= 0:
            raise HTTPException(status_code=400, detail="max_cache_size 必须大于 0")
        
        if "default_ttl_hours" in filtered_config and filtered_config["default_ttl_hours"] <= 0:
            raise HTTPException(status_code=400, detail="default_ttl_hours 必须大于 0")
        
        if "similarity_threshold" in filtered_config:
            threshold = filtered_config["similarity_threshold"]
            if not (0.0 <= threshold <= 1.0):
                raise HTTPException(status_code=400, detail="similarity_threshold 必须在 0.0 到 1.0 之间")
        
        # 更新配置
        updated = await cache_manager.update_cache_config(**filtered_config)
        
        return {
            "success": True,
            "data": {
                "updated_params": updated,
                "message": "缓存配置已更新"
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新缓存配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.get("/export", summary="导出缓存数据")
async def export_cache_data(
    include_embeddings: bool = Query(False, description="是否包含embedding数据")
):
    """导出缓存数据"""
    try:
        data = await cache_manager.export_cache_data(include_embeddings=include_embeddings)
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"导出缓存数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.post("/import", summary="导入缓存数据")
async def import_cache_data(
    import_data: Dict[str, Any] = Body(..., description="要导入的缓存数据"),
    overwrite: bool = Query(False, description="是否覆盖现有数据")
):
    """导入缓存数据"""
    try:
        # 验证导入数据格式
        if "entries" not in import_data:
            raise HTTPException(status_code=400, detail="导入数据缺少 entries 字段")
        
        if not isinstance(import_data["entries"], list):
            raise HTTPException(status_code=400, detail="entries 字段必须是数组")
        
        result = await cache_manager.import_cache_data(import_data, overwrite=overwrite)
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入缓存数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.get("/search/{query}", summary="缓存查询测试")
async def test_cache_query(
    query: str,
    similarity_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="相似度阈值")
):
    """测试缓存查询功能"""
    try:
        # 直接使用缓存的get方法进行测试
        result = await cache_manager.cache.get(query, similarity_threshold)
        
        return {
            "success": True,
            "data": {
                "query": query,
                "similarity_threshold": similarity_threshold,
                "cache_hit": result is not None,
                "result_count": len(result) if result else 0,
                "results": result[:3] if result else None  # 只返回前3个结果
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"缓存查询测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cache_router.get("/metrics", summary="获取缓存性能指标")
async def get_cache_metrics():
    """获取缓存性能指标"""
    try:
        stats = await cache_manager.get_cache_stats()
        health = await cache_manager.get_cache_health()
        
        # 计算额外的性能指标
        hit_rate = 0
        if stats["total_entries"] > 0:
            total_access = sum(entry.access_count for entry in cache_manager.cache.cache.values())
            hit_rate = (total_access / stats["total_entries"]) if stats["total_entries"] > 0 else 0
        
        metrics = {
            "cache_stats": stats,
            "health_status": health,
            "performance_metrics": {
                "estimated_hit_rate": hit_rate,
                "memory_efficiency": stats["cache_usage_percent"],
                "active_ratio": (stats["active_entries"] / max(stats["total_entries"], 1)) * 100
            }
        }
        
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取缓存性能指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))