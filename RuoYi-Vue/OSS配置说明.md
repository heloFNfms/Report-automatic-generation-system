# OSS云存储配置说明

## 概述

报告自动化生成系统已集成OSS云存储功能，支持将生成的报告文件自动上传到云端存储。目前支持阿里云OSS、腾讯云COS等主流云存储服务。

## 配置方式

### 方式一：环境变量配置（推荐）

在系统环境变量中设置以下配置项：

```bash
# OSS访问密钥ID
OSS_ACCESS_KEY_ID=your-actual-access-key-id

# OSS访问密钥Secret
OSS_ACCESS_KEY_SECRET=your-actual-access-key-secret

# OSS存储桶名称
OSS_BUCKET_NAME=your-bucket-name

# OSS服务端点
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com

# OSS文件访问域名
OSS_DOMAIN=https://your-bucket-name.oss-cn-hangzhou.aliyuncs.com
```

### 方式二：直接修改配置文件

编辑 `ruoyi-admin/src/main/resources/application.yml` 文件中的OSS配置：

```yaml
report:
  oss:
    # 是否启用OSS上传
    enabled: true
    # OSS服务提供商 (aliyun/tencent/aws)
    provider: aliyun
    # 访问密钥ID
    accessKeyId: your-actual-access-key-id
    # 访问密钥Secret
    accessKeySecret: your-actual-access-key-secret
    # 存储桶名称
    bucketName: your-bucket-name
    # 服务端点
    endpoint: oss-cn-hangzhou.aliyuncs.com
    # 文件访问域名
    domain: https://your-bucket-name.oss-cn-hangzhou.aliyuncs.com
    # 文件存储路径前缀
    pathPrefix: reports/
```

## 不同云服务商配置示例

### 阿里云OSS

```yaml
report:
  oss:
    provider: aliyun
    accessKeyId: LTAI5t...
    accessKeySecret: 2Kj8x...
    bucketName: my-report-bucket
    endpoint: oss-cn-hangzhou.aliyuncs.com
    domain: https://my-report-bucket.oss-cn-hangzhou.aliyuncs.com
```

### 腾讯云COS

```yaml
report:
  oss:
    provider: tencent
    accessKeyId: AKIDx...
    accessKeySecret: 3Kj9y...
    bucketName: my-report-bucket-1234567890
    endpoint: cos.ap-guangzhou.myqcloud.com
    domain: https://my-report-bucket-1234567890.cos.ap-guangzhou.myqcloud.com
```

### AWS S3

```yaml
report:
  oss:
    provider: aws
    accessKeyId: AKIA...
    accessKeySecret: 4Kj0z...
    bucketName: my-report-bucket
    endpoint: s3.us-west-2.amazonaws.com
    domain: https://my-report-bucket.s3.us-west-2.amazonaws.com
```

## 获取云存储配置信息

### 阿里云OSS

1. 登录阿里云控制台
2. 进入对象存储OSS服务
3. 创建Bucket或使用现有Bucket
4. 在访问控制 > 用户管理中创建RAM用户
5. 为RAM用户分配OSS相关权限
6. 获取AccessKey ID和AccessKey Secret

### 腾讯云COS

1. 登录腾讯云控制台
2. 进入对象存储COS服务
3. 创建存储桶或使用现有存储桶
4. 在访问管理 > 用户管理中创建子用户
5. 为子用户分配COS相关权限
6. 获取SecretId和SecretKey

## 权限配置

确保您的云存储账户具有以下权限：

- 对象读取权限（GetObject）
- 对象写入权限（PutObject）
- 对象删除权限（DeleteObject）
- 存储桶列表权限（ListBucket）

## 测试配置

配置完成后，可以通过以下方式测试：

1. 重启后端服务
2. 生成一个测试报告
3. 点击"发布"按钮
4. 检查云存储控制台是否有文件上传
5. 查看系统日志确认上传状态

## 注意事项

1. **安全性**：请妥善保管AccessKey信息，不要将其提交到代码仓库
2. **权限最小化**：建议为OSS服务单独创建子账户，只分配必要权限
3. **存储桶策略**：根据需要设置存储桶的访问策略和生命周期规则
4. **费用控制**：注意云存储的计费方式，合理设置文件生命周期
5. **网络连接**：确保服务器能够访问云存储服务的API端点

## 故障排查

如果OSS上传失败，请检查：

1. 网络连接是否正常
2. AccessKey配置是否正确
3. 存储桶名称和端点是否正确
4. 权限配置是否充足
5. 查看后端服务日志获取详细错误信息

## 禁用OSS功能

如果暂时不需要使用OSS功能，可以设置：

```yaml
report:
  oss:
    enabled: false
```

这样系统将跳过文件上传步骤，但仍会正常生成报告。