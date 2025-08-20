#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step4单独测试
测试Step4组装报告功能，使用更长的超时时间
"""

import requests
import json
import time
from datetime import datetime

def test_step4_with_existing_task():
    """使用现有任务测试Step4"""
    base_url = "http://localhost:8001"
    task_id = "391601ab-aaf9-4aa7-a81e-ad9c2885863a"  # 从之前的测试获取
    
    print(f"测试Step4组装报告功能")
    print(f"任务ID: {task_id}")
    print(f"开始时间: {datetime.now().isoformat()}")
    
    try:
        # 检查任务状态
        response = requests.get(f"{base_url}/task/{task_id}")
        if response.status_code == 200:
            task_info = response.json()
            print(f"任务状态: {task_info.get('status', 'unknown')}")
        else:
            print(f"无法获取任务信息: {response.status_code}")
            return False
            
        # 测试Step4，使用更长的超时时间
        print("\n开始Step4组装报告...")
        payload = {"task_id": task_id}
        
        # 使用180秒超时
        response = requests.post(f"{base_url}/step4", json=payload, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, str) and len(data) > 100:
                print(f"✅ Step4成功: 报告长度 {len(data)} 字符")
                print(f"报告预览: {data[:200]}...")
                return True
            else:
                print(f"❌ Step4失败: 报告内容异常")
                print(f"响应数据: {data}")
                return False
        else:
            print(f"❌ Step4失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {error_data}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Step4超时: 请求超过180秒")
        return False
    except Exception as e:
        print(f"❌ Step4异常: {str(e)}")
        return False
    finally:
        print(f"\n测试完成时间: {datetime.now().isoformat()}")

if __name__ == "__main__":
    success = test_step4_with_existing_task()
    exit(0 if success else 1)