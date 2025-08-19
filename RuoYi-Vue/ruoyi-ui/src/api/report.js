import request from '@/utils/request'

// 执行步骤1 - 创建报告任务
export function executeStep1(data) {
  return request({
    url: '/system/report/step1',
    method: 'post',
    data: data
  })
}

// 执行步骤2 - 生成研究大纲
export function executeStep2(taskId) {
  return request({
    url: `/system/report/step2/${taskId}`,
    method: 'post'
  })
}

// 执行步骤3 - 章节内容生成
export function executeStep3(taskId) {
  return request({
    url: `/system/report/step3/${taskId}`,
    method: 'post'
  })
}

// 执行步骤4 - 报告组装润色
export function executeStep4(taskId) {
  return request({
    url: `/system/report/step4/${taskId}`,
    method: 'post'
  })
}

// 执行步骤5 - 完成报告
export function executeStep5(taskId) {
  return request({
    url: `/system/report/step5/${taskId}`,
    method: 'post'
  })
}

// 获取步骤结果
export function getStepResult(taskId, step) {
  return request({
    url: `/system/report/step/${taskId}/${step}`,
    method: 'get'
  })
}

// 获取任务状态
export function getTaskStatus(taskId) {
  return request({
    url: `/system/report/status/${taskId}`,
    method: 'get'
  })
}

// 重新执行某个步骤
export function rerunStep(taskId, step) {
  return request({
    url: `/system/report/rerun/${taskId}/${step}`,
    method: 'post'
  })
}

// 导出报告
export function exportReport(taskId, format = 'pdf') {
  return request({
    url: `/system/report/export/${taskId}`,
    method: 'post',
    data: { format },
    responseType: 'blob'
  })
}