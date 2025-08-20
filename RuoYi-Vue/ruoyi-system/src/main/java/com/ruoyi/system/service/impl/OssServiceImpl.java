package com.ruoyi.system.service.impl;

import com.aliyun.oss.OSS;
import com.aliyun.oss.OSSClientBuilder;
import com.aliyun.oss.model.ObjectMetadata;
import com.aliyun.oss.model.PutObjectRequest;
import com.ruoyi.system.config.OssProperties;
import com.ruoyi.system.service.IOssService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.io.InputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.UUID;

/**
 * OSS文件上传服务实现类
 *
 * @author ruoyi
 */
@Service
public class OssServiceImpl implements IOssService {
    private static final Logger log = LoggerFactory.getLogger(OssServiceImpl.class);

    private final OssProperties ossProperties;
    private OSS ossClient;

    public OssServiceImpl(OssProperties ossProperties) {
        this.ossProperties = ossProperties;
    }

    @PostConstruct
    public void init() {
        if (ossProperties.isEnabled()) {
            try {
                // 创建OSS客户端
                ossClient = new OSSClientBuilder().build(
                        ossProperties.getEndpoint(),
                        ossProperties.getAccessKeyId(),
                        ossProperties.getAccessKeySecret());
                log.info("OSS客户端初始化成功，endpoint: {}, bucket: {}",
                        ossProperties.getEndpoint(), ossProperties.getBucketName());
            } catch (Exception e) {
                log.error("OSS客户端初始化失败", e);
            }
        } else {
            log.info("OSS服务未启用");
        }
    }

    @PreDestroy
    public void destroy() {
        if (ossClient != null) {
            try {
                ossClient.shutdown();
                log.info("OSS客户端已关闭");
            } catch (Exception e) {
                log.error("关闭OSS客户端失败", e);
            }
        }
    }

    @Override
    public String uploadFile(InputStream inputStream, String fileName, String contentType) {
        if (!ossProperties.isEnabled() || ossClient == null) {
            log.warn("OSS服务未启用或客户端未初始化");
            return null;
        }

        try {
            // 生成文件路径：pathPrefix + 日期 + UUID + 原文件名
            String datePath = new SimpleDateFormat("yyyy/MM/dd").format(new Date());
            String uuid = UUID.randomUUID().toString().replace("-", "");
            String fileExtension = "";
            if (fileName.contains(".")) {
                fileExtension = fileName.substring(fileName.lastIndexOf("."));
            }
            String objectKey = ossProperties.getPathPrefix() + datePath + "/" + uuid + fileExtension;

            return uploadFile(inputStream, objectKey, contentType, true);
        } catch (Exception e) {
            log.error("上传文件到OSS失败: {}", fileName, e);
            return null;
        }
    }

    @Override
    public String uploadFile(InputStream inputStream, String filePath, String contentType, boolean useFullPath) {
        if (!ossProperties.isEnabled() || ossClient == null) {
            log.warn("OSS服务未启用或客户端未初始化");
            return null;
        }

        try {
            String objectKey = useFullPath ? filePath : ossProperties.getPathPrefix() + filePath;

            // 设置文件元数据
            ObjectMetadata metadata = new ObjectMetadata();
            if (contentType != null && !contentType.isEmpty()) {
                metadata.setContentType(contentType);
            }
            metadata.setContentLength(inputStream.available());

            // 创建上传请求
            PutObjectRequest putObjectRequest = new PutObjectRequest(
                    ossProperties.getBucketName(), objectKey, inputStream, metadata);

            // 上传文件
            ossClient.putObject(putObjectRequest);

            // 返回文件访问URL
            String fileUrl = ossProperties.getDomain() + "/" + objectKey;
            log.info("文件上传成功: {}", fileUrl);
            return fileUrl;
        } catch (Exception e) {
            log.error("上传文件到OSS失败: {}", filePath, e);
            return null;
        }
    }

    @Override
    public boolean deleteFile(String filePath) {
        if (!ossProperties.isEnabled() || ossClient == null) {
            log.warn("OSS服务未启用或客户端未初始化");
            return false;
        }

        try {
            // 从完整URL中提取对象键
            String objectKey = extractObjectKey(filePath);
            if (objectKey == null) {
                log.error("无法从路径中提取对象键: {}", filePath);
                return false;
            }

            ossClient.deleteObject(ossProperties.getBucketName(), objectKey);
            log.info("文件删除成功: {}", filePath);
            return true;
        } catch (Exception e) {
            log.error("删除OSS文件失败: {}", filePath, e);
            return false;
        }
    }

    @Override
    public String getFileUrl(String filePath) {
        if (!ossProperties.isEnabled()) {
            return null;
        }

        // 如果已经是完整URL，直接返回
        if (filePath.startsWith("http")) {
            return filePath;
        }

        // 构建完整URL
        return ossProperties.getDomain() + "/" + filePath;
    }

    @Override
    public boolean fileExists(String filePath) {
        if (!ossProperties.isEnabled() || ossClient == null) {
            return false;
        }

        try {
            String objectKey = extractObjectKey(filePath);
            if (objectKey == null) {
                return false;
            }

            return ossClient.doesObjectExist(ossProperties.getBucketName(), objectKey);
        } catch (Exception e) {
            log.error("检查文件是否存在失败: {}", filePath, e);
            return false;
        }
    }

    /**
     * 从完整URL或路径中提取对象键
     *
     * @param filePath 文件路径或URL
     * @return 对象键
     */
    private String extractObjectKey(String filePath) {
        if (filePath == null || filePath.isEmpty()) {
            return null;
        }

        // 如果是完整URL，提取路径部分
        if (filePath.startsWith("http")) {
            try {
                String domain = ossProperties.getDomain();
                if (filePath.startsWith(domain)) {
                    return filePath.substring(domain.length() + 1);
                }
            } catch (Exception e) {
                log.error("提取对象键失败", e);
            }
        }

        // 直接返回路径
        return filePath;
    }
}