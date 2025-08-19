package com.ruoyi.system.service.impl;

import java.util.Date;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.system.mapper.ReportStepHistoryMapper;
import com.ruoyi.system.domain.ReportStepHistory;
import com.ruoyi.system.service.IReportStepHistoryService;

/**
 * 报告步骤历史Service业务层处理
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
@Service
public class ReportStepHistoryServiceImpl implements IReportStepHistoryService {
    @Autowired
    private ReportStepHistoryMapper reportStepHistoryMapper;

    /**
     * 查询报告步骤历史
     * 
     * @param id 报告步骤历史主键
     * @return 报告步骤历史
     */
    @Override
    public ReportStepHistory selectReportStepHistoryById(Long id) {
        return reportStepHistoryMapper.selectReportStepHistoryById(id);
    }

    /**
     * 查询报告步骤历史列表
     * 
     * @param reportStepHistory 报告步骤历史
     * @return 报告步骤历史
     */
    @Override
    public List<ReportStepHistory> selectReportStepHistoryList(ReportStepHistory reportStepHistory) {
        return reportStepHistoryMapper.selectReportStepHistoryList(reportStepHistory);
    }

    /**
     * 根据任务ID查询步骤历史
     * 
     * @param taskId 任务ID
     * @return 报告步骤历史集合
     */
    @Override
    public List<ReportStepHistory> selectReportStepHistoryByTaskId(String taskId) {
        return reportStepHistoryMapper.selectReportStepHistoryByTaskId(taskId);
    }

    /**
     * 根据任务ID和步骤查询历史
     * 
     * @param taskId 任务ID
     * @param step   步骤名称
     * @return 报告步骤历史集合
     */
    @Override
    public List<ReportStepHistory> selectReportStepHistoryByTaskIdAndStep(String taskId, String step) {
        return reportStepHistoryMapper.selectReportStepHistoryByTaskIdAndStep(taskId, step);
    }

    /**
     * 根据任务ID、步骤和版本查询历史
     * 
     * @param taskId  任务ID
     * @param step    步骤名称
     * @param version 版本号
     * @return 报告步骤历史
     */
    @Override
    public ReportStepHistory selectReportStepHistoryByTaskIdAndStepAndVersion(String taskId, String step,
            Integer version) {
        return reportStepHistoryMapper.selectReportStepHistoryByTaskIdAndStepAndVersion(taskId, step, version);
    }

    /**
     * 新增报告步骤历史
     * 
     * @param reportStepHistory 报告步骤历史
     * @return 结果
     */
    @Override
    public int insertReportStepHistory(ReportStepHistory reportStepHistory) {
        reportStepHistory.setCreateTime(new Date());
        return reportStepHistoryMapper.insertReportStepHistory(reportStepHistory);
    }

    /**
     * 修改报告步骤历史
     * 
     * @param reportStepHistory 报告步骤历史
     * @return 结果
     */
    @Override
    public int updateReportStepHistory(ReportStepHistory reportStepHistory) {
        return reportStepHistoryMapper.updateReportStepHistory(reportStepHistory);
    }

    /**
     * 批量删除报告步骤历史
     * 
     * @param ids 需要删除的报告步骤历史主键
     * @return 结果
     */
    @Override
    public int deleteReportStepHistoryByIds(Long[] ids) {
        return reportStepHistoryMapper.deleteReportStepHistoryByIds(ids);
    }

    /**
     * 删除报告步骤历史信息
     * 
     * @param id 报告步骤历史主键
     * @return 结果
     */
    @Override
    public int deleteReportStepHistoryById(Long id) {
        return reportStepHistoryMapper.deleteReportStepHistoryById(id);
    }

    /**
     * 根据任务ID删除步骤历史
     * 
     * @param taskId 任务ID
     * @return 结果
     */
    @Override
    public int deleteReportStepHistoryByTaskId(String taskId) {
        return reportStepHistoryMapper.deleteReportStepHistoryByTaskId(taskId);
    }

    /**
     * 保存步骤执行历史
     * 
     * @param taskId        任务ID
     * @param step          步骤名称
     * @param outputJson    输出JSON
     * @param executionTime 执行时间
     * @param status        执行状态
     * @param errorMessage  错误信息
     * @return 结果
     */
    @Override
    public int saveStepHistory(String taskId, String step, String outputJson, Integer executionTime, String status,
            String errorMessage) {
        // 获取当前步骤的最大版本号
        List<ReportStepHistory> histories = reportStepHistoryMapper.selectReportStepHistoryByTaskIdAndStep(taskId,
                step);
        Integer nextVersion = 1;
        if (histories != null && !histories.isEmpty()) {
            nextVersion = histories.get(0).getVersion() + 1;
        }

        ReportStepHistory history = new ReportStepHistory();
        history.setTaskId(taskId);
        history.setStep(step);
        history.setVersion(nextVersion);
        history.setOutputJson(outputJson);
        history.setExecutionTime(executionTime);
        history.setStatus(status);
        history.setErrorMessage(errorMessage);

        return insertReportStepHistory(history);
    }

    /**
     * 回滚到指定版本
     * 
     * @param taskId  任务ID
     * @param step    步骤名称
     * @param version 版本号
     * @return 历史记录
     */
    @Override
    public ReportStepHistory rollbackToVersion(String taskId, String step, Integer version) {
        return reportStepHistoryMapper.selectReportStepHistoryByTaskIdAndStepAndVersion(taskId, step, version);
    }
}