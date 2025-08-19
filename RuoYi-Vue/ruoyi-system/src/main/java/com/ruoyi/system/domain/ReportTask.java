package com.ruoyi.system.domain;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseEntity;

/**
 * 报告任务对象 report_task
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
public class ReportTask extends BaseEntity {
    private static final long serialVersionUID = 1L;

    /** 任务ID */
    private String taskId;

    /** 编排器任务ID */
    private String orchestratorTaskId;

    /** 任务标题 */
    @Excel(name = "任务标题")
    private String title;

    /** 公司名称 */
    @Excel(name = "公司名称")
    private String companyName;

    /** 任务描述 */
    @Excel(name = "任务描述")
    private String description;

    /** 报告主题 */
    @Excel(name = "报告主题")
    private String topic;

    /** 任务状态（0待处理 1进行中 2已完成 3失败） */
    @Excel(name = "任务状态", readConverterExp = "0=待处理,1=进行中,2=已完成,3=失败")
    private String status;

    /** 当前步骤（step1-step5） */
    @Excel(name = "当前步骤")
    private String currentStep;

    /** 进度百分比 */
    @Excel(name = "进度百分比")
    private Integer progress;

    /** 报告内容（JSON格式） */
    private String content;

    /** 错误信息 */
    private String errorMessage;

    /** 开始时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "开始时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date startTime;

    /** 完成时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "完成时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date endTime;

    /** 创建者ID */
    private Long userId;

    /** 创建者名称 */
    @Excel(name = "创建者")
    private String userName;

    /** 配置参数（JSON格式） */
    private String configParams;

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public String getTaskId() {
        return taskId;
    }

    public void setOrchestratorTaskId(String orchestratorTaskId) {
        this.orchestratorTaskId = orchestratorTaskId;
    }

    public String getOrchestratorTaskId() {
        return orchestratorTaskId;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getTitle() {
        return title;
    }

    public void setCompanyName(String companyName) {
        this.companyName = companyName;
    }

    public String getCompanyName() {
        return companyName;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }

    public void setTopic(String topic) {
        this.topic = topic;
    }

    public String getTopic() {
        return topic;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getStatus() {
        return status;
    }

    public void setCurrentStep(String currentStep) {
        this.currentStep = currentStep;
    }

    public String getCurrentStep() {
        return currentStep;
    }

    public void setProgress(Integer progress) {
        this.progress = progress;
    }

    public Integer getProgress() {
        return progress;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getContent() {
        return content;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setStartTime(Date startTime) {
        this.startTime = startTime;
    }

    public Date getStartTime() {
        return startTime;
    }

    public void setEndTime(Date endTime) {
        this.endTime = endTime;
    }

    public Date getEndTime() {
        return endTime;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserName(String userName) {
        this.userName = userName;
    }

    public String getUserName() {
        return userName;
    }

    public void setConfigParams(String configParams) {
        this.configParams = configParams;
    }

    public String getConfigParams() {
        return configParams;
    }

    @Override
    public String toString() {
        return new ToStringBuilder(this, ToStringStyle.MULTI_LINE_STYLE)
                .append("taskId", getTaskId())
                .append("orchestratorTaskId", getOrchestratorTaskId())
                .append("title", getTitle())
                .append("companyName", getCompanyName())
                .append("description", getDescription())
                .append("topic", getTopic())
                .append("status", getStatus())
                .append("currentStep", getCurrentStep())
                .append("progress", getProgress())
                .append("content", getContent())
                .append("errorMessage", getErrorMessage())
                .append("startTime", getStartTime())
                .append("endTime", getEndTime())
                .append("userId", getUserId())
                .append("userName", getUserName())
                .append("configParams", getConfigParams())
                .append("createTime", getCreateTime())
                .append("updateTime", getUpdateTime())
                .toString();
    }
}