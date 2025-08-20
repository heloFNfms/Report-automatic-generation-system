import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import asdict

from .rag_cache import RAGCache, get_rag_cache
from .rag_config import RAGConfig

logger = logging.getLogger(__name__)

class CacheManager:
    """RAG缓存管理器"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.cache = get_rag_cache(
            cache_dir=config.cache_dir,
            max_cache_size=config.max_cache_size,
            default_ttl_hours=config.cache_ttl_hours,
            similarity_threshold=config.cache_similarity_threshold,
            embedding_model=config.embedding_model
        )
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = self.cache.get_stats()
        
        # 添加配置信息
        stats.update({
            "config": {
                "cache_dir": self.config.cache_dir,
                "max_cache_size": self.config.max_cache_size,
                "default_ttl_hours": self.config.cache_ttl_hours,
                "similarity_threshold": self.config.cache_similarity_threshold,
                "enable_cache": self.config.enable_cache
            },
            "timestamp": datetime.now().isoformat()
        })
        
        return stats
    
    async def search_cache_entries(self, 
                                   query: Optional[str] = None,
                                   limit: int = 50,
                                   include_expired: bool = False) -> List[Dict[str, Any]]:
        """搜索缓存条目"""
        entries = []
        
        for entry in self.cache.cache.values():
            # 过滤过期条目
            if not include_expired and entry.is_expired():
                continue
            
            # 查询过滤
            if query and query.lower() not in entry.query_text.lower():
                continue
            
            entry_info = {
                "query_hash": entry.query_hash,
                "query_text": entry.query_text[:100] + "..." if len(entry.query_text) > 100 else entry.query_text,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "access_count": entry.access_count,
                "ttl_hours": entry.ttl_hours,
                "is_expired": entry.is_expired(),
                "results_count": len(entry.results),
                "similarity_threshold": entry.similarity_threshold
            }
            
            entries.append(entry_info)
            
            if len(entries) >= limit:
                break
        
        # 按访问时间排序
        entries.sort(key=lambda x: x["last_accessed"], reverse=True)
        
        return entries
    
    async def get_cache_entry_detail(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """获取缓存条目详情"""
        if query_hash not in self.cache.cache:
            return None
        
        entry = self.cache.cache[query_hash]
        
        return {
            "query_hash": entry.query_hash,
            "query_text": entry.query_text,
            "query_embedding": entry.query_embedding[:10],  # 只显示前10个维度
            "results": entry.results,
            "created_at": entry.created_at.isoformat(),
            "last_accessed": entry.last_accessed.isoformat(),
            "access_count": entry.access_count,
            "ttl_hours": entry.ttl_hours,
            "is_expired": entry.is_expired(),
            "similarity_threshold": entry.similarity_threshold,
            "embedding_dimension": len(entry.query_embedding)
        }
    
    async def delete_cache_entry(self, query_hash: str) -> bool:
        """删除指定缓存条目"""
        if query_hash in self.cache.cache:
            await self.cache._remove_entry(query_hash)
            await self.cache.save_cache()
            logger.info(f"删除缓存条目: {query_hash}")
            return True
        return False
    
    async def clear_expired_entries(self) -> int:
        """清理过期条目"""
        return await self.cache.cleanup_expired()
    
    async def clear_all_cache(self) -> None:
        """清空所有缓存"""
        await self.cache.clear_cache()
        logger.info("已清空所有缓存")
    
    async def update_cache_config(self, 
                                  max_cache_size: Optional[int] = None,
                                  default_ttl_hours: Optional[int] = None,
                                  similarity_threshold: Optional[float] = None) -> Dict[str, Any]:
        """更新缓存配置"""
        updated = {}
        
        if max_cache_size is not None:
            self.cache.max_cache_size = max_cache_size
            self.config.max_cache_size = max_cache_size
            updated["max_cache_size"] = max_cache_size
        
        if default_ttl_hours is not None:
            self.cache.default_ttl_hours = default_ttl_hours
            self.config.cache_ttl_hours = default_ttl_hours
            updated["default_ttl_hours"] = default_ttl_hours
        
        if similarity_threshold is not None:
            self.cache.similarity_threshold = similarity_threshold
            self.config.cache_similarity_threshold = similarity_threshold
            updated["similarity_threshold"] = similarity_threshold
        
        if updated:
            logger.info(f"缓存配置已更新: {updated}")
        
        return updated
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """优化缓存"""
        stats_before = self.cache.get_stats()
        
        # 清理过期条目
        expired_count = await self.clear_expired_entries()
        
        # 如果缓存使用率过高，执行LRU淘汰
        if len(self.cache.cache) > self.cache.max_cache_size * 0.9:
            await self.cache._evict_lru()
        
        # 清理旧版本文件
        try:
            self.cache.query_store.cleanup_old_versions(keep_versions=3)
        except Exception as e:
            logger.warning(f"清理旧版本文件失败: {e}")
        
        stats_after = self.cache.get_stats()
        
        optimization_result = {
            "expired_removed": expired_count,
            "entries_before": stats_before["total_entries"],
            "entries_after": stats_after["total_entries"],
            "space_freed": stats_before["total_entries"] - stats_after["total_entries"],
            "cache_usage_before": stats_before["cache_usage_percent"],
            "cache_usage_after": stats_after["cache_usage_percent"],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"缓存优化完成: {optimization_result}")
        return optimization_result
    
    async def export_cache_data(self, include_embeddings: bool = False) -> Dict[str, Any]:
        """导出缓存数据"""
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "config": asdict(self.config),
            "stats": await self.get_cache_stats(),
            "entries": []
        }
        
        for entry in self.cache.cache.values():
            entry_data = entry.to_dict()
            
            # 可选择是否包含embedding数据
            if not include_embeddings:
                entry_data.pop("query_embedding", None)
            
            export_data["entries"].append(entry_data)
        
        return export_data
    
    async def import_cache_data(self, data: Dict[str, Any], 
                                overwrite: bool = False) -> Dict[str, Any]:
        """导入缓存数据"""
        if not overwrite:
            # 备份当前缓存
            backup_data = await self.export_cache_data(include_embeddings=True)
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            for entry_data in data.get("entries", []):
                try:
                    from .rag_cache import CacheEntry
                    entry = CacheEntry.from_dict(entry_data)
                    
                    # 检查是否已存在
                    if not overwrite and entry.query_hash in self.cache.cache:
                        skipped_count += 1
                        continue
                    
                    # 添加到缓存
                    self.cache.cache[entry.query_hash] = entry
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"导入缓存条目失败: {e}")
                    error_count += 1
            
            # 保存缓存
            await self.cache.save_cache()
            
            result = {
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "error_count": error_count,
                "total_entries": len(data.get("entries", [])),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"缓存数据导入完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"导入缓存数据失败: {e}")
            
            # 如果有备份，尝试恢复
            if not overwrite and 'backup_data' in locals():
                try:
                    await self.import_cache_data(backup_data, overwrite=True)
                    logger.info("已恢复备份缓存")
                except Exception as restore_error:
                    logger.error(f"恢复备份缓存失败: {restore_error}")
            
            raise e
    
    async def get_cache_health(self) -> Dict[str, Any]:
        """获取缓存健康状态"""
        stats = await self.get_cache_stats()
        
        # 计算健康指标
        usage_percent = stats["cache_usage_percent"]
        expired_percent = (stats["expired_entries"] / max(stats["total_entries"], 1)) * 100
        avg_access = stats["average_access_count"]
        
        # 健康评分 (0-100)
        health_score = 100
        
        # 使用率过高扣分
        if usage_percent > 90:
            health_score -= 30
        elif usage_percent > 80:
            health_score -= 15
        
        # 过期条目过多扣分
        if expired_percent > 20:
            health_score -= 25
        elif expired_percent > 10:
            health_score -= 10
        
        # 平均访问次数过低扣分
        if avg_access < 1.5:
            health_score -= 15
        elif avg_access < 2:
            health_score -= 5
        
        # 确定健康状态
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "warning"
        else:
            status = "critical"
        
        recommendations = []
        
        if usage_percent > 85:
            recommendations.append("考虑增加缓存大小或清理旧条目")
        
        if expired_percent > 15:
            recommendations.append("建议清理过期缓存条目")
        
        if avg_access < 2:
            recommendations.append("缓存命中率较低，考虑调整相似度阈值")
        
        return {
            "status": status,
            "health_score": max(0, health_score),
            "usage_percent": usage_percent,
            "expired_percent": expired_percent,
            "average_access_count": avg_access,
            "recommendations": recommendations,
            "last_check": datetime.now().isoformat()
        }

# 全局缓存管理器实例
_global_cache_manager: Optional[CacheManager] = None

def get_cache_manager(config: RAGConfig) -> CacheManager:
    """获取全局缓存管理器实例"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager(config)
    return _global_cache_manager

def set_cache_manager(manager: CacheManager) -> None:
    """设置全局缓存管理器实例"""
    global _global_cache_manager
    _global_cache_manager = manager