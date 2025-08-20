#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速工作流测试
创建新任务并测试完整流程
"""

import requests
import json
import time
from datetime import datetime

def test_quick_workflow():
    """快速测试完整工作流"""
    base_url = "http://localhost:8001"
    
    print("=== 快速工作流测试 ===")
    print(f"开始时间: {datetime.now().isoformat()}")
    
    try:
        # Step1: 创建任务
        print("\n1. 创建任务...")
        payload = {
            "project_name": "简单测试报告",
            "company_name": "测试公司",
            "research_content": "人工智能基础概念研究"
        }
        
        response = requests.post(f"{base_url}/step1", json=payload)
        if response.status_code != 200:
            print(f"❌ Step1失败: {response.status_code}")
            return False
            
        data = response.json()
        task_id = data.get("task_id")
        if not task_id:
            print("❌ Step1失败: 无task_id")
            return False
            
        print(f"✅ Step1成功: {task_id}")
        
        # Step2: 生成大纲
        print("\n2. 生成大纲...")
        payload = {"task_id": task_id}
        response = requests.post(f"{base_url}/step2", json=payload)
        
        if response.status_code != 200:
            print(f"❌ Step2失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {error_data}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
        data = response.json()
        outline = data.get("研究大纲")
        if not outline:
            print("❌ Step2失败: 无大纲")
            return False
            
        print(f"✅ Step2成功: {len(outline)}个章节")
        
        # Step3: 生成内容（简化版，只生成第一个章节）
        print("\n3. 生成内容...")
        payload = {"task_id": task_id}
        response = requests.post(f"{base_url}/step3", json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Step3失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {error_data}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
        data = response.json()
        if not isinstance(data, dict) or len(data) == 0:
            print("❌ Step3失败: 内容为空")
            return False
            
        print(f"✅ Step3成功: {len(data)}个章节")
        
        # Step4: 组装报告
        print("\n4. 组装报告...")
        payload = {"task_id": task_id}
        response = requests.post(f"{base_url}/step4", json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"❌ Step4失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {error_data}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
        data = response.json()
        if not isinstance(data, str) or len(data) < 50:
            print("❌ Step4失败: 报告内容异常")
            return False
            
        print(f"✅ Step4成功: 报告长度 {len(data)} 字符")
        
        # Step5: 完成报告
        print("\n5. 完成报告...")
        payload = {"task_id": task_id}
        response = requests.post(f"{base_url}/step5", json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Step5失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {error_data}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
        data = response.json()
        if not isinstance(data, dict) or "摘要" not in data:
            print("❌ Step5失败: 最终报告格式异常")
            return False
            
        print(f"✅ Step5成功: 最终报告生成完成")
        
        print("\n=== 测试成功 ===")
        print(f"任务ID: {task_id}")
        print(f"完成时间: {datetime.now().isoformat()}")
        return True
        
    except requests.exceptions.Timeout as e:
        print(f"❌ 超时错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 异常错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_quick_workflow()
    exit(0 if success else 1)