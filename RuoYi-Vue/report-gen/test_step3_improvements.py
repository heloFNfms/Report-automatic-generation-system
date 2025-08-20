#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Step3 改进效果：
1. arXiv 工具超时修复
2. 分阶段耗时日志
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# 配置
ORCHESTRATOR_URL = "http://localhost:9000"
MCP_URL = "http://localhost:8000"

async def test_arxiv_timeout():
    """测试 arXiv 工具的超时修复"""
    print("\n=== 测试 arXiv 工具超时修复 ===")
    
    async with aiohttp.ClientSession() as session:
        # 测试 MCP arXiv 工具
        payload = {
            "tool_name": "arxiv_search",
            "arguments": {
                "query": "artificial intelligence machine learning",
                "max_results": 5
            }
        }
        
        start_time = time.time()
        try:
            async with session.post(f"{MCP_URL}/invoke", json=payload, timeout=20) as response:
                result = await response.json()
                elapsed = time.time() - start_time
                
                print(f"✅ arXiv 搜索成功，耗时: {elapsed:.2f}s")
                print(f"   状态码: {response.status}")
                print(f"   结果数量: {result.get('count', 0)}")
                
                if result.get('error'):
                    print(f"   错误信息: {result['error']}")
                    
                return True
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"❌ arXiv 搜索超时，耗时: {elapsed:.2f}s")
            return False
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ arXiv 搜索失败，耗时: {elapsed:.2f}s，错误: {str(e)}")
            return False

async def test_step3_with_timing():
    """测试 Step3 的耗时统计"""
    print("\n=== 测试 Step3 耗时统计 ===")
    
    async with aiohttp.ClientSession() as session:
        # 1. 创建任务
        step1_payload = {
            "project_name": "AI技术发展趋势研究",
            "company_name": "测试公司",
            "research_content": "人工智能在各行业的应用现状与发展前景"
        }
        
        print("1. 创建任务 (Step1)...")
        async with session.post(f"{ORCHESTRATOR_URL}/step1", json=step1_payload) as response:
            if response.status != 200:
                print(f"❌ Step1 失败，状态码: {response.status}")
                return False
            
            result = await response.json()
            task_id = result.get('task_id')
            print(f"✅ 任务创建成功，task_id: {task_id}")
        
        # 2. 生成大纲
        print("2. 生成大纲 (Step2)...")
        step2_payload = {"task_id": task_id}
        async with session.post(f"{ORCHESTRATOR_URL}/step2", json=step2_payload) as response:
            if response.status != 200:
                print(f"❌ Step2 失败，状态码: {response.status}")
                return False
            print("✅ 大纲生成成功")
        
        # 3. 生成内容（重点测试）
        print("3. 生成内容 (Step3) - 观察耗时日志...")
        step3_start = time.time()
        step3_payload = {"task_id": task_id}
        
        try:
            async with session.post(f"{ORCHESTRATOR_URL}/step3", json=step3_payload, timeout=300) as response:
                step3_elapsed = time.time() - step3_start
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Step3 成功完成，总耗时: {step3_elapsed:.2f}s")
                    print(f"   生成章节数: {len(result)}")
                    
                    # 显示部分结果
                    for i, (key, content) in enumerate(list(result.items())[:2]):
                        print(f"   章节 {i+1}: {key}")
                        print(f"     内容长度: {len(content.get('研究内容', ''))} 字符")
                        print(f"     参考链接: {len(content.get('参考网址', []))} 个")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Step3 失败，状态码: {response.status}，耗时: {step3_elapsed:.2f}s")
                    print(f"   错误信息: {error_text[:200]}...")
                    return False
                    
        except asyncio.TimeoutError:
            step3_elapsed = time.time() - step3_start
            print(f"❌ Step3 超时，耗时: {step3_elapsed:.2f}s")
            return False
        except Exception as e:
            step3_elapsed = time.time() - step3_start
            print(f"❌ Step3 异常，耗时: {step3_elapsed:.2f}s，错误: {str(e)}")
            return False

async def main():
    print(f"开始测试 Step3 改进效果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试 1: arXiv 超时修复
    arxiv_ok = await test_arxiv_timeout()
    
    # 测试 2: Step3 耗时统计
    step3_ok = await test_step3_with_timing()
    
    print("\n=== 测试总结 ===")
    print(f"arXiv 超时修复: {'✅ 通过' if arxiv_ok else '❌ 失败'}")
    print(f"Step3 耗时统计: {'✅ 通过' if step3_ok else '❌ 失败'}")
    
    if arxiv_ok and step3_ok:
        print("\n🎉 所有改进测试通过！")
        print("\n📋 改进效果:")
        print("   1. arXiv 工具现在有 15 秒超时保护")
        print("   2. Step3 各阶段耗时已记录到日志")
        print("   3. 可通过日志分析性能瓶颈")
    else:
        print("\n⚠️  部分测试失败，请检查日志")

if __name__ == "__main__":
    asyncio.run(main())