package com.ruoyi.system.validation;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;
import java.util.regex.Pattern;

/**
 * 任务ID验证器
 * 
 * @author ruoyi
 */
public class TaskIdValidator implements ConstraintValidator<ValidTaskId, String> {

    // UUID格式的正则表达式
    private static final Pattern UUID_PATTERN = Pattern.compile(
            "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$");

    @Override
    public void initialize(ValidTaskId constraintAnnotation) {
        // 初始化方法
    }

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null || value.trim().isEmpty()) {
            return false;
        }

        // 验证UUID格式
        return UUID_PATTERN.matcher(value.trim()).matches();
    }
}