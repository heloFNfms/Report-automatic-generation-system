package com.ruoyi.system.domain;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseEntity;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;
import javax.validation.constraints.Pattern;

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
    @NotBlank(message = "任务标题不能为空")
    @Size(max = 200, message = "任务标题长度不能超过200个字符")
    private String title;

    /** 公司名称 */
    @Excel(name = "公司名称")
    @NotBlank(message = "公司名称不能为空")
    @Size(max = 100, message = "公司名称长度不能超过100个字符")
    private String companyName;

    /** 任务描述 */
    @Excel(name = "任务描述")
    @Size(max = 1000, message = "任务描述长度不能超过1000个字符")
    private String description;

    /** 报告主题 */
    @Excel(name = "报告主题")
    @NotBlank(message = "报告主题不能为空")
    @Size(max = 500, message = "报告主题长度不能超过500个字符")
    private String topic;

    /** 任务状态（0待处理 1进行中 2已完成 3失败） */
    @Excel(name = "任务状态", readConverterExp = "0=待处理,1=进行中,2=已完成,3=失败")
    private String status;

    /** 发布状态（0草稿 1已发布 2已归档） */
    @Excel(name = "发布状态", readConverterExp = "0=草稿,1=已发布,2=已归档")
    private String publishStatus;

    /** OSS文件路径 */
    @Excel(name = "OSS文件路径")
    private String ossFilePath;

    /** 发布时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "发布时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date publishTime;

    /** 归档时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "归档时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date archiveTime;

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

    public void setPublishStatus(String publishStatus) {
        this.publishStatus = publishStatus;
    }

    public String getPublishStatus() {
        return publishStatus;
    }

    public void setOssFilePath(String ossFilePath) {
        this.ossFilePath = ossFilePath;
    }

    public String getOssFilePath() {
        return ossFilePath;
    }

    public void setPublishTime(Date publishTime) {
        this.publishTime = publishTime;
    }

    public Date getPublishTime() {
        return publishTime;
    }

    public void setArchiveTime(Date archiveTime) {
        this.archiveTime = archiveTime;
    }

    public Date getArchiveTime() {
        return archiveTime;
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
                .append("publishStatus", getPublishStatus())
                .append("ossFilePath", getOssFilePath())
                .append("publishTime", getPublishTime())
                .append("archiveTime", getArchiveTime())
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