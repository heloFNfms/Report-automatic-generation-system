from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class RAGConfig:
    """RAG流水线配置类"""
    # 检索配置
    max_search_results: int = 12
    max_retrieved_docs: int = 15
    rerank_top_k: int = 8
    similarity_threshold: float = 0.8
    
    # 上下文配置
    max_context_tokens: int = 1500
    chunk_max_tokens: int = 400
    chunk_strategy: str = "mixed"  # "sentence", "paragraph", "token", "mixed"
    
    # 缓存配置
    cache_dir: str = "./cache"
    max_cache_size: int = 1000
    cache_ttl_hours: int = 24
    cache_similarity_threshold: float = 0.85
    enable_cache: bool = True
    
    # 嵌入模型配置
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # 功能开关
    enable_query_expansion: bool = True
    enable_semantic_compression: bool = True
    enable_multi_source: bool = True
    enable_vector_cache: bool = True
    
    # 性能配置
    parallel_search: bool = True
    max_concurrent_searches: int = 3
    search_timeout: float = 30.0
    
    # 质量控制
    min_relevance_score: float = 0.3
    max_duplicate_ratio: float = 0.7
    enable_content_filtering: bool = True
    
    @classmethod
    def for_academic_research(cls) -> 'RAGConfig':
        """学术研究场景的配置"""
        return cls(
            max_search_results=15,
            max_retrieved_docs=20,
            rerank_top_k=10,
            similarity_threshold=0.85,
            max_context_tokens=2000,
            chunk_max_tokens=500,
            enable_query_expansion=True,
            enable_semantic_compression=True,
            min_relevance_score=0.4
        )
    
    @classmethod
    def for_quick_summary(cls) -> 'RAGConfig':
        """快速摘要场景的配置"""
        return cls(
            max_search_results=8,
            max_retrieved_docs=10,
            rerank_top_k=5,
            similarity_threshold=0.75,
            max_context_tokens=1000,
            chunk_max_tokens=300,
            enable_query_expansion=False,
            enable_semantic_compression=False,
            parallel_search=True,
            search_timeout=15.0
        )
    
    @classmethod
    def for_comprehensive_analysis(cls) -> 'RAGConfig':
        """全面分析场景的配置"""
        return cls(
            max_search_results=20,
            max_retrieved_docs=25,
            rerank_top_k=12,
            similarity_threshold=0.8,
            max_context_tokens=2500,
            chunk_max_tokens=600,
            enable_query_expansion=True,
            enable_semantic_compression=True,
            enable_multi_source=True,
            max_concurrent_searches=5,
            min_relevance_score=0.35
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "max_search_results": self.max_search_results,
            "max_retrieved_docs": self.max_retrieved_docs,
            "rerank_top_k": self.rerank_top_k,
            "similarity_threshold": self.similarity_threshold,
            "max_context_tokens": self.max_context_tokens,
            "chunk_max_tokens": self.chunk_max_tokens,
            "chunk_strategy": self.chunk_strategy,
            "enable_query_expansion": self.enable_query_expansion,
            "enable_semantic_compression": self.enable_semantic_compression,
            "enable_multi_source": self.enable_multi_source,
            "enable_vector_cache": self.enable_vector_cache,
            "parallel_search": self.parallel_search,
            "max_concurrent_searches": self.max_concurrent_searches,
            "search_timeout": self.search_timeout,
            "min_relevance_score": self.min_relevance_score,
            "max_duplicate_ratio": self.max_duplicate_ratio,
            "enable_content_filtering": self.enable_content_filtering
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RAGConfig':
        """从字典创建配置"""
        return cls(**config_dict)
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        if self.max_search_results <= 0 or self.max_retrieved_docs <= 0:
            return False
        if self.rerank_top_k > self.max_retrieved_docs:
            return False
        if self.similarity_threshold < 0 or self.similarity_threshold > 1:
            return False
        if self.max_context_tokens <= 0 or self.chunk_max_tokens <= 0:
            return False
        if self.chunk_strategy not in ["sentence", "paragraph", "token", "mixed"]:
            return False
        return True
    
    def optimize_for_performance(self) -> 'RAGConfig':
        """性能优化配置"""
        optimized = RAGConfig(
            max_search_results=min(self.max_search_results, 10),
            max_retrieved_docs=min(self.max_retrieved_docs, 12),
            rerank_top_k=min(self.rerank_top_k, 6),
            similarity_threshold=max(self.similarity_threshold, 0.8),
            max_context_tokens=min(self.max_context_tokens, 1200),
            chunk_max_tokens=min(self.chunk_max_tokens, 350),
            chunk_strategy="mixed",
            enable_query_expansion=False,
            enable_semantic_compression=False,
            parallel_search=True,
            max_concurrent_searches=min(self.max_concurrent_searches, 3),
            search_timeout=min(self.search_timeout, 20.0),
            min_relevance_score=max(self.min_relevance_score, 0.4)
        )
        return optimized
    
    def optimize_for_quality(self) -> 'RAGConfig':
        """质量优化配置"""
        optimized = RAGConfig(
            max_search_results=max(self.max_search_results, 15),
            max_retrieved_docs=max(self.max_retrieved_docs, 18),
            rerank_top_k=max(self.rerank_top_k, 10),
            similarity_threshold=min(self.similarity_threshold, 0.75),
            max_context_tokens=max(self.max_context_tokens, 2000),
            chunk_max_tokens=max(self.chunk_max_tokens, 500),
            chunk_strategy="mixed",
            enable_query_expansion=True,
            enable_semantic_compression=True,
            enable_multi_source=True,
            parallel_search=True,
            max_concurrent_searches=max(self.max_concurrent_searches, 4),
            search_timeout=max(self.search_timeout, 45.0),
            min_relevance_score=min(self.min_relevance_score, 0.3)
        )
        return optimized

# 预定义配置实例
DEFAULT_CONFIG = RAGConfig()
ACADEMIC_CONFIG = RAGConfig.for_academic_research()
QUICK_CONFIG = RAGConfig.for_quick_summary()
COMPREHENSIVE_CONFIG = RAGConfig.for_comprehensive_analysis()

# 配置映射
CONFIG_PRESETS = {
    "default": DEFAULT_CONFIG,
    "academic": ACADEMIC_CONFIG,
    "quick": QUICK_CONFIG,
    "comprehensive": COMPREHENSIVE_CONFIG
}

def get_config(preset_name: str = "default") -> RAGConfig:
    """获取预设配置"""
    return CONFIG_PRESETS.get(preset_name, DEFAULT_CONFIG)

def create_custom_config(**kwargs) -> RAGConfig:
    """创建自定义配置"""
    base_config = DEFAULT_CONFIG
    config_dict = base_config.to_dict()
    config_dict.update(kwargs)
    return RAGConfig.from_dict(config_dict)