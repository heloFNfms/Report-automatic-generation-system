# 报告自动化生成系统

一个基于 MCP (Model Context Protocol) 和 DeepSeek 的智能报告生成系统，支持从主题到最终报告的全流程自动化生成。

## 🚀 核心特性

### ✅ 已完成的关键改进

1. **修复 DeepSeek 客户端**
   - 更正 API 路径为 `/v1/chat/completions`
   - 添加模型参数支持（从环境变量读取）
   - 增强 JSON 解析容错性

2. **Step3 性能优化**
   - 集成 BM25 重排序算法
   - 基于 token 预算的上下文长度控制
   - 并行化章节内容生成（限制并发数为3）

3. **历史管理和回退**
   - 查询步骤历史版本接口
   - 重跑指定步骤功能
   - 回滚到指定版本功能

4. **部署编排**
   - 完整的 docker-compose 配置
   - 支持 MySQL、Redis、PGVector
   - 网络隔离和服务发现
   - 一键启动脚本

5. **向量库持久化**
   - FAISS 版本化存储
   - 文本去重机制
   - 自动清理旧版本
   - 统计信息接口

6. **日志和可观测性**
   - 结构化 JSON 日志
   - 请求 ID 追踪
   - 性能监控
   - 错误告警

7. **安全和速率控制**
   - IP 白名单/黑名单
   - 速率限制（每小时100次）
   - 并发控制（最大10个）
   - 请求追踪

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RuoYi-Vue     │    │  Orchestrator   │    │   MCP Server    │
│   前端界面      │◄──►│   编排服务      │◄──►│   工具服务      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     MySQL       │    │     Redis       │
                       │   持久化存储    │    │   缓存服务      │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   DeepSeek API  │
                       │   大模型服务    │
                       └─────────────────┘
```

## 📋 五步报告生成流程

1. **Step1**: 保存主题到数据库
2. **Step2**: 调用 DeepSeek 生成研究大纲
3. **Step3**: 通过 MCP 检索文献，结合 RAG 生成内容
4. **Step4**: 组装并润色报告内容
5. **Step5**: 生成摘要和关键词，完成最终报告

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.11+
- MySQL 8.0+
- Redis 7+

### 一键部署

```bash
# 克隆项目
git clone <repository-url>
cd report-gen

# 配置环境变量
cp report-orchestrator/.env.example report-orchestrator/.env
cp report-mcp/.env.example report-mcp/.env

# 启动所有服务
./start.bat  # Windows
# 或
docker-compose up -d --build  # Linux/Mac
```

### 服务访问地址

- **Orchestrator API**: http://localhost:9000
- **MCP Server**: http://localhost:8000
- **MySQL**: localhost:3306
- **Redis**: localhost:6379

## 🔧 配置说明

### Orchestrator 环境变量

```env
# MCP 服务配置
MCP_BASE=http://report-mcp:8000

# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 数据库配置
MYSQL_DSN=mysql+asyncmy://user:password@mysql:3306/analyze_db?charset=utf8mb4

# 向量存储配置
VECTOR_BACKEND=faiss
FAISS_INDEX_PATH=/app/data/faiss.index
FAISS_META_PATH=/app/data/faiss_meta.json

# 安全配置
API_WHITELIST=127.0.0.1,localhost
API_BLACKLIST=
```

### MCP 环境变量

```env
# Redis 配置
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600
```

## 📊 API 接口

### 核心流程接口

- `POST /step1` - 保存主题
- `POST /step2` - 生成大纲
- `POST /step3` - 生成内容
- `POST /step4` - 组装报告
- `POST /step5` - 完成报告

### 管理接口

- `GET /task/{task_id}` - 查询任务状态
- `GET /task/{task_id}/history/{step}` - 查询步骤历史
- `POST /rerun` - 重跑指定步骤
- `POST /rollback` - 回滚到指定版本
- `GET /health` - 健康检查

## 🔍 监控和日志

### 日志文件位置

- **Orchestrator**: `logs/orchestrator.log`
- **容器日志**: `docker-compose logs -f`

### 日志格式

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "report_orchestrator",
  "message": "Request completed",
  "request_id": "uuid-here",
  "task_id": "task-123",
  "duration": 1.234,
  "client_ip": "127.0.0.1"
}
```

