package com.ruoyi.system.mapper;

import java.util.List;
import com.ruoyi.system.domain.ReportTask;

/**
 * 报告任务Mapper接口
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
public interface ReportTaskMapper 
{
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
     * 删除报告任务
     * 
     * @param taskId 报告任务主键
     * @return 结果
     */
    public int deleteReportTaskByTaskId(String taskId);

    /**
     * 批量删除报告任务
     * 
     * @param taskIds 需要删除的数据主键集合
     * @return 结果
     */
    public int deleteReportTaskByTaskIds(String[] taskIds);
}