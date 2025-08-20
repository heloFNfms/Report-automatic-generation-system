package com.ruoyi.system.validation;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/**
 * 步骤验证器
 * 
 * @author ruoyi
 */
public class StepValidator implements ConstraintValidator<ValidStep, String> {

    private static final Set<String> VALID_STEPS = new HashSet<>(Arrays.asList(
            "step1", "step2", "step3", "step4", "step5"));

    @Override
    public void initialize(ValidStep constraintAnnotation) {
        // 初始化方法，可以在这里获取注解参数
    }

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null) {
            return false;
        }
        return VALID_STEPS.contains(value.toLowerCase());
    }
}