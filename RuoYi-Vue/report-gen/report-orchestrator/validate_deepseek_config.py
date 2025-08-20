#!/usr/bin/env python3
"""
DeepSeek配置验证脚本
用于检查DeepSeek API配置的完整性和有效性
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from core.deepseek_config import DeepSeekConfig, get_rate_limiter, get_alert_manager
from core.deepseek_client import DeepSeekClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment_variables():
    """检查环境变量配置"""
    logger.info("=== 检查环境变量配置 ===")
    
    required_vars = ['DEEPSEEK_API_KEY']
    optional_vars = [
        'DEEPSEEK_BASE', 'DEEPSEEK_MODEL', 'DEEPSEEK_MAX_RETRIES',
        'DEEPSEEK_RETRY_DELAY', 'DEEPSEEK_RETRY_BACKOFF', 'DEEPSEEK_TIMEOUT',
        'DEEPSEEK_RATE_LIMIT_PER_MINUTE', 'DEEPSEEK_RATE_LIMIT_PER_HOUR'
    ]
    
    issues = []
    
    # 检查必需变量
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            issues.append(f"❌ 缺少必需环境变量: {var}")
            logger.error(f"Missing required environment variable: {var}")
        else:
            # 隐藏API密钥的大部分内容
            if 'API_KEY' in var:
                masked_value = value[:8] + '*' * (len(value) - 12) + value[-4:] if len(value) > 12 else '*' * len(value)
                logger.info(f"✅ {var}: {masked_value}")
            else:
                logger.info(f"✅ {var}: {value}")
    
    # 检查可选变量
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.info(f"ℹ️  {var}: 使用默认值")
    
    return issues

def check_config_creation():
    """检查配置对象创建"""
    logger.info("\n=== 检查配置对象创建 ===")
    
    try:
        config = DeepSeekConfig.from_env()
        config.validate()
        
        logger.info(f"✅ 配置创建成功:")
        logger.info(f"   - Base URL: {config.base_url}")
        logger.info(f"   - Model: {config.model}")
        logger.info(f"   - Max Retries: {config.max_retries}")
        logger.info(f"   - Timeout: {config.timeout}s")
        logger.info(f"   - Rate Limit: {config.rate_limit_per_minute}/min, {config.rate_limit_per_hour}/hour")
        
        return config, []
        
    except Exception as e:
        error_msg = f"❌ 配置创建失败: {e}"
        logger.error(error_msg)
        return None, [error_msg]

def check_client_creation(config):
    """检查客户端创建"""
    logger.info("\n=== 检查客户端创建 ===")
    
    try:
        # 使用配置创建客户端
        client = DeepSeekClient(config=config)
        logger.info("✅ 客户端创建成功")
        
        # 检查统计信息
        stats = client.get_stats()
        logger.info(f"✅ 客户端统计信息获取成功")
        logger.info(f"   - 配置: {stats['config']}")
        logger.info(f"   - 速率限制: {stats['rate_limiter']}")
        
        return client, []
        
    except Exception as e:
        error_msg = f"❌ 客户端创建失败: {e}"
        logger.error(error_msg)
        return None, [error_msg]

async def check_api_connectivity(client):
    """检查API连接性（可选）"""
    logger.info("\n=== 检查API连接性 ===")
    
    if not client:
        logger.warning("⚠️  跳过API连接性检查（客户端创建失败）")
        return ["客户端创建失败，无法测试API连接"]
    
    # 检查API密钥是否为空
    if not client.config.api_key:
        logger.warning("⚠️  跳过API连接性检查（API密钥为空）")
        return ["API密钥为空，无法测试API连接"]
    
    try:
        # 发送一个简单的测试请求
        logger.info("发送测试请求...")
        response = await client.chat_async(
            prompt="请回复'测试成功'",
            system="你是一个测试助手，只需要简单回复即可。"
        )
        
        if "测试成功" in response or "success" in response.lower():
            logger.info("✅ API连接测试成功")
            return []
        else:
            logger.warning(f"⚠️  API响应异常: {response[:100]}...")
            return [f"API响应异常: {response[:100]}..."]
            
    except Exception as e:
        error_msg = f"❌ API连接测试失败: {e}"
        logger.error(error_msg)
        return [error_msg]

def check_rate_limiter():
    """检查速率限制器"""
    logger.info("\n=== 检查速率限制器 ===")
    
    try:
        config = DeepSeekConfig.from_env()
        rate_limiter = get_rate_limiter(config)
        
        logger.info(f"✅ 速率限制器创建成功")
        logger.info(f"   - 每分钟限制: {rate_limiter.per_minute}")
        logger.info(f"   - 每小时限制: {rate_limiter.per_hour}")
        logger.info(f"   - 当前分钟请求数: {len(rate_limiter.minute_requests)}")
        logger.info(f"   - 当前小时请求数: {len(rate_limiter.hour_requests)}")
        
        return []
        
    except Exception as e:
        error_msg = f"❌ 速率限制器检查失败: {e}"
        logger.error(error_msg)
        return [error_msg]

def check_alert_manager():
    """检查告警管理器"""
    logger.info("\n=== 检查告警管理器 ===")
    
    try:
        alert_manager = get_alert_manager()
        stats = alert_manager.get_stats()
        
        logger.info(f"✅ 告警管理器创建成功")
        logger.info(f"   - 总错误数: {stats['total_errors']}")
        logger.info(f"   - 连续错误数: {stats['consecutive_errors']}")
        logger.info(f"   - 最后错误时间: {stats['last_error_time']}")
        logger.info(f"   - 最后告警时间: {stats['last_alert_time']}")
        
        return []
        
    except Exception as e:
        error_msg = f"❌ 告警管理器检查失败: {e}"
        logger.error(error_msg)
        return [error_msg]

async def main():
    """主函数"""
    logger.info("开始DeepSeek配置验证...")
    
    all_issues = []
    
    # 1. 检查环境变量
    issues = check_environment_variables()
    all_issues.extend(issues)
    
    # 2. 检查配置创建
    config, issues = check_config_creation()
    all_issues.extend(issues)
    
    # 3. 检查客户端创建
    client, issues = check_client_creation(config)
    all_issues.extend(issues)
    
    # 4. 检查API连接性（可选）
    if os.getenv('TEST_API_CONNECTION', '').lower() in ('true', '1', 'yes'):
        issues = await check_api_connectivity(client)
        all_issues.extend(issues)
    else:
        logger.info("\n=== 跳过API连接性检查 ===")
        logger.info("提示: 设置环境变量 TEST_API_CONNECTION=true 来启用API连接测试")
    
    # 5. 检查速率限制器
    issues = check_rate_limiter()
    all_issues.extend(issues)
    
    # 6. 检查告警管理器
    issues = check_alert_manager()
    all_issues.extend(issues)
    
    # 总结
    logger.info("\n=== 验证总结 ===")
    if all_issues:
        logger.error(f"发现 {len(all_issues)} 个问题:")
        for i, issue in enumerate(all_issues, 1):
            logger.error(f"  {i}. {issue}")
        return 1
    else:
        logger.info("✅ 所有检查通过，DeepSeek配置正常！")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)