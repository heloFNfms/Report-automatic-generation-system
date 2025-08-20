#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_cache_api():
    """测试缓存API的可用性"""
    base_url = "http://localhost:8001"
    
    # 测试基础健康检查
    print("1. 测试基础健康检查...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应内容: {response.json()}")
    except Exception as e:
        print(f"   健康检查失败: {e}")
    
    # 测试API文档
    print("\n2. 测试API文档...")
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"   API文档状态码: {response.status_code}")
    except Exception as e:
        print(f"   API文档访问失败: {e}")
    
    # 测试OpenAPI规范
    print("\n3. 测试OpenAPI规范...")
    try:
        response = requests.get(f"{base_url}/openapi.json")
        print(f"   OpenAPI规范状态码: {response.status_code}")
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get('paths', {})
            cache_paths = [path for path in paths.keys() if '/api/cache' in path]
            print(f"   找到的缓存API路径: {cache_paths}")
    except Exception as e:
        print(f"   OpenAPI规范访问失败: {e}")
    
    # 测试缓存API
    print("\n4. 测试缓存API...")
    cache_endpoints = [
        "/api/cache/stats",
        "/api/cache/health",
        "/cache/stats",  # 测试不带/api前缀的路径
        "/cache/health"
    ]
    
    for endpoint in cache_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"   {endpoint}: 状态码 {response.status_code}")
            if response.status_code == 200:
                print(f"      响应: {response.json()}")
            elif response.status_code == 404:
                print(f"      404错误: {response.text}")
            else:
                print(f"      其他错误: {response.text}")
        except Exception as e:
            print(f"   {endpoint}: 请求失败 - {e}")

if __name__ == "__main__":
    test_cache_api()