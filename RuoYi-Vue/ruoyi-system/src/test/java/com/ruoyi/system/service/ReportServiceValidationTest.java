package com.ruoyi.system.service;

import com.ruoyi.system.domain.ReportTask;
import com.ruoyi.system.exception.OrchestratorException;
import com.ruoyi.system.constants.OrchestratorErrorCode;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import javax.validation.ConstraintViolation;
import javax.validation.Validation;
import javax.validation.Validator;
import javax.validation.ValidatorFactory;
import java.util.Set;

/**
 * 报告服务验证测试
 * 
 * @author ruoyi
 */
public class ReportServiceValidationTest {

    private final ValidatorFactory factory = Validation.buildDefaultValidatorFactory();
    private final Validator validator = factory.getValidator();

    @Test
    public void testReportTaskValidation() {
        // 测试空标题
        ReportTask task = new ReportTask();
        task.setTitle("");
        task.setCompanyName("测试公司");
        task.setTopic("测试主题");

        Set<ConstraintViolation<ReportTask>> violations = validator.validate(task);
        assertFalse(violations.isEmpty());

        boolean hasBlankTitleError = violations.stream()
                .anyMatch(v -> v.getMessage().contains("任务标题不能为空"));
        assertTrue(hasBlankTitleError);
    }

    @Test
    public void testReportTaskTitleTooLong() {
        ReportTask task = new ReportTask();
        task.setTitle("a".repeat(201)); // 超过200字符
        task.setCompanyName("测试公司");
        task.setTopic("测试主题");

        Set<ConstraintViolation<ReportTask>> violations = validator.validate(task);
        assertFalse(violations.isEmpty());

        boolean hasTitleLengthError = violations.stream()
                .anyMatch(v -> v.getMessage().contains("任务标题长度不能超过200个字符"));
        assertTrue(hasTitleLengthError);
    }

    @Test
    public void testValidReportTask() {
        ReportTask task = new ReportTask();
        task.setTitle("有效的任务标题");
        task.setCompanyName("测试公司");
        task.setTopic("测试主题");
        task.setDescription("这是一个有效的任务描述");

        Set<ConstraintViolation<ReportTask>> violations = validator.validate(task);
        assertTrue(violations.isEmpty());
    }

    @Test
    public void testOrchestratorExceptionCreation() {
        // 测试400错误
        OrchestratorException ex400 = OrchestratorException.fromHttpError(
                400, "Bad Request", "执行步骤1");
        assertEquals(OrchestratorErrorCode.BAD_REQUEST, ex400.getCode());
        assertTrue(ex400.getMessage().contains("执行步骤1失败"));
        assertTrue(ex400.getMessage().contains("请求参数错误"));

        // 测试500错误
        OrchestratorException ex500 = OrchestratorException.fromHttpError(
                500, "Internal Server Error", "导出PDF格式报告");
        assertEquals(OrchestratorErrorCode.INTERNAL_ERROR, ex500.getCode());
        assertTrue(ex500.getMessage().contains("导出PDF格式报告失败"));
        assertTrue(ex500.getMessage().contains("编排器服务内部错误"));

        // 测试422错误
        OrchestratorException ex422 = OrchestratorException.fromHttpError(
                422, "Validation Error", "重新执行步骤2");
        assertEquals(OrchestratorErrorCode.VALIDATION_ERROR, ex422.getCode());
        assertTrue(ex422.getMessage().contains("重新执行步骤2失败"));
        assertTrue(ex422.getMessage().contains("数据验证失败"));
    }

    @Test
    public void testOrchestratorExceptionWithoutOperation() {
        OrchestratorException ex = OrchestratorException.fromHttpError(
                404, "Not Found", null);
        assertEquals(OrchestratorErrorCode.NOT_FOUND, ex.getCode());
        assertEquals("编排器服务接口不存在", ex.getMessage());
    }
}