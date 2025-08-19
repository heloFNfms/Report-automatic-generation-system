package com.ruoyi.web.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.client.SimpleClientHttpRequestFactory;

/**
 * 报告生成配置类
 * 
 * @author ruoyi
 */
@Configuration
@ConfigurationProperties(prefix = "report.orchestrator")
public class ReportConfig {
    
    /** 编排器服务地址 */
    private String url = "http://localhost:9000";
    
    /** 连接超时时间（毫秒） */
    private int connectTimeout = 5000;
    
    /** 读取超时时间（毫秒） */
    private int readTimeout = 30000;
    
    /**
     * 创建用于调用报告编排器的RestTemplate
     */
    @Bean("reportRestTemplate")
    public RestTemplate reportRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(connectTimeout);
        factory.setReadTimeout(readTimeout);
        
        RestTemplate restTemplate = new RestTemplate(factory);
        return restTemplate;
    }
    
    public String getUrl() {
        return url;
    }
    
    public void setUrl(String url) {
        this.url = url;
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
}