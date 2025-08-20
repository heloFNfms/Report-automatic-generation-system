package com.ruoyi.system.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * OSS云存储配置属性
 *
 * @author ruoyi
 */
@Component
@ConfigurationProperties(prefix = "report.oss")
public class OssProperties {
    /** 是否启用OSS上传 */
    private boolean enabled = true;

    /** OSS服务提供商 */
    private String provider = "aliyun";

    /** 访问密钥ID */
    private String accessKeyId;

    /** 访问密钥Secret */
    private String accessKeySecret;

    /** 存储桶名称 */
    private String bucketName;

    /** 服务端点 */
    private String endpoint;

    /** 文件访问域名 */
    private String domain;

    /** 文件存储路径前缀 */
    private String pathPrefix = "reports/";

    /** 连接超时时间（毫秒） */
    private int connectTimeout = 10000;

    /** 读取超时时间（毫秒） */
    private int readTimeout = 30000;

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public String getProvider() {
        return provider;
    }

    public void setProvider(String provider) {
        this.provider = provider;
    }

    public String getAccessKeyId() {
        return accessKeyId;
    }

    public void setAccessKeyId(String accessKeyId) {
        this.accessKeyId = accessKeyId;
    }

    public String getAccessKeySecret() {
        return accessKeySecret;
    }

    public void setAccessKeySecret(String accessKeySecret) {
        this.accessKeySecret = accessKeySecret;
    }

    public String getBucketName() {
        return bucketName;
    }

    public void setBucketName(String bucketName) {
        this.bucketName = bucketName;
    }

    public String getEndpoint() {
        return endpoint;
    }

    public void setEndpoint(String endpoint) {
        this.endpoint = endpoint;
    }

    public String getDomain() {
        return domain;
    }

    public void setDomain(String domain) {
        this.domain = domain;
    }

    public String getPathPrefix() {
        return pathPrefix;
    }

    public void setPathPrefix(String pathPrefix) {
        this.pathPrefix = pathPrefix;
    }

    public int getConnectTimeout() {
        return connectTimeout;
    }

    public void setConnectTimeout(int connectTimeout) {
        this.connectTimeout = connectTimeout;
    }

    public int getReadTimeout() {
        return readTimeout;
    }

    public void setReadTimeout(int readTimeout) {
        this.readTimeout = readTimeout;
    }

    @Override
    public String toString() {
        return "OssProperties{" +
                "enabled=" + enabled +
                ", provider='" + provider + '\'' +
                ", accessKeyId='" + accessKeyId + '\'' +
                ", bucketName='" + bucketName + '\'' +
                ", endpoint='" + endpoint + '\'' +
                ", domain='" + domain + '\'' +
                ", pathPrefix='" + pathPrefix + '\'' +
                ", connectTimeout=" + connectTimeout +
                ", readTimeout=" + readTimeout +
                '}';
    }
}