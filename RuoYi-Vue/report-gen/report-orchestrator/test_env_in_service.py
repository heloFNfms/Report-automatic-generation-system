#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务中的环境变量加载
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=== 环境变量测试 ===")
print(f"当前工作目录: {os.getcwd()}")
print(f"Python路径: {sys.executable}")

# 检查关键环境变量
env_vars = [
    'DEEPSEEK_API_KEY',
    'DEEPSEEK_BASE',
    'DEEPSEEK_MODEL',
    'MCP_BASE'
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        if 'API_KEY' in var:
            # 隐藏API密钥的大部分内容
            masked_value = value[:8] + '*' * (len(value) - 12) + value[-4:] if len(value) > 12 else '*' * len(value)
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: 未设置")

# 测试 DeepSeek 配置加载
try:
    from core.deepseek_config import DeepSeekConfig
    config = DeepSeekConfig.from_env()
    print(f"\n✅ DeepSeek 配置加载成功")
    print(f"   - Base URL: {config.base_url}")
    print(f"   - Model: {config.model}")
    print(f"   - Max Retries: {config.max_retries}")
except Exception as e:
    print(f"\n❌ DeepSeek 配置加载失败: {e}")

print("\n=== 测试完成 ===")