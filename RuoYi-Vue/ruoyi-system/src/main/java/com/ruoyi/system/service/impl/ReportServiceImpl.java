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
import com.ruoyi.system.service.IOssService;
import com.ruoyi.system.exception.OrchestratorException;
import com.ruoyi.system.constants.OrchestratorErrorCode;

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

    @Autowired
    private IOssService ossService;

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
            reportTask.setStatus("3"); // 3失败
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
                task.setStatus("2"); // 2已完成
                task.setProgress(100);
                task.setEndTime(new Date());
                task.setUpdateTime(DateUtils.getNowDate());
                reportTaskMapper.updateReportTask(task);

            } catch (Exception e) {
                // 更新任务状态为失败
                ReportTask task = new ReportTask();
                task.setTaskId(taskId);
                task.setStatus("3"); // 3失败
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
            throw OrchestratorException.fromHttpError(
                    response.getStatusCodeValue(),
                    response.getBody(),
                    "执行" + step);
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
                orchestratorUrl + "/task/" + taskId,
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
            throw OrchestratorException.fromHttpError(
                    response.getStatusCodeValue(),
                    response.getBody(),
                    "重新执行步骤" + step);
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
            throw OrchestratorException.fromHttpError(
                    response.getStatusCodeValue(),
                    response.getBody(),
                    "回滚步骤" + step + "到版本" + version);
        }
    }

    @Override
    public String exportReport(String taskId, String format, boolean uploadToOss) throws Exception {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("task_id", taskId);
        requestBody.put("format", format);
        requestBody.put("upload_to_oss", uploadToOss);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        ResponseEntity<Map> response = restTemplate.exchange(
                orchestratorUrl + "/export",
                HttpMethod.POST,
                entity,
                Map.class);

        if (!response.getStatusCode().is2xxSuccessful()) {
            String errorMessage = "导出" + format.toUpperCase() + "格式报告失败";
            if (response.getBody() != null) {
                Map<String, Object> errorBody = response.getBody();
                if (errorBody.containsKey("error")) {
                    errorMessage = errorBody.get("error").toString();
                }
            }
            throw OrchestratorException.fromHttpError(
                    response.getStatusCodeValue(),
                    errorMessage,
                    "导出" + format.toUpperCase() + "格式报告");
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
                throw OrchestratorException.fromHttpError(
                        fileResponse.getStatusCodeValue(),
                        "下载失败",
                        "下载报告文件");
            }

            byte[] fileData = fileResponse.getBody();
            if (fileData == null) {
                throw new OrchestratorException("文件数据为空，请重新生成报告", OrchestratorErrorCode.FILE_EMPTY);
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
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("task_id", taskId);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

            ResponseEntity<Map> response = restTemplate.exchange(
                    orchestratorUrl + "/cleanup",
                    HttpMethod.POST,
                    entity,
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
        reportTask.setStatus("1"); // 1进行中
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
            task.setStatus("1"); // 1进行中
            task.setProgress(40);
            updateReportTask(task);
        }

        // 构建请求体
        Map<String, String> requestBody = new HashMap<>();
        requestBody.put("task_id", taskId);

        // 设置请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(requestBody, headers);

        // 调用编排器的step2接口
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step2",
                HttpMethod.POST,
                requestEntity,
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
            task.setStatus("1"); // 1进行中
            task.setProgress(60);
            updateReportTask(task);
        }

        // 构建请求体
        Map<String, String> requestBody = new HashMap<>();
        requestBody.put("task_id", taskId);

        // 设置请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(requestBody, headers);

        // 调用编排器的step3接口
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step3",
                HttpMethod.POST,
                requestEntity,
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
            task.setStatus("1"); // 1进行中
            task.setProgress(80);
            updateReportTask(task);
        }

        // 构建请求体
        Map<String, String> requestBody = new HashMap<>();
        requestBody.put("task_id", taskId);

        // 设置请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(requestBody, headers);

        // 调用编排器的step4接口
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step4",
                HttpMethod.POST,
                requestEntity,
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
            task.setStatus("2"); // 2已完成
            task.setProgress(100);
            updateReportTask(task);
        }

        // 构建请求体
        Map<String, String> requestBody = new HashMap<>();
        requestBody.put("task_id", taskId);

        // 设置请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(requestBody, headers);

        // 调用编排器的step5接口
        ResponseEntity<String> response = restTemplate.exchange(
                orchestratorUrl + "/step5",
                HttpMethod.POST,
                requestEntity,
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
                orchestratorUrl + "/task/" + taskId,
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
                orchestratorUrl + "/task/" + taskId + "/history/" + step,
                HttpMethod.GET,
                null,
                String.class);

        if (response.getStatusCode().is2xxSuccessful()) {
            return objectMapper.readValue(response.getBody(), Object.class);
        } else {
            throw new Exception("获取步骤历史失败: " + response.getBody());
        }
    }

    // ==================== 报告发布和归档功能实现 ====================

    /**
     * 发布报告
     */
    @Override
    public boolean publishReport(String taskId) throws Exception {
        ReportTask task = selectReportTaskByTaskId(taskId);
        if (task == null) {
            throw new Exception("报告任务不存在");
        }

        if (!"2".equals(task.getStatus())) {
            throw new Exception("只有已完成的报告才能发布");
        }

        if ("1".equals(task.getPublishStatus())) {
            throw new Exception("报告已经发布");
        }

        try {
            // 导出报告为PDF格式
            String downloadUrl = exportReport(taskId, "pdf", false);

            // 从下载URL获取文件流并上传到OSS
            String fileName = "report_" + taskId + ".pdf";
            String ossPath = "reports/" + DateUtils.dateTimeNow("yyyy/MM/dd") + "/" + fileName;

            // 通过RestTemplate下载文件并获取输入流
            ResponseEntity<byte[]> fileResponse = restTemplate.getForEntity(downloadUrl, byte[].class);
            if (!fileResponse.getStatusCode().is2xxSuccessful() || fileResponse.getBody() == null) {
                throw new Exception("下载报告文件失败");
            }

            // 将字节数组转换为输入流并上传到OSS
            try (java.io.ByteArrayInputStream inputStream = new java.io.ByteArrayInputStream(fileResponse.getBody())) {
                String ossUrl = ossService.uploadFile(inputStream, ossPath, "application/pdf", true);
                if (ossUrl == null) {
                    throw new Exception("上传文件到OSS失败");
                }
            }

            // 更新数据库
            ReportTask updateTask = new ReportTask();
            updateTask.setTaskId(taskId);
            updateTask.setPublishStatus("1"); // 已发布
            updateTask.setOssFilePath(ossPath);
            updateTask.setPublishTime(DateUtils.getNowDate());
            updateTask.setUpdateTime(DateUtils.getNowDate());

            return updateReportTask(updateTask) > 0;
        } catch (Exception e) {
            throw new Exception("发布报告失败: " + e.getMessage());
        }
    }

    /**
     * 归档报告
     */
    @Override
    public boolean archiveReport(String taskId) throws Exception {
        ReportTask task = selectReportTaskByTaskId(taskId);
        if (task == null) {
            throw new Exception("报告任务不存在");
        }

        if (!"1".equals(task.getPublishStatus())) {
            throw new Exception("只有已发布的报告才能归档");
        }

        if ("2".equals(task.getPublishStatus())) {
            throw new Exception("报告已经归档");
        }

        try {
            // 更新数据库
            ReportTask updateTask = new ReportTask();
            updateTask.setTaskId(taskId);
            updateTask.setPublishStatus("2"); // 已归档
            updateTask.setArchiveTime(DateUtils.getNowDate());
            updateTask.setUpdateTime(DateUtils.getNowDate());

            return updateReportTask(updateTask) > 0;
        } catch (Exception e) {
            throw new Exception("归档报告失败: " + e.getMessage());
        }
    }

    /**
     * 批量归档报告
     */
    @Override
    public int batchArchiveReports(String[] taskIds) throws Exception {
        int successCount = 0;
        for (String taskId : taskIds) {
            try {
                if (archiveReport(taskId)) {
                    successCount++;
                }
            } catch (Exception e) {
                // 记录错误但继续处理其他报告
                System.err.println("归档报告 " + taskId + " 失败: " + e.getMessage());
            }
        }
        return successCount;
    }

    /**
     * 取消发布报告
     */
    @Override
    public boolean unpublishReport(String taskId) throws Exception {
        ReportTask task = selectReportTaskByTaskId(taskId);
        if (task == null) {
            throw new Exception("报告任务不存在");
        }

        if (!"1".equals(task.getPublishStatus())) {
            throw new Exception("只有已发布的报告才能取消发布");
        }

        try {
            // 删除OSS文件
            if (task.getOssFilePath() != null && !task.getOssFilePath().isEmpty()) {
                ossService.deleteFile(task.getOssFilePath());
            }

            // 更新数据库
            ReportTask updateTask = new ReportTask();
            updateTask.setTaskId(taskId);
            updateTask.setPublishStatus("0"); // 草稿
            updateTask.setOssFilePath(null);
            updateTask.setPublishTime(null);
            updateTask.setUpdateTime(DateUtils.getNowDate());

            return updateReportTask(updateTask) > 0;
        } catch (Exception e) {
            throw new Exception("取消发布报告失败: " + e.getMessage());
        }
    }

    /**
     * 恢复归档报告
     */
    @Override
    public boolean restoreReport(String taskId) throws Exception {
        ReportTask task = selectReportTaskByTaskId(taskId);
        if (task == null) {
            throw new Exception("报告任务不存在");
        }

        if (!"2".equals(task.getPublishStatus())) {
            throw new Exception("只有已归档的报告才能恢复");
        }

        try {
            // 更新数据库
            ReportTask updateTask = new ReportTask();
            updateTask.setTaskId(taskId);
            updateTask.setPublishStatus("1"); // 已发布
            updateTask.setArchiveTime(null);
            updateTask.setUpdateTime(DateUtils.getNowDate());

            return updateReportTask(updateTask) > 0;
        } catch (Exception e) {
            throw new Exception("恢复报告失败: " + e.getMessage());
        }
    }
}