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
    method: 'post',
    timeout: 60000 // 60秒超时，适应AI生成的长时间处理
  })
}

// 执行步骤3：检索并生成章节内容
export function executeStep3(taskId) {
  return request({
    url: '/system/report/step3/' + taskId,
    method: 'post',
    timeout: 120000 // 120秒超时，内容生成需要更长时间
  })
}

// 执行步骤4：组装润色报告
export function executeStep4(taskId) {
  return request({
    url: '/system/report/step4/' + taskId,
    method: 'post',
    timeout: 180000 // 180秒超时，报告组装和润色耗时最长
  })
}

// 执行步骤5：生成摘要和关键词
export function executeStep5(taskId) {
  return request({
    url: '/system/report/step5/' + taskId,
    method: 'post',
    timeout: 60000 // 60秒超时
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

// 重新执行步骤
export function rerunStep(taskId, step, data) {
  return request({
    url: `/system/report/${taskId}/rerun/${step}`,
    method: 'post',
    data: data
  })
}

// 获取报告编辑内容
export function getReportEditContent(taskId) {
  return request({
    url: `/system/report/${taskId}/edit-content`,
    method: 'get'
  })
}

// 更新报告编辑内容
export function updateReportContent(data) {
  return request({
    url: '/system/report/update-content',
    method: 'post',
    data: data
  })
}

// 保存章节内容
export function saveChapterContent(taskId, chapterId, data) {
  return request({
    url: `/system/report/${taskId}/chapter/${chapterId}`,
    method: 'put',
    data: data
  })
}

// ==================== 报告发布和归档API ====================

// 发布报告
export function publishReport(taskId) {
  return request({
    url: '/system/report/publish/' + taskId,
    method: 'post'
  })
}

// 归档报告
export function archiveReport(taskId) {
  return request({
    url: '/system/report/archive/' + taskId,
    method: 'post'
  })
}

// 批量归档报告
export function batchArchiveReports(taskIds) {
  return request({
    url: '/system/report/archive/batch',
    method: 'post',
    data: taskIds
  })
}

// 取消发布报告
export function unpublishReport(taskId) {
  return request({
    url: '/system/report/unpublish/' + taskId,
    method: 'post'
  })
}

// 恢复归档报告
export function restoreReport(taskId) {
  return request({
    url: '/system/report/restore/' + taskId,
    method: 'post'
  })
}