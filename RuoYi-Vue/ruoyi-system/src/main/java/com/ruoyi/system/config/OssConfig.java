package com.ruoyi.system.config;

import com.ruoyi.system.config.OssProperties;
import com.ruoyi.system.service.IOssService;
import com.ruoyi.system.service.impl.OssServiceImpl;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * OSS配置类
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
@Configuration
@EnableConfigurationProperties(OssProperties.class)
@ConditionalOnProperty(prefix = "report.oss", name = "enabled", havingValue = "true")
public class OssConfig {

    /**
     * OSS服务Bean
     */
    @Bean
    public IOssService ossService(OssProperties ossProperties) {
        return new OssServiceImpl(ossProperties);
    }
}