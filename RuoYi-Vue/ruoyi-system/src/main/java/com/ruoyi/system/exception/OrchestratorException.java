package com.ruoyi.system.exception;

import com.ruoyi.system.constants.OrchestratorErrorCode;

/**
 * 编排器异常
 * 用于封装编排器服务返回的错误信息
 * 
 * @author ruoyi
 */
public class OrchestratorException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    /**
     * HTTP状态码
     */
    private int httpStatus;

    /**
     * 编排器返回的原始错误信息
     */
    private String originalMessage;

    /**
     * 错误码
     */
    private Integer code;

    public OrchestratorException(String message) {
        super(message);
    }

    public OrchestratorException(String message, int httpStatus) {
        super(message);
        this.httpStatus = httpStatus;
    }

    public OrchestratorException(String message, int httpStatus, String originalMessage) {
        super(message);
        this.httpStatus = httpStatus;
        this.originalMessage = originalMessage;
    }

    public OrchestratorException(String message, Integer code) {
        super(message);
        this.code = code;
    }

    public OrchestratorException(String message, Integer code, int httpStatus, String originalMessage) {
        super(message);
        this.code = code;
        this.httpStatus = httpStatus;
        this.originalMessage = originalMessage;
    }

    public Integer getCode() {
        return code;
    }

    public void setCode(Integer code) {
        this.code = code;
    }

    public int getHttpStatus() {
        return httpStatus;
    }

    public void setHttpStatus(int httpStatus) {
        this.httpStatus = httpStatus;
    }

    public String getOriginalMessage() {
        return originalMessage;
    }

    public void setOriginalMessage(String originalMessage) {
        this.originalMessage = originalMessage;
    }

    /**
     * 根据HTTP状态码生成用户友好的错误信息
     */
    public static OrchestratorException fromHttpError(int status, String responseBody, String operation) {
        String userMessage;
        Integer errorCode = null;

        switch (status) {
            case 400:
                userMessage = "请求参数错误，请检查输入信息";
                errorCode = OrchestratorErrorCode.BAD_REQUEST;
                break;
            case 401:
                userMessage = "编排器服务认证失败";
                errorCode = OrchestratorErrorCode.UNAUTHORIZED;
                break;
            case 403:
                userMessage = "编排器服务访问被拒绝";
                errorCode = OrchestratorErrorCode.FORBIDDEN;
                break;
            case 404:
                userMessage = "编排器服务接口不存在";
                errorCode = OrchestratorErrorCode.NOT_FOUND;
                break;
            case 422:
                userMessage = "数据验证失败，请检查输入格式";
                errorCode = OrchestratorErrorCode.VALIDATION_ERROR;
                break;
            case 429:
                userMessage = "请求过于频繁，请稍后重试";
                errorCode = OrchestratorErrorCode.TOO_MANY_REQUESTS;
                break;
            case 500:
                userMessage = "编排器服务内部错误";
                errorCode = OrchestratorErrorCode.INTERNAL_ERROR;
                break;
            case 502:
                userMessage = "编排器服务网关错误";
                errorCode = OrchestratorErrorCode.BAD_GATEWAY;
                break;
            case 503:
                userMessage = "编排器服务暂时不可用";
                errorCode = OrchestratorErrorCode.SERVICE_UNAVAILABLE;
                break;
            case 504:
                userMessage = "编排器服务响应超时";
                errorCode = OrchestratorErrorCode.GATEWAY_TIMEOUT;
                break;
            default:
                userMessage = "编排器服务异常 (HTTP " + status + ")";
                errorCode = OrchestratorErrorCode.UNKNOWN_ERROR;
                break;
        }

        if (operation != null && !operation.isEmpty()) {
            userMessage = operation + "失败：" + userMessage;
        }

        return new OrchestratorException(userMessage, errorCode, status, responseBody);
    }
}