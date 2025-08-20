package com.ruoyi.system.validation;

import javax.validation.Constraint;
import javax.validation.Payload;
import java.lang.annotation.*;

/**
 * 任务ID验证注解
 * 验证任务ID格式是否正确
 * 
 * @author ruoyi
 */
@Target({ ElementType.FIELD, ElementType.PARAMETER })
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = TaskIdValidator.class)
@Documented
public @interface ValidTaskId {

    String message() default "无效的任务ID格式";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}