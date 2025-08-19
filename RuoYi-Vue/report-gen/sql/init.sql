-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS analyze_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE analyze_db;

-- 创建报告任务表
CREATE TABLE IF NOT EXISTS report_tasks (
    id VARCHAR(255) PRIMARY KEY,
    topic TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建报告步骤表
CREATE TABLE IF NOT EXISTS report_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    step VARCHAR(50) NOT NULL,
    output_json JSON,
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task_step (task_id, step),
    INDEX idx_task_step_version (task_id, step, version),
    FOREIGN KEY (task_id) REFERENCES report_tasks(id) ON DELETE CASCADE
);

-- 插入示例数据（可选）
INSERT IGNORE INTO report_tasks (id, topic, status) VALUES 
('demo-task-001', '人工智能在医疗领域的应用', 'pending'),
('demo-task-002', '区块链技术发展趋势分析', 'pending');

COMMIT;