# 安全开发指南

## 前端安全

### 1. XSS防护

#### 使用SafeHtml组件替代v-html
```vue
<!-- 不安全的做法 -->
<div v-html="userContent"></div>

<!-- 安全的做法 -->
<SafeHtml :content="userContent" />
```

#### 配置DOMPurify
```javascript
// 自定义配置
const config = {
  ALLOWED_TAGS: ['p', 'br', 'strong', 'em'],
  ALLOWED_ATTR: ['class'],
  ALLOW_DATA_ATTR: false
}
```

### 2. 输入验证
- 所有用户输入必须进行验证
- 使用白名单而非黑名单
- 对特殊字符进行转义

## 后端安全

### 1. API密钥管理
- 使用环境变量存储敏感信息
- 定期轮换API密钥
- 实施访问控制

### 2. 数据库安全
- 使用参数化查询
- 最小权限原则
- 定期备份

## 部署安全

### 1. 环境变量
- 生产环境不使用默认密码
- 限制文件权限
- 使用HTTPS

### 2. 监控
- 实施日志记录
- 异常检测
- 安全审计

## 检查清单

- [ ] 所有v-html已替换为SafeHtml组件
- [ ] API密钥已正确配置
- [ ] 数据库连接使用环境变量
- [ ] 输入验证已实施
- [ ] 错误处理不泄露敏感信息
- [ ] 日志记录已配置
