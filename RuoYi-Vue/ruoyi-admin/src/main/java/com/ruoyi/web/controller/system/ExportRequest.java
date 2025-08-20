package com.ruoyi.web.controller.system;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Pattern;

/**
 * 导出请求参数
 * 
 * @author ruoyi
 */
public class ExportRequest {
    /** 导出格式 (pdf, docx) */
    @NotBlank(message = "导出格式不能为空")
    @Pattern(regexp = "^(pdf|docx)$", message = "导出格式只支持pdf或docx")
    private String format;

    /** 是否上传到对象存储 */
    private boolean uploadToOss;

    public ExportRequest() {
    }

    public ExportRequest(String format, boolean uploadToOss) {
        this.format = format;
        this.uploadToOss = uploadToOss;
    }

    public String getFormat() {
        return format;
    }

    public void setFormat(String format) {
        this.format = format;
    }

    public boolean isUploadToOss() {
        return uploadToOss;
    }

    public void setUploadToOss(boolean uploadToOss) {
        this.uploadToOss = uploadToOss;
    }

    @Override
    public String toString() {
        return "ExportRequest{" +
                "format='" + format + '\'' +
                ", uploadToOss=" + uploadToOss +
                '}';
    }
}