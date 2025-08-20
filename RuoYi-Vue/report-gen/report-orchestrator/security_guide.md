
# 环境变量安全配置指南

## 1. API密钥管理
- 永远不要在代码中硬编码API密钥
- 使用环境变量或密钥管理服务
- 定期轮换API密钥
- 为不同环境使用不同的密钥

## 2. 数据库连接安全
- 避免在连接字符串中使用明文密码
- 使用环境变量存储数据库凭据
- 考虑使用连接池和SSL连接

## 3. 配置文件安全
- .env文件应该被添加到.gitignore
- 提供.env.template作为配置模板
- 在生产环境中使用密钥管理服务

## 4. 最佳实践
- 使用最小权限原则
- 定期审计配置文件
- 监控异常的API调用
- 实施访问日志记录

## 5. 环境变量示例
```bash
# 正确的方式
export DEEPSEEK_API_KEY="your_actual_api_key"
export DB_PASSWORD="your_db_password"

# 在应用中使用
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
MYSQL_DSN=mysql+asyncmy://user:${DB_PASSWORD}@localhost:3306/db
```
