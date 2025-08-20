#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试Step4问题
"""

import requests
import json
from datetime import datetime

def debug_step4():
    """调试Step4问题"""
    base_url = "http://localhost:8001"
    task_id = "7a5ff5c8-21d6-4292-bdbf-c805675d0558"  # 从上次测试获取
    
    print(f"调试Step4问题")
    print(f"任务ID: {task_id}")
    
    try:
        # 检查Step3的内容
        print("\n1. 检查Step3内容...")
        response = requests.get(f"{base_url}/task/{task_id}/history/content")
        if response.status_code == 200:
            content_data = response.json()
            print(f"Step3历史记录: {len(content_data.get('history', []))}条")
            if content_data.get('history'):
                latest_content = content_data['history'][-1]['output']
                print(f"最新内容包含: {len(latest_content)}个章节")
                for key in list(latest_content.keys())[:3]:  # 只显示前3个
                    print(f"  - {key}")
        else:
            print(f"无法获取Step3内容: {response.status_code}")
            
        # 测试Step4并获取详细响应
        print("\n2. 测试Step4...")
        payload = {"task_id": task_id}
        response = requests.post(f"{base_url}/step4", json=payload, timeout=120)
        
        print(f"Step4响应状态: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应数据类型: {type(data)}")
                if isinstance(data, str):
                    print(f"报告长度: {len(data)} 字符")
                    print(f"报告开头: {data[:200]}...")
                    if len(data) < 50:
                        print(f"完整报告内容: {data}")
                elif isinstance(data, dict):
                    print(f"字典键: {list(data.keys())}")
                    print(f"字典内容: {data}")
                else:
                    print(f"未知数据格式: {data}")
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                print(f"原始响应: {response.text}")
        else:
            print(f"Step4失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {error_data}")
            except:
                print(f"响应内容: {response.text}")
                
    except Exception as e:
        print(f"调试异常: {str(e)}")

if __name__ == "__main__":
    debug_step4()