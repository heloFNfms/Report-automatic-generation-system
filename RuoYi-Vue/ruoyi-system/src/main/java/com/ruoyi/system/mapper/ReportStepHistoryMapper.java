package com.ruoyi.system.mapper;

import java.util.List;
import com.ruoyi.system.domain.ReportStepHistory;

/**
 * 报告步骤历史Mapper接口
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
public interface ReportStepHistoryMapper {
    /**
     * 查询报告步骤历史
     * 
     * @param id 报告步骤历史主键
     * @return 报告步骤历史
     */
    public ReportStepHistory selectReportStepHistoryById(Long id);

    /**
     * 查询报告步骤历史列表
     * 
     * @param reportStepHistory 报告步骤历史
     * @return 报告步骤历史集合
     */
    public List<ReportStepHistory> selectReportStepHistoryList(ReportStepHistory reportStepHistory);

    /**
     * 根据任务ID查询步骤历史
     * 
     * @param taskId 任务ID
     * @return 报告步骤历史集合
     */
    public List<ReportStepHistory> selectReportStepHistoryByTaskId(String taskId);

    /**
     * 根据任务ID和步骤查询历史
     * 
     * @param taskId 任务ID
     * @param step   步骤名称
     * @return 报告步骤历史集合
     */
    public List<ReportStepHistory> selectReportStepHistoryByTaskIdAndStep(String taskId, String step);

    /**
     * 根据任务ID、步骤和版本查询历史
     * 
     * @param taskId  任务ID
     * @param step    步骤名称
     * @param version 版本号
     * @return 报告步骤历史
     */
    public ReportStepHistory selectReportStepHistoryByTaskIdAndStepAndVersion(String taskId, String step,
            Integer version);

    /**
     * 新增报告步骤历史
     * 
     * @param reportStepHistory 报告步骤历史
     * @return 结果
     */
    public int insertReportStepHistory(ReportStepHistory reportStepHistory);

    /**
     * 修改报告步骤历史
     * 
     * @param reportStepHistory 报告步骤历史
     * @return 结果
     */
    public int updateReportStepHistory(ReportStepHistory reportStepHistory);

    /**
     * 删除报告步骤历史
     * 
     * @param id 报告步骤历史主键
     * @return 结果
     */
    public int deleteReportStepHistoryById(Long id);

    /**
     * 批量删除报告步骤历史
     * 
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
    public int deleteReportStepHistoryByIds(Long[] ids);

    /**
     * 根据任务ID删除步骤历史
     * 
     * @param taskId 任务ID
     * @return 结果
     */
    public int deleteReportStepHistoryByTaskId(String taskId);
}