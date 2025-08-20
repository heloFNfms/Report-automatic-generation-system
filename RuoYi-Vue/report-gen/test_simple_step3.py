#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试 Step3 改进效果
"""

import asyncio
import aiohttp
import json
import time

# 配置
ORCHESTRATOR_URL = "http://localhost:9000"

async def test_simple_step3():
    """简单测试 Step3"""
    print("=== 简单 Step3 测试 ===")
    
    async with aiohttp.ClientSession() as session:
        # 1. 创建任务
        step1_payload = {
            "project_name": "AI测试",
            "company_name": "测试公司",
            "research_content": "人工智能基础研究"
        }
        
        print("1. 创建任务...")
        async with session.post(f"{ORCHESTRATOR_URL}/step1", json=step1_payload) as response:
            if response.status != 200:
                print(f"❌ Step1 失败: {response.status}")
                return False
            
            result = await response.json()
            task_id = result.get('task_id')
            print(f"✅ 任务创建成功: {task_id}")
        
        # 2. 生成大纲
        print("2. 生成大纲...")
        step2_payload = {"task_id": task_id}
        async with session.post(f"{ORCHESTRATOR_URL}/step2", json=step2_payload) as response:
            if response.status != 200:
                print(f"❌ Step2 失败: {response.status}")
                return False
            print("✅ 大纲生成成功")
        
        # 3. 生成内容（观察日志）
        print("3. 生成内容 (观察服务端日志)...")
        step3_payload = {"task_id": task_id}
        
        start_time = time.time()
        try:
            async with session.post(f"{ORCHESTRATOR_URL}/step3", json=step3_payload, timeout=60) as response:
                elapsed = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Step3 成功，耗时: {elapsed:.2f}s")
                    
                    # 检查结果结构
                    research_results = result.get('research_results', {})
                    print(f"   章节数量: {len(research_results)}")
                    
                    # 显示前几个章节
                    for i, (key, content) in enumerate(list(research_results.items())[:3]):
                        print(f"   章节 {i+1}: {key}")
                        if isinstance(content, dict):
                            content_text = content.get('研究内容', '')
                            refs = content.get('参考网址', [])
                            print(f"     内容长度: {len(content_text)} 字符")
                            print(f"     参考链接: {len(refs)} 个")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Step3 失败: {response.status}")
                    print(f"   错误: {error_text[:200]}...")
                    return False
                    
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Step3 异常，耗时: {elapsed:.2f}s")
            print(f"   错误: {str(e)}")
            return False

async def main():
    print("开始简单 Step3 测试")
    print("请观察 report-orchestrator 服务端日志中的详细耗时信息")
    print("="*50)
    
    success = await test_simple_step3()
    
    print("\n" + "="*50)
    if success:
        print("🎉 测试成功！请检查服务端日志中的分阶段耗时统计")
    else:
        print("❌ 测试失败")

if __name__ == "__main__":
    asyncio.run(main())