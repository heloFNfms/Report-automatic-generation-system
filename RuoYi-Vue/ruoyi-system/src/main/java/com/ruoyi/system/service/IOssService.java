package com.ruoyi.system.service;

import java.io.InputStream;

/**
 * OSS文件上传服务接口
 *
 * @author ruoyi
 */
public interface IOssService {
    /**
     * 上传文件到OSS
     *
     * @param inputStream 文件输入流
     * @param fileName    文件名
     * @param contentType 文件类型
     * @return 文件访问URL
     */
    String uploadFile(InputStream inputStream, String fileName, String contentType);

    /**
     * 上传文件到OSS（指定路径）
     *
     * @param inputStream 文件输入流
     * @param filePath    文件路径（包含文件名）
     * @param contentType 文件类型
     * @return 文件访问URL
     */
    String uploadFile(InputStream inputStream, String filePath, String contentType, boolean useFullPath);

    /**
     * 删除OSS文件
     *
     * @param filePath 文件路径
     * @return 是否删除成功
     */
    boolean deleteFile(String filePath);

    /**
     * 获取文件访问URL
     *
     * @param filePath 文件路径
     * @return 文件访问URL
     */
    String getFileUrl(String filePath);

    /**
     * 检查文件是否存在
     *
     * @param filePath 文件路径
     * @return 是否存在
     */
    boolean fileExists(String filePath);
}