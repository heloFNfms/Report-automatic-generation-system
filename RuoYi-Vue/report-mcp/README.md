###############################################################################
# README 摘要 (复制到 README.md 中)
###############################################################################
# README
# report-mcp (MCP Server)


# 主要文件
# - server.py : FastAPI 主进程，提供 /tools 和 /invoke
# - tools/* : 各类检索工具（arXiv, Bing）
# - utils/cache.py : 缓存 (Redis or memory)
# - example_client.py : 示例客户端调用
# - Dockerfile / requirements.txt


# 运行步骤
# 1) 复制 .env.example -> .env 并填写 BING_API_KEY (可选) 和 REDIS_URL (可选)
# 2) 本地运行: python -m uvicorn server:app --reload --port 8000
# 3) 或者构建 Docker: docker build -t report-mcp . && docker run -p 8000:8000 --env-file .env report-mcp


# API 说明
# GET /health
# GET /tools -> 返回工具列表与参数说明
# POST /invoke -> 调用工具
# body: { "tool": "arxiv_search", "args": {"query": "xxx", ...}}


# 扩展建议
# - 增加更多工具（Semantic Scholar, CrossRef, PubMed, Web scraping）
# - 在 tool 层实现 chunking、rerank, 返回原始文本 + metadata
# - 添加签名 / API key 验证
# - 添加异步队列 (celery / redis) 支持长任务


# 结束
# 祝你好运，接下来你可以把这个工程接入到 Orchestrator（LangChain）里，作为检索层的 MCP endpoint。