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