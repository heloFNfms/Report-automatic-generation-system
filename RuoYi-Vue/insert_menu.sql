-- 插入报告生成菜单数据
INSERT INTO sys_menu VALUES('2000', '报告生成', '0', '5', 'report', null, '', '', 1, 0, 'M', '0', '0', '', 'documentation', 'admin', NOW(), '', null, '报告生成目录');
INSERT INTO sys_menu VALUES('2001', '任务管理', '2000', '1', 'task', 'system/report/index', '', '', 1, 0, 'C', '0', '0', 'system:report:list', 'list', 'admin', NOW(), '', null, '报告任务管理菜单');

-- 报告生成按钮权限
INSERT INTO sys_menu VALUES('2002', '任务查询', '2001', '1', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:query', '#', 'admin', NOW(), '', null, '');
INSERT INTO sys_menu VALUES('2003', '任务新增', '2001', '2', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:add', '#', 'admin', NOW(), '', null, '');
INSERT INTO sys_menu VALUES('2004', '任务修改', '2001', '3', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:edit', '#', 'admin', NOW(), '', null, '');
INSERT INTO sys_menu VALUES('2005', '任务删除', '2001', '4', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:remove', '#', 'admin', NOW(), '', null, '');
INSERT INTO sys_menu VALUES('2006', '任务导出', '2001', '5', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:export', '#', 'admin', NOW(), '', null, '');
INSERT INTO sys_menu VALUES('2007', '生成报告', '2001', '6', '#', '', '', '', 1, 0, 'F', '0', '0', 'system:report:generate', '#', 'admin', NOW(), '', null, '');

-- 管理员角色关联报告生成菜单
INSERT INTO sys_role_menu VALUES ('1', '2000');
INSERT INTO sys_role_menu VALUES ('1', '2001');
INSERT INTO sys_role_menu VALUES ('1', '2002');
INSERT INTO sys_role_menu VALUES ('1', '2003');
INSERT INTO sys_role_menu VALUES ('1', '2004');
INSERT INTO sys_role_menu VALUES ('1', '2005');
INSERT INTO sys_role_menu VALUES ('1', '2006');
INSERT INTO sys_role_menu VALUES ('1', '2007');

COMMIT;