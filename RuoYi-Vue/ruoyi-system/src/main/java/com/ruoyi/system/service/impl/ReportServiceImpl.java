package com.ruoyi.system.service.impl;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.system.domain.ReportTask;
import com.ruoyi.system.mapper.ReportTaskMapper;
import com.ruoyi.system.service.IReportService;

/**
 * 报告生成Service业务层处理
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
@Service
public class ReportServiceImpl implements IReportService {
    @Autowired
    private ReportTaskMapper reportTaskMapper;

    @Autowired
    @Qualifier("reportRestTemplate")
    private RestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Value("${report.orchestrator.url:http://localhost:9000}")
    private String orchestratorUrl;

    /**
     * 查询报告任务
     * 
     * @param taskId 报告任务主键
     * @return 报告任务
     */
    @Override
    public ReportTask selectReportTaskByTaskId(String taskId) {
        return reportTaskMapper.selectReportTaskByTaskId(taskId);
    }

    /**
     * 查询报告任务列表
     * 
     * @param reportTask 报告任务
     * @return 报告任务
     */
    @Override
    public List<ReportTask> selectReportTaskList(ReportTask reportTask) {
        return reportTaskMapper.selectReportTaskList(reportTask);
    }

    /**
     * 新增报告任务
     * 
     * @param reportTask 报告任务
     * @return 结果
     */
    @Override
    public int insertReportTask(ReportTask reportTask) {
        if (reportTask.getTaskId() == null || reportTask.getTaskId().isEmpty()) {
            reportTask.setTaskId(UUID.randomUUID().toString().replace("-", ""));
        }
        reportTask.setUserId(SecurityUtils.getUserId());
        reportTask.setUserName(SecurityUtils.getUsername());
        reportTask.setCreateTime(DateUtils.getNowDate());
        return reportTaskMapper.insertReportTask(reportTask);
    }

    /**
     * 修改报告任务
     * 
     * @param reportTask 报告任务
     * @return 结果
     */
    @Override
    public int updateReportTask(ReportTask reportTask) {
        reportTask.setUpdateTime(DateUtils.getNowDate());
        return reportTaskMapper.updateReportTask(reportTask);
    }

    /**
     * 批量删除报告任务
     * 
     * @param taskIds 需要删除的报告任务主键
     * @return 结果
     */
    @Override
    public int deleteReportTaskByTaskIds(String[] taskIds) {
        return reportTaskMapper.deleteReportTaskByTaskIds(taskIds);
    }

    /**
     * 删除报告任务信息
     * 
     * @param taskId 报告任务主键
     * @return 结果
     */
    @Override
    public int deleteReportTaskByTaskId(String taskId) {
        return reportTaskMapper.deleteReportTaskByTaskId(taskId);
    }

    /**
     * 启动报告生成
     * 
     * @param reportTask 报告任务
     * @return 任务ID
     */
    @Override
    public String startReportGeneration(ReportTask reportTask) throws Exception {
        // 生成任务ID
        String taskId = UUID.randomUUID().toString().replace("-", "");
        reportTask.setTaskId(taskId);
        reportTask.setStatus("1"); // 进行中
        reportTask.setCurrentStep("step1");
        reportTask.setProgress(0);
        reportTask.setStartTime(new Date());
        reportTask.setUserId(SecurityUtils.getUserId());
        reportTask.setUserName(SecurityUtils.getUsername());
        reportTask.setCreateTime(DateUtils.getNowDate());

        // 保存任务到数据库
        reportTaskMapper.insertReportTask(reportTask);

        // 调用Python编排器启动报告生成
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("task_id", taskId);
        requestBody.put("topic", reportTask.getTopic());
        requestBody.put("title", reportTask.getTitle());
        requestBody.put("description", reportTask.getDescription());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        try {
            ResponseEntity<String> response = restTemplate.exchange(
                    orchestratorUrl + "/step1",
                    HttpMethod.POST,
                    entity,
                    String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                // 异步启动后续步骤
                startAsyncReportGeneration(taskId);
                return taskId;
            } else {
                throw new Exception("启动报告生成失败: " + response.getBody());
            }
        } catch (Exception e) {
            // 更新任务状态为失败
            reportTask.setStatus("3");
            reportTask.setErrorMessage(e.getMessage());
            reportTaskMapper.updateReportTask(reportTask);
            throw e;
        }
    }

    /**
     * 异步启动报告生成流程
     */
    private void startAsyncReportGeneration(String taskId) {
        new Thread(() -> {
            try {
                // 依次执行step2-step5
                executeStep(taskId, "step2");
                executeStep(taskId, "step3");
                executeStep(taskId, "step4");
                executeStep(taskId, "step5");

                // 更新任务状态为完成
                ReportTask task = new ReportTask();
                task.setTaskId(taskId);
                task.setStatus("2"); // 已完成
                task.setProgress(100);
                task.setEndTime(new Date());
                task.setUpdateTime(DateUtils.getNowDate());
                reportTaskMapper.updateReportTask(task);

            } catch (Exception e) {
                // 更新任务状态为失败
                ReportTask task = new ReportTask();
                task.setTaskId(taskId);
                task.setStatus("3"); // 失败
                task.setErrorMessage(e.getMessage());
                task.setUpdateTime(DateUtils.getNowDate());
                reportTaskMapper.updateReportTask(task);
            }
        }).start();
    }

    /**
     * 执行指定步骤
     */
    private void executeStep(String taskId, String step) throws Exception {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("task_id", taskId);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/" + step,
                HttpMethod.POST,
                entity,
                String.class);

        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new Exception("执行" + step + "失败: " + response.getBody());
        }

        // 更新当前步骤和进度
        ReportTask task = new ReportTask();
        task.setTaskId(taskId);
        task.setCurrentStep(step);
        task.setProgress(getProgressByStep(step));
        task.setUpdateTime(DateUtils.getNowDate());
        reportTaskMapper.updateReportTask(task);
    }

    /**
     * 根据步骤获取进度
     */
    private Integer getProgressByStep(String step) {
        switch (step) {
            case "step1":
                return 20;
            case "step2":
                return 40;
            case "step3":
                return 60;
            case "step4":
                return 80;
            case "step5":
                return 100;
            default:
                return 0;
        }
    }

    /**
     * 获取报告生成状态
     * 
     * @param taskId 任务ID
     * @return 状态信息
     */
    @Override
    public Map<String, Object> getReportStatus(String taskId) throws Exception {
        ReportTask task = reportTaskMapper.selectReportTaskByTaskId(taskId);
        if (task == null) {
            throw new Exception("任务不存在");
        }

        Map<String, Object> result = new HashMap<>();
        result.put("taskId", task.getTaskId());
        result.put("status", task.getStatus());
        result.put("currentStep", task.getCurrentStep());
        result.put("progress", task.getProgress());
        result.put("errorMessage", task.getErrorMessage());
        result.put("startTime", task.getStartTime());
        result.put("endTime", task.getEndTime());

        return result;
    }

    /**
     * 获取报告内容
     * 
     * @param taskId 任务ID
     * @return 报告内容
     */
    @Override
    public Map<String, Object> getReportContent(String taskId) throws Exception {
        // 调用Python编排器获取报告内容
        ResponseEntity<String> response = restTemplate.getForEntity(
                orchestratorUrl + "/tasks/" + taskId,
                String.class);

        if (response.getStatusCode().is2xxSuccessful()) {
            return objectMapper.readValue(response.getBody(), Map.class);
        } else {
            throw new Exception("获取报告内容失败: " + response.getBody());
        }
    }

    /**
     * 重新执行报告步骤
     * 
     * @param taskId 任务ID
     * @param step   步骤名称
     */
    @Override
    public void rerunReportStep(String taskId, String step) throws Exception {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("task_id", taskId);
        requestBody.put("step", step);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/rerun",
                HttpMethod.POST,
                entity,
                String.class);

        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new Exception("重新执行步骤失败: " + response.getBody());
        }
    }

    /**
     * 回滚报告到指定版本
     * 
     * @param taskId  任务ID
     * @param step    步骤名称
     * @param version 版本号
     */
    @Override
    public void rollbackReportStep(String taskId, String step, Integer version) throws Exception {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("task_id", taskId);
        requestBody.put("step", step);
        requestBody.put("version", version);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/rollback",
                HttpMethod.POST,
                entity,
                String.class);

        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new Exception("回滚报告版本失败: " + response.getBody());
        }
    }

    @Override
    public String exportReport(String taskId, String format, boolean uploadToOss) throws Exception {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("format", format);
        requestBody.put("upload_to_oss", uploadToOss);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        ResponseEntity<Map> response = restTemplate.exchange(
                orchestratorUrl + "/export/" + taskId,
                HttpMethod.POST,
                entity,
                Map.class);

        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new Exception("导出失败: " + response.getBody());
        }

        Map<String, Object> result = response.getBody();
        return (String) result.get("download_url");
    }

    @Override
    public void downloadReport(String taskId, String filename, javax.servlet.http.HttpServletResponse response)
            throws Exception {
        try {
            ResponseEntity<byte[]> fileResponse = restTemplate.exchange(
                    orchestratorUrl + "/download/" + taskId + "/" + filename,
                    HttpMethod.GET,
                    null,
                    byte[].class);

            if (!fileResponse.getStatusCode().is2xxSuccessful()) {
                throw new Exception("下载文件失败");
            }

            byte[] fileData = fileResponse.getBody();
            if (fileData == null) {
                throw new Exception("文件数据为空");
            }

            // 设置响应头
            String contentType = filename.endsWith(".pdf") ? "application/pdf"
                    : "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            response.setContentType(contentType);
            response.setHeader("Content-Disposition", "attachment; filename=\"" + filename + "\"");
            response.setContentLength(fileData.length);

            // 写入响应流
            response.getOutputStream().write(fileData);
            response.getOutputStream().flush();

        } catch (Exception e) {
            throw new Exception("下载文件失败: " + e.getMessage());
        }
    }

    @Override
    public boolean cleanupFiles(String taskId) throws Exception {
        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                    orchestratorUrl + "/cleanup/" + taskId,
                    HttpMethod.DELETE,
                    null,
                    Map.class);

            if (!response.getStatusCode().is2xxSuccessful()) {
                return false;
            }

            Map<String, Object> result = response.getBody();
            return result != null && Boolean.TRUE.equals(result.get("success"));

        } catch (Exception e) {
            throw new Exception("清理文件失败: " + e.getMessage());
        }
    }

    // ==================== 分步骤执行方法实现 ====================

    /**
     * 执行步骤1：保存主题到数据库
     */
    @Override
    public String executeStep1(ReportTask reportTask) throws Exception {
        // 生成任务ID
        String taskId = UUID.randomUUID().toString();
        reportTask.setTaskId(taskId);
        reportTask.setStatus("step1");
        reportTask.setProgress(20);
        reportTask.setCreateTime(DateUtils.getNowDate());
        reportTask.setCreateBy(SecurityUtils.getUsername());

        // 保存到数据库
        insertReportTask(reportTask);

        // 调用编排器的step1接口
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("project_name", reportTask.getTitle());
        requestBody.put("company_name", reportTask.getCompanyName());
        requestBody.put("research_content", reportTask.getDescription());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step1",
                HttpMethod.POST,
                entity,
                String.class);

        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new Exception("执行步骤1失败: " + response.getBody());
        }

        // 解析编排器返回的task_id
        try {
            Map<String, Object> responseData = objectMapper.readValue(response.getBody(), Map.class);
            String orchestratorTaskId = (String) responseData.get("task_id");

            // 更新数据库中的任务记录，保存编排器的task_id
            ReportTask updateTask = new ReportTask();
            updateTask.setTaskId(taskId);
            updateTask.setOrchestratorTaskId(orchestratorTaskId);
            updateTask.setStatus("step1_done");
            updateReportTask(updateTask);
        } catch (Exception e) {
            // 如果解析失败，仍然返回Java端的taskId
            System.err.println("解析编排器响应失败: " + e.getMessage());
        }

        return taskId;
    }

    /**
     * 执行步骤2：生成研究大纲
     */
    @Override
    public Object executeStep2(String taskId) throws Exception {
        // 更新任务状态
        ReportTask task = selectReportTaskByTaskId(taskId);
        if (task != null) {
            task.setStatus("step2");
            task.setProgress(40);
            updateReportTask(task);
        }

        // 调用编排器的step2接口
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step2/" + taskId,
                HttpMethod.POST,
                null,
                String.class);

        if (response.getStatusCode().is2xxSuccessful()) {
            return objectMapper.readValue(response.getBody(), Object.class);
        } else {
            throw new Exception("执行步骤2失败: " + response.getBody());
        }
    }

    /**
     * 执行步骤3：检索并生成章节内容
     */
    @Override
    public Object executeStep3(String taskId) throws Exception {
        // 更新任务状态
        ReportTask task = selectReportTaskByTaskId(taskId);
        if (task != null) {
            task.setStatus("step3");
            task.setProgress(60);
            updateReportTask(task);
        }

        // 调用编排器的step3接口
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step3/" + taskId,
                HttpMethod.POST,
                null,
                String.class);

        if (response.getStatusCode().is2xxSuccessful()) {
            return objectMapper.readValue(response.getBody(), Object.class);
        } else {
            throw new Exception("执行步骤3失败: " + response.getBody());
        }
    }

    /**
     * 执行步骤4：组装润色报告
     */
    @Override
    public Object executeStep4(String taskId) throws Exception {
        // 更新任务状态
        ReportTask task = selectReportTaskByTaskId(taskId);
        if (task != null) {
            task.setStatus("step4");
            task.setProgress(80);
            updateReportTask(task);
        }

        // 调用编排器的step4接口
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step4/" + taskId,
                HttpMethod.POST,
                null,
                String.class);

        if (response.getStatusCode().is2xxSuccessful()) {
            return objectMapper.readValue(response.getBody(), Object.class);
        } else {
            throw new Exception("执行步骤4失败: " + response.getBody());
        }
    }

    /**
     * 执行步骤5：生成摘要和关键词
     */
    @Override
    public Object executeStep5(String taskId) throws Exception {
        // 更新任务状态
        ReportTask task = selectReportTaskByTaskId(taskId);
        if (task != null) {
            task.setStatus("completed");
            task.setProgress(100);
            updateReportTask(task);
        }

        // 调用编排器的step5接口
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step5/" + taskId,
                HttpMethod.POST,
                null,
                String.class);

        if (response.getStatusCode().is2xxSuccessful()) {
            return objectMapper.readValue(response.getBody(), Object.class);
        } else {
            throw new Exception("执行步骤5失败: " + response.getBody());
        }
    }

    /**
     * 获取指定步骤的结果
     */
    @Override
    public Object getStepResult(String taskId, String step) throws Exception {
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step-result/" + taskId + "/" + step,
                HttpMethod.GET,
                null,
                String.class);

        if (response.getStatusCode().is2xxSuccessful()) {
            return objectMapper.readValue(response.getBody(), Object.class);
        } else {
            throw new Exception("获取步骤结果失败: " + response.getBody());
        }
    }

    /**
     * 获取指定步骤的历史版本
     */
    @Override
    public Object getStepHistory(String taskId, String step) throws Exception {
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step-history/" + taskId + "/" + step,
                HttpMethod.GET,
                null,
                String.class);

        if (response.getStatusCode().is2xxSuccessful()) {
            return objectMapper.readValue(response.getBody(), Object.class);
        } else {
            throw new Exception("获取步骤历史失败: " + response.getBody());
        }
    }
}