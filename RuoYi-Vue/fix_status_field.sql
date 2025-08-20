-- 修复report_task表status字段长度问题
ALTER TABLE report_task MODIFY COLUMN status varchar(20) DEFAULT '0' COMMENT '任务状态（0待处理 1进行中 2已完成 3失败 或step1_done等）';