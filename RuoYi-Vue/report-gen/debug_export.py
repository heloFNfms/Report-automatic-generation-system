#!/usr/bin/env python3
"""
调试导出功能
"""

import requests
import json

def test_export():
    base_url = "http://localhost:8001"
    
    # 1. 创建一个测试任务
    print("1. 创建测试任务...")
    step1_payload = {
        "project_name": "导出测试报告",
        "company_name": "测试公司",
        "research_content": "测试导出功能的基本流程"
    }
    
    response = requests.post(f"{base_url}/step1", json=step1_payload)
    if response.status_code != 200:
        print(f"Step1 失败: {response.status_code} - {response.text}")
        return
    
    task_id = response.json().get("task_id")
    print(f"任务创建成功，ID: {task_id}")
    
    # 2. 执行所有步骤
    steps = ["step2", "step3", "step4", "step5"]
    for step in steps:
        print(f"执行 {step}...")
        payload = {"task_id": task_id}
        response = requests.post(f"{base_url}/{step}", json=payload)
        if response.status_code != 200:
            print(f"{step} 失败: {response.status_code} - {response.text}")
            return
        print(f"{step} 完成")
    
    # 3. 测试导出
    print("\n3. 测试PDF导出...")
    export_payload = {
        "task_id": task_id,
        "format": "pdf",
        "upload_to_oss": False
    }
    
    response = requests.post(f"{base_url}/export", json=export_payload)
    print(f"PDF导出响应状态: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"PDF导出成功: {result}")
    else:
        print(f"PDF导出失败: {response.text}")
    
    print("\n4. 测试Word导出...")
    export_payload["format"] = "docx"
    
    response = requests.post(f"{base_url}/export", json=export_payload)
    print(f"Word导出响应状态: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Word导出成功: {result}")
    else:
        print(f"Word导出失败: {response.text}")

if __name__ == "__main__":
    test_export()