# 安全修复指南

本文档提供了针对安全审计中发现问题的修复建议。

## 高危问题修复

### 1. DeepSeek API密钥配置

**问题**: 环境变量文件中API密钥为空

**修复步骤**:
1. 获取DeepSeek API密钥：访问 https://platform.deepseek.com/api_keys
2. 在 `report-orchestrator/.env` 文件中设置：
   ```bash
   DEEPSEEK_API_KEY=your_actual_api_key_here
   ```
3. 确保 `.env` 文件不被提交到版本控制系统
4. 运行验证脚本确认配置正确：
   ```bash
   cd report-orchestrator
   python validate_deepseek_config.py
   ```

### 2. 数据库连接字符串安全

**问题**: 数据库连接字符串包含明文密码

**修复建议**:
1. 使用环境变量分别存储数据库连接参数：
   ```bash
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=analyze_db
   DB_USER=root
   DB_PASSWORD=your_secure_password
   ```
2. 在代码中动态构建连接字符串
3. 考虑使用数据库连接池和SSL连接

## 中危问题修复

### 1. XSS风险 - v-html使用

**问题**: 多个Vue组件使用 `v-html` 可能导致XSS攻击

**修复策略**:

#### 对于报告内容显示：
```vue
<!-- 不安全的做法 -->
<div v-html="reportContent"></div>

<!-- 安全的做法 -->
<div v-dompurify-html="reportContent"></div>
```

#### 安装和配置DOMPurify：
```bash
cd ruoyi-ui
npm install dompurify
npm install vue-dompurify-html
```

#### 在main.js中注册：
```javascript
import VueDOMPurifyHTML from 'vue-dompurify-html'
Vue.use(VueDOMPurifyHTML)
```

#### 或者使用文本插值：
```vue
<!-- 对于纯文本内容 -->
<div>{{ reportContent }}</div>

<!-- 对于需要格式化的内容，使用过滤器 -->
<div>{{ reportContent | sanitize }}</div>
```

### 2. 文件上传安全

**问题**: 文件上传缺少类型和大小验证

**修复示例**:
```java
@PostMapping("/upload")
public AjaxResult uploadFile(@RequestParam("file") MultipartFile file) {
    // 1. 检查文件大小
    if (file.getSize() > 10 * 1024 * 1024) { // 10MB限制
        return AjaxResult.error("文件大小不能超过10MB");
    }
    
    // 2. 检查文件类型
    String contentType = file.getContentType();
    List<String> allowedTypes = Arrays.asList(
        "application/pdf", 
        "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    );
    
    if (!allowedTypes.contains(contentType)) {
        return AjaxResult.error("不支持的文件类型");
    }
    
    // 3. 检查文件扩展名
    String originalFilename = file.getOriginalFilename();
    if (originalFilename != null) {
        String extension = originalFilename.substring(originalFilename.lastIndexOf(".")).toLowerCase();
        List<String> allowedExtensions = Arrays.asList(".pdf", ".doc", ".docx");
        
        if (!allowedExtensions.contains(extension)) {
            return AjaxResult.error("不支持的文件扩展名");
        }
    }
    
    // 4. 生成安全的文件名
    String safeFilename = UUID.randomUUID().toString() + getFileExtension(originalFilename);
    
    // 继续处理文件...
}
```

### 3. SQL注入风险

**问题**: MyBatis XML中使用 `${}` 可能导致SQL注入

**修复方法**:
```xml
<!-- 不安全的做法 -->
<select id="selectByCondition">
    SELECT * FROM report WHERE title LIKE '%${title}%'
</select>

<!-- 安全的做法 -->
<select id="selectByCondition">
    SELECT * FROM report WHERE title LIKE CONCAT('%', #{title}, '%')
</select>

<!-- 对于动态ORDER BY，使用白名单验证 -->
<select id="selectWithOrder">
    SELECT * FROM report 
    <if test="orderBy != null and orderBy != ''">
        ORDER BY 
        <choose>
            <when test="orderBy == 'create_time'">create_time</when>
            <when test="orderBy == 'update_time'">update_time</when>
            <when test="orderBy == 'title'">title</when>
            <otherwise>id</otherwise>
        </choose>
    </if>
</select>
```

## 安全配置建议

### 1. CORS配置

在Spring Boot配置中：
```yaml
spring:
  web:
    cors:
      allowed-origins: 
        - "http://localhost:8080"
        - "https://yourdomain.com"
      allowed-methods: [GET, POST, PUT, DELETE]
      allowed-headers: ["*"]
      allow-credentials: true
      max-age: 3600
```

### 2. 安全头配置

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.headers(headers -> headers
            .frameOptions().deny()
            .contentTypeOptions().and()
            .httpStrictTransportSecurity(hstsConfig -> hstsConfig
                .maxAgeInSeconds(31536000)
                .includeSubdomains(true))
            .and()
        );
        return http.build();
    }
}
```

### 3. 输入验证

使用Bean Validation：
```java
public class ReportRequest {
    @NotBlank(message = "标题不能为空")
    @Size(max = 100, message = "标题长度不能超过100字符")
    private String title;
    
    @NotBlank(message = "内容不能为空")
    @Size(max = 10000, message = "内容长度不能超过10000字符")
    private String content;
    
    // getters and setters
}
```

## 安全检查清单

- [ ] 所有API密钥都通过环境变量配置
- [ ] 数据库连接使用加密和最小权限原则
- [ ] 所有用户输入都经过验证和清理
- [ ] 文件上传有类型、大小和内容检查
- [ ] SQL查询使用参数化查询
- [ ] 前端输出使用适当的转义
- [ ] CORS配置限制了允许的来源
- [ ] 启用了安全响应头
- [ ] 定期更新依赖库
- [ ] 实施日志记录和监控

## 持续安全实践

1. **定期安全扫描**: 每月运行安全检查脚本
2. **依赖更新**: 定期更新第三方库
3. **代码审查**: 所有涉及安全的代码变更都需要审查
4. **安全培训**: 团队成员定期接受安全培训
5. **渗透测试**: 定期进行安全测试

## 紧急响应

如果发现安全漏洞：
1. 立即评估影响范围
2. 实施临时缓解措施
3. 开发和测试修复方案
4. 部署修复
5. 验证修复效果
6. 更新安全文档

---

**注意**: 这些修复建议应该在测试环境中先行验证，确保不会影响系统正常功能。