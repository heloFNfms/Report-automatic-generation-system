package com.ruoyi.system.constants;

/**
 * 编排器错误码常量
 * 
 * @author ruoyi
 */
public class OrchestratorErrorCode {

    // 4xx 客户端错误
    public static final int BAD_REQUEST = 40001;
    public static final int UNAUTHORIZED = 40101;
    public static final int FORBIDDEN = 40301;
    public static final int NOT_FOUND = 40401;
    public static final int VALIDATION_ERROR = 42201;
    public static final int TOO_MANY_REQUESTS = 42901;

    // 5xx 服务器错误
    public static final int INTERNAL_ERROR = 50001;
    public static final int FILE_EMPTY = 50002;
    public static final int BAD_GATEWAY = 50201;
    public static final int SERVICE_UNAVAILABLE = 50301;
    public static final int GATEWAY_TIMEOUT = 50401;
    public static final int UNKNOWN_ERROR = 50000;

    // 业务错误码
    public static final int STEP_EXECUTION_FAILED = 60001;
    public static final int STEP_RERUN_FAILED = 60002;
    public static final int STEP_ROLLBACK_FAILED = 60003;
    public static final int EXPORT_FAILED = 60004;
    public static final int DOWNLOAD_FAILED = 60005;

    private OrchestratorErrorCode() {
        // 工具类，禁止实例化
    }
}