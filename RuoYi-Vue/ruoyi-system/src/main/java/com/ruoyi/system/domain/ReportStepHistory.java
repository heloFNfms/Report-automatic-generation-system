package com.ruoyi.system.domain;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseEntity;

/**
 * 报告步骤历史对象 report_step_history
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
public class ReportStepHistory extends BaseEntity {
    private static final long serialVersionUID = 1L;

    /** 历史记录ID */
    private Long id;

    /** 任务ID */
    @Excel(name = "任务ID")
    private String taskId;

    /** 步骤名称（step1-step5） */
    @Excel(name = "步骤名称")
    private String step;

    /** 版本号 */
    @Excel(name = "版本号")
    private Integer version;

    /** 步骤输出（JSON格式） */
    private String outputJson;

    /** 执行时间（秒） */
    @Excel(name = "执行时间")
    private Integer executionTime;

    /** 执行状态（0失败 1成功） */
    @Excel(name = "执行状态", readConverterExp = "0=失败,1=成功")
    private String status;

    /** 错误信息 */
    private String errorMessage;

    public void setId(Long id) {
        this.id = id;
    }

    public Long getId() {
        return id;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public String getTaskId() {
        return taskId;
    }

    public void setStep(String step) {
        this.step = step;
    }

    public String getStep() {
        return step;
    }

    public void setVersion(Integer version) {
        this.version = version;
    }

    public Integer getVersion() {
        return version;
    }

    public void setOutputJson(String outputJson) {
        this.outputJson = outputJson;
    }

    public String getOutputJson() {
        return outputJson;
    }

    public void setExecutionTime(Integer executionTime) {
        this.executionTime = executionTime;
    }

    public Integer getExecutionTime() {
        return executionTime;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getStatus() {
        return status;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    @Override
    public String toString() {
        return new ToStringBuilder(this, ToStringStyle.MULTI_LINE_STYLE)
                .append("id", getId())
                .append("taskId", getTaskId())
                .append("step", getStep())
                .append("version", getVersion())
                .append("outputJson", getOutputJson())
                .append("executionTime", getExecutionTime())
                .append("status", getStatus())
                .append("errorMessage", getErrorMessage())
                .append("createTime", getCreateTime())
                .toString();
    }
}