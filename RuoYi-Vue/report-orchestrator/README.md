###############################################################################
# README 摘要
###############################################################################
# report-orchestrator


# 说明
# - 本 Orchestrator 提供 Step1-5 的 HTTP 接口 (FastAPI)。
# - 内部使用 MCPClient 调用 MCP Server (/invoke)，并使用 DeepSeekClient 调用 DeepSeek API。
# - 包含 BM25 rerank、简单 chunk/compress 流程。


# 运行
# 1) 设置 .env, 启动 report-mcp
# 2) 启动本 orchestrator: uvicorn orchestrator.app:app --port 9000 --reload


# 扩展建议
# - 将 TASK_STORE 从内存改为 MySQL/Redis
# - 增加 embedding-based rerank（使用 sentence-transformers 或 OpenAI embeddings）
# - 使用分布式任务队列处理 step4 的长任务
# - 为 DeepSeek 返回结构做更强的 JSON 解析和校验


# 结束
# 现在把这套 Orchestrator 跑起来，然后我会继续帮你把 LangChain 的 orchestration 换成更模块化的 Chain/Agent 架构（若你需要）。