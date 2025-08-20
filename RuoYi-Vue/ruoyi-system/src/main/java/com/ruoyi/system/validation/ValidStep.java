package com.ruoyi.system.validation;

import javax.validation.Constraint;
import javax.validation.Payload;
import java.lang.annotation.*;

/**
 * 步骤验证注解
 * 验证步骤参数是否为有效的步骤名称
 * 
 * @author ruoyi
 */
@Target({ ElementType.FIELD, ElementType.PARAMETER })
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = StepValidator.class)
@Documented
public @interface ValidStep {

    String message() default "无效的步骤名称，支持的步骤：step1, step2, step3, step4, step5";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}