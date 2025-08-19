-- 创建简单视图以对齐编排器和Java后端的表名
-- 由于MySQL不支持INSTEAD OF触发器，我们创建简单的查询视图

USE analyze_db;

-- 创建 rg_task 视图，映射到 report_task 表（只读）
CREATE OR REPLACE VIEW rg_task AS
SELECT 
    task_id as id,
    COALESCE(
        JSON_UNQUOTE(JSON_EXTRACT(config_params, '$.project_name')),
        SUBSTRING_INDEX(title, ' - ', 1)
    ) as project_name,
    COALESCE(
        JSON_UNQUOTE(JSON_EXTRACT(config_params, '$.company_name')),
        ''
    ) as company_name,
    description as research_content,
    CASE 
        WHEN status = '0' THEN 'created'
        WHEN status = '1' THEN 'processing'
        WHEN status = '2' THEN 'completed'
        WHEN status = '3' THEN 'failed'
        ELSE 'created'
    END as status,
    create_time as created_at,
    update_time as updated_at
FROM report_task;

-- 创建 rg_step 视图，映射到 report_step_history 表（只读）
CREATE OR REPLACE VIEW rg_step AS
SELECT 
    id,
    task_id,
    step,
    CAST(output_json AS JSON) as output_json,
    version,
    create_time as created_at,
    create_time as updated_at
FROM report_step_history;

COMMIT;