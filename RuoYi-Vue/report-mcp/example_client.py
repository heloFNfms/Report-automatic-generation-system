import requests
import os
BASE = os.getenv('MCP_BASE', 'http://localhost:8000')


# 列出工具
r = requests.get(BASE + '/tools')
print(r.json())


# 调用 arXiv
payload = {"tool": "arxiv_search", "args": {"query": "computer vision", "max_results": 3}}
r = requests.post(BASE + '/invoke', json=payload)
print(r.json())


# 调用 Bing (需配置 BING_API_KEY)
payload = {"tool": "bing_web_search", "args": {"query": "retrieval augmented generation", "count": 3}}
r = requests.post(BASE + '/invoke', json=payload)
print(r.json())