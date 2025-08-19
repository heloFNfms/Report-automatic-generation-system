import request from '@/utils/request'

// 查询报告任务列表
export function listReport(query) {
  return request({
    url: '/system/report/list',
    method: 'get',
    params: query
  })
}

// 查询报告任务详细
export function getReport(taskId) {
  return request({
    url: '/system/report/' + taskId,
    method: 'get'
  })
}

// 新增报告任务
export function addReport(data) {
  return request({
    url: '/system/report',
    method: 'post',
    data: data
  })
}

// 修改报告任务
export function updateReport(data) {
  return request({
    url: '/system/report',
    method: 'put',
    data: data
  })
}

// 删除报告任务
export function delReport(taskId) {
  return request({
    url: '/system/report/' + taskId,
    method: 'delete'
  })
}

// 开始生成报告
export function startReport(data) {
  return request({
    url: '/system/report/start',
    method: 'post',
    data: data
  })
}

// 获取报告状态
export function getReportStatus(taskId) {
  return request({
    url: '/system/report/status/' + taskId,
    method: 'get'
  })
}

// 获取报告内容
export function getReportContent(taskId) {
  return request({
    url: '/system/report/content/' + taskId,
    method: 'get'
  })
}

// 重新执行报告步骤
export function rerunReportStep(taskId, step) {
  return request({
    url: '/system/report/rerun/' + taskId + '/' + step,
    method: 'post'
  })
}

// 回滚报告版本
export function rollbackReport(taskId, step, version) {
  return request({
    url: '/system/report/rollback/' + taskId + '/' + step + '/' + version,
    method: 'post'
  })
}

// 导出报告任务列表
export function exportReportList(query) {
  return request({
    url: '/system/report/export',
    method: 'post',
    data: query
  })
}

// 导出报告文档
export function exportReport(taskId, data) {
  return request({
    url: '/system/report/export/' + taskId,
    method: 'post',
    data: data
  })
}

// 下载报告文件
export function downloadReportFile(taskId, filename) {
  return request({
    url: '/system/report/download/' + taskId + '/' + filename,
    method: 'get',
    responseType: 'blob'
  })
}

// 清理临时文件
export function cleanupFiles(taskId) {
  return request({
    url: '/system/report/cleanup/' + taskId,
    method: 'delete'
  })
}

// ==================== 分步骤执行API ====================

// 执行步骤1：保存主题到数据库
export function executeStep1(data) {
  return request({
    url: '/system/report/step1',
    method: 'post',
    data: data
  })
}

// 执行步骤2：生成研究大纲
export function executeStep2(taskId) {
  return request({
    url: '/system/report/step2/' + taskId,
    method: 'post'
  })
}

// 执行步骤3：检索并生成章节内容
export function executeStep3(taskId) {
  return request({
    url: '/system/report/step3/' + taskId,
    method: 'post'
  })
}

// 执行步骤4：组装润色报告
export function executeStep4(taskId) {
  return request({
    url: '/system/report/step4/' + taskId,
    method: 'post'
  })
}

// 执行步骤5：生成摘要和关键词
export function executeStep5(taskId) {
  return request({
    url: '/system/report/step5/' + taskId,
    method: 'post'
  })
}

// 获取指定步骤的结果
export function getStepResult(taskId, step) {
  return request({
    url: '/system/report/step-result/' + taskId + '/' + step,
    method: 'get'
  })
}

// 获取指定步骤的历史版本
export function getStepHistory(taskId, step) {
  return request({
    url: '/system/report/step-history/' + taskId + '/' + step,
    method: 'get'
  })
}