## 新流程对齐
- Step1：保存主题
- Step2：**大纲（DeepSeek，纯模型，无检索）**
- Step3：**内容生成（仅此步调用 MCP: arxiv_search） + 向量检索 RAG + 参考网址**
- Step4：**润色**，输出主体报告（Markdown）
- Step5：**摘要&关键词** + 输出完整文章（文首含摘要/关键词）

## 启动
1) 启动 MCP：
```
cd services/report-mcp
cp .env.example .env
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```
2) 启动 Orchestrator：
```
cd ../report-orchestrator
cp .env.example .env  # 填 DEEPSEEK_*，MCP_BASE
pip install -r requirements.txt
uvicorn app:app --reload --port 9000
```

## 可选：向量库
- 默认 FAISS（内存、轻量）
- 切换 PGVector：`.env` 设置 `VECTOR_BACKEND=pgvector` 并配置 `PG_DSN`，确保已安装 `pgvector` 扩展：
```
CREATE EXTENSION IF NOT EXISTS vector;
```
并创建表结构（代码会自动建表）。

## 对接若依（RuoYi）
- 后端 `ReportController` 依次调用 `/step1..5` 并写入 MySQL 的 `report_task` / `report_step`。
- 前端展示树状大纲与逐章内容，Step3 返回的 `参考网址` 渲染为可点链接；Step5 展示“完整文章”，支持导出 PDF/Word。

## 安全与生产建议
- 为 `/step*` 增加 API Key / JWT 校验与速率限制。
- DeepSeek 返回 JSON 的健壮解析与重试。
- Step3 的 MCP 调用加熔断与重试；向量库结果加过期策略与去重。
