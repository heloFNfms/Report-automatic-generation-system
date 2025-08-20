# OSS配置检查工具

## 当前配置状态

### 1. 检查配置文件

当前系统的OSS配置位于：`ruoyi-admin/src/main/resources/application.yml`

```yaml
report:
  oss:
    enabled: true  # 是否启用OSS功能
    provider: aliyun  # 目前仅支持阿里云OSS
    accessKeyId: ${OSS_ACCESS_KEY_ID:your-access-key-id}
    accessKeySecret: ${OSS_ACCESS_KEY_SECRET:your-access-key-secret}
    bucketName: ${OSS_BUCKET_NAME:report-storage}
    endpoint: ${OSS_ENDPOINT:oss-cn-hangzhou.aliyuncs.com}
    domain: ${OSS_DOMAIN:https://report-storage.oss-cn-hangzhou.aliyuncs.com}
    pathPrefix: reports/
```

### 2. 支持的云服务商

**当前实现状态：**
- ✅ **阿里云OSS** - 已完全实现
- ❌ **腾讯云COS** - 配置文档已准备，但代码未实现
- ❌ **AWS S3** - 配置文档已准备，但代码未实现

### 3. 配置检查清单

#### 必需配置项
- [ ] `accessKeyId` - OSS访问密钥ID
- [ ] `accessKeySecret` - OSS访问密钥Secret
- [ ] `bucketName` - OSS存储桶名称
- [ ] `endpoint` - OSS服务端点
- [ ] `domain` - OSS文件访问域名

#### 可选配置项
- [ ] `enabled` - 是否启用OSS（默认：true）
- [ ] `provider` - 云服务商（目前仅支持：aliyun）
- [ ] `pathPrefix` - 文件路径前缀（默认：reports/）
- [ ] `connectTimeout` - 连接超时时间（默认：10000ms）
- [ ] `readTimeout` - 读取超时时间（默认：30000ms）

## 配置方法

### 方法一：环境变量（推荐）

在系统环境变量中设置：

```bash
# Windows PowerShell
$env:OSS_ACCESS_KEY_ID="your-actual-access-key-id"
$env:OSS_ACCESS_KEY_SECRET="your-actual-access-key-secret"
$env:OSS_BUCKET_NAME="your-bucket-name"
$env:OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
$env:OSS_DOMAIN="https://your-bucket-name.oss-cn-hangzhou.aliyuncs.com"

# Linux/Mac
export OSS_ACCESS_KEY_ID="your-actual-access-key-id"
export OSS_ACCESS_KEY_SECRET="your-actual-access-key-secret"
export OSS_BUCKET_NAME="your-bucket-name"
export OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
export OSS_DOMAIN="https://your-bucket-name.oss-cn-hangzhou.aliyuncs.com"
```

### 方法二：直接修改配置文件

编辑 `application.yml` 文件，将占位符替换为实际值：

```yaml
report:
  oss:
    accessKeyId: LTAI5tXXXXXXXXXXXX  # 替换为实际的AccessKey ID
    accessKeySecret: 2Kj8xXXXXXXXXXXXXXXXXXXXXXXXXXX  # 替换为实际的AccessKey Secret
    bucketName: my-report-bucket  # 替换为实际的存储桶名称
    endpoint: oss-cn-hangzhou.aliyuncs.com  # 替换为实际的端点
    domain: https://my-report-bucket.oss-cn-hangzhou.aliyuncs.com  # 替换为实际的域名
```

## 配置验证

### 1. 启动时检查

重启后端服务后，查看日志输出：

```
# 成功配置的日志
OSS客户端初始化成功，endpoint: oss-cn-hangzhou.aliyuncs.com, bucket: your-bucket-name

# 未启用OSS的日志
OSS服务未启用

# 配置错误的日志
OSS客户端初始化失败
```

### 2. 功能测试

1. 生成一个测试报告
2. 点击"发布"按钮
3. 查看系统日志：
   - 成功：`文件上传成功: https://your-bucket.oss-cn-hangzhou.aliyuncs.com/reports/...`
   - 失败：`上传文件到OSS失败: ...`

### 3. 阿里云控制台验证

登录阿里云OSS控制台，检查：
- 存储桶是否存在
- `reports/` 目录下是否有上传的文件
- 文件是否可以正常访问

## 常见问题

### 1. 配置未生效

**问题**：修改配置后OSS功能仍然不工作

**解决方案**：
- 确保重启了后端服务
- 检查环境变量是否正确设置
- 验证配置文件语法是否正确

### 2. 权限不足

**问题**：`AccessDenied` 错误

**解决方案**：
- 检查AccessKey是否有OSS权限
- 确认存储桶策略允许当前操作
- 验证RAM用户权限配置

### 3. 网络连接问题

**问题**：连接超时或网络错误

**解决方案**：
- 检查服务器网络连接
- 验证endpoint地址是否正确
- 确认防火墙设置

### 4. 存储桶不存在

**问题**：`NoSuchBucket` 错误

**解决方案**：
- 在阿里云控制台创建对应的存储桶
- 确认存储桶名称拼写正确
- 检查存储桶所在区域与endpoint匹配

## 临时禁用OSS

如果暂时不需要使用OSS功能，可以设置：

```yaml
report:
  oss:
    enabled: false
```

或设置环境变量：

```bash
# Windows
$env:REPORT_OSS_ENABLED="false"

# Linux/Mac
export REPORT_OSS_ENABLED="false"
```

这样系统将跳过文件上传步骤，但仍会正常生成和管理报告。

## 扩展支持其他云服务商

目前系统架构已支持多云服务商扩展，但代码实现仅支持阿里云OSS。如需支持腾讯云COS或AWS S3，需要：

1. 添加对应的SDK依赖
2. 扩展 `OssServiceImpl` 类
3. 根据 `provider` 配置选择不同的客户端实现

这部分功能可以根据实际需求进行开发。