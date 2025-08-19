package com.ruoyi.system.service;

import java.util.List;
import java.util.Map;
import com.ruoyi.system.domain.ReportTask;

/**
 * 报告生成Service接口
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
public interface IReportService {
    /**
     * 查询报告任务
     * 
     * @param taskId 报告任务主键
     * @return 报告任务
     */
    public ReportTask selectReportTaskByTaskId(String taskId);

    /**
     * 查询报告任务列表
     * 
     * @param reportTask 报告任务
     * @return 报告任务集合
     */
    public List<ReportTask> selectReportTaskList(ReportTask reportTask);

    /**
     * 新增报告任务
     * 
     * @param reportTask 报告任务
     * @return 结果
     */
    public int insertReportTask(ReportTask reportTask);

    /**
     * 修改报告任务
     * 
     * @param reportTask 报告任务
     * @return 结果
     */
    public int updateReportTask(ReportTask reportTask);

    /**
     * 批量删除报告任务
     * 
     * @param taskIds 需要删除的报告任务主键集合
     * @return 结果
     */
    public int deleteReportTaskByTaskIds(String[] taskIds);

    /**
     * 删除报告任务信息
     * 
     * @param taskId 报告任务主键
     * @return 结果
     */
    public int deleteReportTaskByTaskId(String taskId);

    /**
     * 启动报告生成
     * 
     * @param reportTask 报告任务
     * @return 任务ID
     */
    public String startReportGeneration(ReportTask reportTask) throws Exception;

    /**
     * 获取报告生成状态
     * 
     * @param taskId 任务ID
     * @return 状态信息
     */
    public Map<String, Object> getReportStatus(String taskId) throws Exception;

    /**
     * 获取报告内容
     * 
     * @param taskId 任务ID
     * @return 报告内容
     */
    public Map<String, Object> getReportContent(String taskId) throws Exception;

    /**
     * 重新执行报告步骤
     * 
     * @param taskId 任务ID
     * @param step   步骤名称
     */
    public void rerunReportStep(String taskId, String step) throws Exception;

    /**
     * 回滚报告到指定版本
     * 
     * @param taskId  任务ID
     * @param step    步骤名称
     * @param version 版本号
     */
    public void rollbackReportStep(String taskId, String step, Integer version) throws Exception;

    /**
     * 导出报告
     * 
     * @param taskId      任务ID
     * @param format      导出格式 (pdf, docx)
     * @param uploadToOss 是否上传到对象存储
     * @return 下载URL或文件路径
     */
    public String exportReport(String taskId, String format, boolean uploadToOss) throws Exception;

    /**
     * 下载报告文件
     * 
     * @param taskId   任务ID
     * @param filename 文件名
     * @param response HTTP响应
     */
    public void downloadReport(String taskId, String filename, javax.servlet.http.HttpServletResponse response)
            throws Exception;

    /**
     * 清理临时文件
     * 
     * @param taskId 任务ID
     * @return 是否成功
     */
    public boolean cleanupFiles(String taskId) throws Exception;

    // ==================== 分步骤执行方法 ====================

    /**
     * 执行步骤1：保存主题到数据库
     * 
     * @param reportTask 报告任务
     * @return 任务ID
     */
    public String executeStep1(ReportTask reportTask) throws Exception;

    /**
     * 执行步骤2：生成研究大纲
     * 
     * @param taskId 任务ID
     * @return 大纲结果
     */
    public Object executeStep2(String taskId) throws Exception;

    /**
     * 执行步骤3：检索并生成章节内容
     * 
     * @param taskId 任务ID
     * @return 章节内容结果
     */
    public Object executeStep3(String taskId) throws Exception;

    /**
     * 执行步骤4：组装润色报告
     * 
     * @param taskId 任务ID
     * @return 报告结果
     */
    public Object executeStep4(String taskId) throws Exception;

    /**
     * 执行步骤5：生成摘要和关键词
     * 
     * @param taskId 任务ID
     * @return 最终结果
     */
    public Object executeStep5(String taskId) throws Exception;

    /**
     * 获取指定步骤的结果
     * 
     * @param taskId 任务ID
     * @param step   步骤名称
     * @return 步骤结果
     */
    public Object getStepResult(String taskId, String step) throws Exception;

    /**
     * 获取指定步骤的历史版本
     * 
     * @param taskId 任务ID
     * @param step   步骤名称
     * @return 历史版本列表
     */
    public Object getStepHistory(String taskId, String step) throws Exception;
}