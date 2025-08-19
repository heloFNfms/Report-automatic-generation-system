-- ----------------------------
-- 报告任务表
-- ----------------------------
drop table if exists report_task;
create table report_task (
  task_id           varchar(64)     not null                   comment '任务ID',
  title             varchar(200)    default ''                 comment '任务标题',
  description       varchar(500)    default ''                 comment '任务描述',
  topic             varchar(500)    not null                   comment '报告主题',
  status            char(1)         default '0'                comment '任务状态（0待处理 1进行中 2已完成 3失败）',
  current_step      varchar(20)     default 'step1'            comment '当前步骤（step1-step5）',
  progress          int(3)          default 0                  comment '进度百分比',
  content           longtext                                   comment '报告内容（JSON格式）',
  error_message     varchar(2000)   default ''                 comment '错误信息',
  start_time        datetime                                   comment '开始时间',
  end_time          datetime                                   comment '完成时间',
  user_id           bigint(20)                                 comment '创建者ID',
  user_name         varchar(64)     default ''                 comment '创建者名称',
  config_params     text                                       comment '配置参数（JSON格式）',
  orchestrator_task_id varchar(64)   default ''                 comment '编排器任务ID',
  company_name      varchar(200)    default ''                 comment '公司名称',
  create_by         varchar(64)     default ''                 comment '创建者',
  create_time       datetime                                   comment '创建时间',
  update_by         varchar(64)     default ''                 comment '更新者',
  update_time       datetime                                   comment '更新时间',
  remark            varchar(500)    default null               comment '备注',
  primary key (task_id)
) engine=innodb comment = '报告任务表';

-- ----------------------------
-- 报告步骤历史表
-- ----------------------------
drop table if exists report_step_history;
create table report_step_history (
  id                bigint(20)      not null auto_increment    comment '历史记录ID',
  task_id           varchar(64)     not null                   comment '任务ID',
  step              varchar(20)     not null                   comment '步骤名称（step1-step5）',
  version           int(11)         default 1                  comment '版本号',
  output_json       longtext                                   comment '步骤输出（JSON格式）',
  execution_time    int(11)         default 0                  comment '执行时间（秒）',
  status            char(1)         default '1'                comment '执行状态（0失败 1成功）',
  error_message     varchar(2000)   default ''                 comment '错误信息',
  create_time       datetime                                   comment '创建时间',
  primary key (id),
  key idx_task_step (task_id, step),
  key idx_task_step_version (task_id, step, version)
) engine=innodb auto_increment=1 comment = '报告步骤历史表';

-- ----------------------------
-- 初始化菜单数据
-- ----------------------------
-- 报告生成菜单（使用INSERT ... ON DUPLICATE KEY UPDATE避免重复插入）
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark) 
VALUES ('2000', '报告生成', '0', '5', 'report', null, '', '', 1, 0, 'M', '0', '0', '', 'documentation', 'admin', sysdate(), '', null, '报告生成目录')
ON DUPLICATE KEY UPDATE menu_name='报告生成', icon='documentation';

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark) 
VALUES ('2001', '任务管理', '2000', '1', 'task', 'system/report/index', '', '', 1, 0, 'C', '0', '0', 'system:report:list', 'list', 'admin', sysdate(), '', null, '报告任务管理菜单')
ON DUPLICATE KEY UPDATE menu_name='任务管理', icon='list';

-- 报告生成按钮
insert into sys_menu values('2002', '任务查询', '2001', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:query', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2003', '任务新增', '2001', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:add', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2004', '任务修改', '2001', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:edit', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2005', '任务删除', '2001', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:remove', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2006', '任务导出', '2001', '5', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:export', '#', 'admin', sysdate(), '', null, '');
insert into sys_menu values('2007', '生成报告', '2001', '6', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:generate', '#', 'admin', sysdate(), '', null, '');

-- ----------------------------
-- 初始化角色菜单关联数据
-- ----------------------------
-- 管理员角色关联报告生成菜单
insert into sys_role_menu values ('1', '2000');
insert into sys_role_menu values ('1', '2001');
insert into sys_role_menu values ('1', '2002');
insert into sys_role_menu values ('1', '2003');
insert into sys_role_menu values ('1', '2004');
insert into sys_role_menu values ('1', '2005');
insert into sys_role_menu values ('1', '2006');
insert into sys_role_menu values ('1', '2007');

-- ----------------------------
-- 示例数据
-- ----------------------------
insert into report_task values('demo-task-001', '人工智能医疗应用研究', '探讨人工智能技术在医疗领域的应用现状与发展趋势', '人工智能在医疗领域的应用', '2', 'step5', 100, null, '', '2024-01-01 10:00:00', '2024-01-01 12:30:00', 1, 'admin', null, 'admin', '2024-01-01 10:00:00', 'admin', '2024-01-01 12:30:00', '示例报告任务');
insert into report_task values('demo-task-002', '区块链技术发展分析', '分析区块链技术的发展现状、挑战与未来趋势', '区块链技术发展趋势分析', '1', 'step3', 60, null, '', '2024-01-01 14:00:00', null, 1, 'admin', null, 'admin', '2024-01-01 14:00:00', 'admin', '2024-01-01 14:30:00', '示例报告任务');

commit;