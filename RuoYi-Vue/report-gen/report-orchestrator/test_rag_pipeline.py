#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG流水线测试脚本
测试增强RAG流水线的各个组件和完整流程
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_rag_pipeline import EnhancedRAGPipeline
from core.rag_config import RAGConfig, get_config, ACADEMIC_CONFIG, QUICK_CONFIG
from core.mcp_client import MCPClient
from core.deepseek_client import DeepSeekClient
from core.vectorstore import Embedding, FaissStore
from core.vector_config import get_vector_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGPipelineTest:
    """RAG流水线测试类"""
    
    def __init__(self):
        self.mcp = None
        self.deepseek = None
        self.embedding = None
        self.vector_store = None
        self.pipeline = None
    
    async def setup(self):
        """初始化测试环境"""
        try:
            # 初始化组件
            self.mcp = MCPClient(base=os.getenv("MCP_BASE", "http://localhost:8000"))
            self.deepseek = DeepSeekClient.from_env()
            self.embedding = Embedding()
            self.vector_manager = get_vector_manager()
            
            # 初始化RAG流水线
            config = get_config("academic")
            self.pipeline = EnhancedRAGPipeline(
                mcp_client=self.mcp,
                deepseek_client=self.deepseek,
                embedding=self.embedding,
                vector_store=None,  # 使用新的向量管理器
                config=config
            )
            
            logger.info("RAG流水线测试环境初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def test_config_system(self):
        """测试配置系统"""
        logger.info("=== 测试配置系统 ===")
        
        try:
            # 测试预设配置
            default_config = get_config("default")
            academic_config = get_config("academic")
            quick_config = get_config("quick")
            
            logger.info(f"默认配置: max_search_results={default_config.max_search_results}")
            logger.info(f"学术配置: max_search_results={academic_config.max_search_results}")
            logger.info(f"快速配置: max_search_results={quick_config.max_search_results}")
            
            # 测试配置验证
            assert default_config.validate(), "默认配置验证失败"
            assert academic_config.validate(), "学术配置验证失败"
            assert quick_config.validate(), "快速配置验证失败"
            
            # 测试配置优化
            optimized_config = default_config.optimize_for_performance()
            logger.info(f"性能优化后: max_search_results={optimized_config.max_search_results}")
            
            logger.info("配置系统测试通过")
            return True
            
        except Exception as e:
            logger.error(f"配置系统测试失败: {e}")
            return False
    
    async def test_query_generation(self):
        """测试查询生成"""
        logger.info("=== 测试查询生成 ===")
        
        try:
            task_info = {
                "project_name": "人工智能在医疗诊断中的应用",
                "research_content": "深度学习算法在医学影像分析中的最新进展"
            }
            
            queries = await self.pipeline._generate_search_queries(
                task_info, "技术背景", "深度学习基础"
            )
            
            logger.info(f"生成的查询数量: {len(queries)}")
            for i, query in enumerate(queries):
                logger.info(f"查询 {i+1}: {query}")
            
            assert len(queries) > 0, "未生成任何查询"
            logger.info("查询生成测试通过")
            return True
            
        except Exception as e:
            logger.error(f"查询生成测试失败: {e}")
            return False
    
    async def test_mcp_retrieval(self):
        """测试MCP检索"""
        logger.info("=== 测试MCP检索 ===")
        
        try:
            queries = [
                "artificial intelligence medical diagnosis",
                "deep learning medical imaging"
            ]
            
            documents = await self.pipeline._multi_source_retrieval(queries)
            
            logger.info(f"检索到的文档数量: {len(documents)}")
            if documents:
                sample_doc = documents[0]
                logger.info(f"示例文档字段: {list(sample_doc.keys()) if isinstance(sample_doc, dict) else type(sample_doc)}")
            
            logger.info("MCP检索测试通过")
            return True
            
        except Exception as e:
            logger.error(f"MCP检索测试失败: {e}")
            return False
    
    async def test_vector_operations(self):
        """测试向量操作"""
        logger.info("=== 测试向量操作 ===")
        
        try:
            # 模拟文档
            mock_documents = [
                {
                    "title": "AI in Healthcare",
                    "url": "https://example.com/ai-healthcare",
                    "content": "Artificial intelligence is revolutionizing healthcare through advanced diagnostic tools.",
                    "_source": "test",
                    "_query": "AI healthcare"
                },
                {
                    "title": "Deep Learning Medical Imaging",
                    "url": "https://example.com/dl-imaging",
                    "content": "Deep learning algorithms show promising results in medical image analysis.",
                    "_source": "test",
                    "_query": "deep learning imaging"
                }
            ]
            
            queries = ["AI healthcare", "deep learning imaging"]
            retrieved_docs = await self.pipeline._vector_retrieval(queries, mock_documents)
            
            logger.info(f"向量检索结果数量: {len(retrieved_docs)}")
            if retrieved_docs:
                sample_text, sample_meta = retrieved_docs[0]
                logger.info(f"示例文本长度: {len(sample_text)}")
                logger.info(f"示例元数据: {sample_meta}")
            
            logger.info("向量操作测试通过")
            return True
            
        except Exception as e:
            logger.error(f"向量操作测试失败: {e}")
            return False
    
    async def test_full_pipeline(self):
        """测试完整流水线"""
        logger.info("=== 测试完整RAG流水线 ===")
        
        try:
            task_info = {
                "project_name": "人工智能在医疗诊断中的应用研究",
                "research_content": "基于深度学习的医学影像智能分析系统"
            }
            
            result = await self.pipeline.generate_section_content(
                task_info, "技术背景", "人工智能发展现状"
            )
            
            logger.info(f"生成结果字段: {list(result.keys())}")
            logger.info(f"内容长度: {len(result.get('content', ''))}")
            logger.info(f"参考网址数量: {len(result.get('参考网址', []))}")
            
            if result.get('metadata'):
                metadata = result['metadata']
                logger.info(f"处理步骤: {metadata.get('processing_steps', [])}")
                logger.info(f"上下文token数: {metadata.get('context_tokens', 0)}")
            
            # 验证结果
            assert 'content' in result, "结果中缺少content字段"
            assert 'h1' in result, "结果中缺少h1字段"
            assert 'h2' in result, "结果中缺少h2字段"
            assert '参考网址' in result, "结果中缺少参考网址字段"
            
            logger.info("完整流水线测试通过")
            return True
            
        except Exception as e:
            logger.error(f"完整流水线测试失败: {e}")
            return False
    
    async def test_performance_comparison(self):
        """测试性能对比"""
        logger.info("=== 测试性能对比 ===")
        
        try:
            task_info = {
                "project_name": "机器学习算法优化",
                "research_content": "神经网络训练效率提升方法"
            }
            
            # 测试快速配置
            quick_pipeline = EnhancedRAGPipeline(
                mcp_client=self.mcp,
                deepseek_client=self.deepseek,
                embedding=self.embedding,
                vector_store=None,  # 使用新的向量管理器
                config=QUICK_CONFIG
            )
            
            import time
            
            # 快速配置测试
            start_time = time.time()
            quick_result = await quick_pipeline.generate_section_content(
                task_info, "算法优化", "训练加速技术"
            )
            quick_time = time.time() - start_time
            
            # 学术配置测试
            start_time = time.time()
            academic_result = await self.pipeline.generate_section_content(
                task_info, "算法优化", "训练加速技术"
            )
            academic_time = time.time() - start_time
            
            logger.info(f"快速配置耗时: {quick_time:.2f}秒")
            logger.info(f"学术配置耗时: {academic_time:.2f}秒")
            logger.info(f"快速配置内容长度: {len(quick_result.get('content', ''))}")
            logger.info(f"学术配置内容长度: {len(academic_result.get('content', ''))}")
            
            logger.info("性能对比测试通过")
            return True
            
        except Exception as e:
            logger.error(f"性能对比测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始RAG流水线完整测试")
        
        # 初始化
        if not await self.setup():
            logger.error("测试环境初始化失败")
            return False
        
        # 运行测试
        tests = [
            self.test_config_system,
            self.test_query_generation,
            self.test_mcp_retrieval,
            self.test_vector_operations,
            self.test_full_pipeline,
            self.test_performance_comparison
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if await test():
                    passed += 1
                    logger.info(f"✓ {test.__name__} 通过")
                else:
                    logger.error(f"✗ {test.__name__} 失败")
            except Exception as e:
                logger.error(f"✗ {test.__name__} 异常: {e}")
        
        logger.info(f"\n测试完成: {passed}/{total} 通过")
        return passed == total

async def main():
    """主函数"""
    test_runner = RAGPipelineTest()
    success = await test_runner.run_all_tests()
    
    if success:
        logger.info("所有测试通过！RAG流水线工作正常")
        return 0
    else:
        logger.error("部分测试失败，请检查配置和依赖")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)