## 🛠️ 开发指南

### 本地开发

```bash
# 安装依赖
cd report-orchestrator
pip install -r requirements.txt

cd ../report-mcp
pip install -r requirements.txt

# 启动服务
uvicorn app:app --host 0.0.0.0 --port 9000  # Orchestrator
uvicorn server:app --host 0.0.0.0 --port 8000  # MCP
```

### 扩展 MCP 工具

在 `report-mcp/tools/` 目录下添加新的工具模块：

```python
# tools/new_tool.py
async def new_tool_handler(params: dict) -> dict:
    """新工具处理函数"""
    return {"result": "success"}
```

## 📈 性能优化

### 已实现的优化

- **并行处理**: Step3 章节并发生成
- **缓存机制**: Redis 缓存 MCP 结果
- **向量去重**: 避免重复存储相同文本
- **Token 控制**: 防止超长 Prompt
- **连接池**: 数据库连接复用

### 性能指标

- **Step3 并发度**: 3个章节同时处理
- **速率限制**: 每小时100次请求
- **并发限制**: 最大10个同时请求
- **缓存TTL**: 1小时

## 🔒 安全特性

- **IP 白名单**: 限制访问来源
- **速率限制**: 防止API滥用
- **并发控制**: 防止资源耗尽
- **请求追踪**: 完整的审计日志
- **错误隔离**: 异常不会影响其他请求

## 🚧 待完成功能

- [ ] RuoYi-SpringBoot 集成
- [ ] PDF/Word 导出功能
- [ ] OSS 文件上传
- [ ] 更多 MCP 工具扩展
- [ ] 企业微信/钉钉告警
- [ ] 文本处理优化

## 📞 技术支持

如有问题，请查看：

1. **日志文件**: `logs/orchestrator.log`
2. **容器状态**: `docker-compose ps`
3. **服务健康**: `curl http://localhost:9000/health`

## MySQL（业务数据）
- 表：`rg_task`（用户输入与状态）、`rg_step`（每一步 JSON 输出）
- Orchestrator 在 Step1/2/3/4/5 自动写入 MySQL，支持回溯与重跑。


### MySQL 建表（如不用 SQLAlchemy 自动建表，也可手工执行）
```sql
CREATE TABLE IF NOT EXISTS rg_task (
id VARCHAR(36) PRIMARY KEY,
project_name VARCHAR(255) NOT NULL,
company_name VARCHAR(255) NULL,
research_content TEXT NOT NULL,
status VARCHAR(32) DEFAULT 'created',
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS rg_step (
id BIGINT PRIMARY KEY AUTO_INCREMENT,
task_id VARCHAR(36) NOT NULL,
step VARCHAR(32) NOT NULL,
output_json JSON NOT NULL,
version INT DEFAULT 1,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
INDEX idx_task_step (task_id, step),
CONSTRAINT fk_task FOREIGN KEY (task_id) REFERENCES rg_task(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```


## 向量库（知识数据）
- 默认 **FAISS**（内存 + 磁盘持久化到 `FAISS_INDEX_PATH`/`FAISS_META_PATH`）。
- 可切 **PGVector**（PostgreSQL + `vector` 扩展）。


### FAISS 持久化
- 启动时：自动 `load()`；新增数据即 `save()`，可在高并发场景中改为定时批量落盘。


### PGVector（可选）
- DSN 配置 `PG_DSN`，并在 Postgres 执行：`CREATE EXTENSION IF NOT EXISTS vector;`


## 接口顺序（RuoYi 调用）
- `/step1` → `/step2` → `/step3` → `/step4` → `/step5`
- 需要回显历史：`GET /task/{taskId}` + 查询 MySQL 的 `rg_step`（可在 orchestrator 另加查询接口）。


## 前端引用展示
- Step3 的 JSON 中每个章节含 `参考网址` 数组，直接渲染为可点击链接即可。

## 📄 许可证

MIT License