-- 插入新的字典类型：报告发布状态
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, remark) 
VALUES (12, '报告发布状态', 'report_publish_status', '0', 'admin', sysdate(), '报告发布状态列表')
ON DUPLICATE KEY UPDATE dict_name = VALUES(dict_name), remark = VALUES(remark);

-- 插入字典数据：报告发布状态
INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark) VALUES
(33, 1, '草稿', '0', 'report_publish_status', '', 'info', 'Y', '0', 'admin', sysdate(), '报告草稿状态'),
(34, 2, '已发布', '1', 'report_publish_status', '', 'success', 'N', '0', 'admin', sysdate(), '报告已发布状态'),
(35, 3, '已归档', '2', 'report_publish_status', '', 'warning', 'N', '0', 'admin', sysdate(), '报告已归档状态')
ON DUPLICATE KEY UPDATE dict_label = VALUES(dict_label), remark = VALUES(remark);

-- 修正原有的report_status字典标签，使其更准确地反映任务执行状态
UPDATE sys_dict_data SET dict_label = '待处理', remark = '任务待处理状态' WHERE dict_type = 'report_status' AND dict_value = '0';
UPDATE sys_dict_data SET dict_label = '进行中', remark = '任务进行中状态' WHERE dict_type = 'report_status' AND dict_value = '1';
UPDATE sys_dict_data SET dict_label = '已完成', remark = '任务已完成状态' WHERE dict_type = 'report_status' AND dict_value = '2';

-- 如果不存在失败状态的字典数据，则添加
INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark) 
SELECT 36, 4, '失败', '3', 'report_status', '', 'danger', 'N', '0', 'admin', sysdate(), '任务失败状态'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_type = 'report_status' AND dict_value = '3');

-- 更新现有数据，将已完成的任务设置为草稿状态
UPDATE report_task SET publish_status = '0' WHERE status = '2';