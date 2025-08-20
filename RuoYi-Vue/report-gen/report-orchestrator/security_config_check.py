#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全配置检查脚本
检查环境变量配置的安全性，确保敏感信息不会泄露
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

class SecurityConfigChecker:
    """安全配置检查器"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        
    def check_env_file(self, env_path: str) -> Dict[str, List[str]]:
        """检查.env文件的安全性"""
        if not os.path.exists(env_path):
            self.issues.append(f"环境配置文件不存在: {env_path}")
            return {"issues": self.issues, "warnings": self.warnings}
            
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            self._check_line_security(line, line_num)
            
        return {"issues": self.issues, "warnings": self.warnings}
    
    def _check_line_security(self, line: str, line_num: int):
        """检查单行配置的安全性"""
        if '=' not in line:
            return
            
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # 检查空的API密钥
        if 'API_KEY' in key.upper() and not value:
            self.issues.append(f"第{line_num}行: {key} 为空，可能导致API调用失败")
            
        # 检查明文密码
        if any(keyword in key.upper() for keyword in ['PASSWORD', 'PASSWD', 'PWD']):
            if value and not value.startswith('${'):
                self.warnings.append(f"第{line_num}行: {key} 包含明文密码，建议使用环境变量")
                
        # 检查数据库连接字符串中的明文密码
        if 'DSN' in key.upper() and ':' in value and '@' in value:
            # 匹配类似 user:password@host 的模式
            if re.search(r'://[^:]+:[^@]+@', value):
                self.warnings.append(f"第{line_num}行: {key} 包含明文数据库密码")
                
        # 检查硬编码的敏感信息
        sensitive_patterns = [
            (r'sk-[a-zA-Z0-9]{32,}', 'OpenAI API密钥'),
            (r'[A-Za-z0-9]{32,}', '可能的API密钥'),
        ]
        
        for pattern, desc in sensitive_patterns:
            if re.search(pattern, value) and len(value) > 20:
                self.warnings.append(f"第{line_num}行: {key} 可能包含硬编码的{desc}")
                
    def generate_secure_template(self, env_path: str) -> str:
        """生成安全的环境变量模板"""
        template_path = env_path + '.template'
        
        if not os.path.exists(env_path):
            return template_path
            
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 替换敏感信息为占位符
        lines = content.split('\n')
        secure_lines = []
        
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 清空敏感配置
                if any(keyword in key.upper() for keyword in ['API_KEY', 'PASSWORD', 'PASSWD', 'PWD', 'DSN']):
                    secure_lines.append(f"# {key}=your_{key.lower()}_here")
                    secure_lines.append(f"{key}=")
                else:
                    secure_lines.append(line)
            else:
                secure_lines.append(line)
                
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(secure_lines))
            
        return template_path
        
    def create_security_guide(self) -> str:
        """创建安全配置指南"""
        guide = """
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
"""
        
        guide_path = "security_guide.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide)
            
        return guide_path

def main():
    """主函数"""
    checker = SecurityConfigChecker()
    
    # 检查环境配置文件
    env_files = [
        '.env',
        '../.env',
        '../../.env'
    ]
    
    print("🔍 开始安全配置检查...")
    print("=" * 50)
    
    found_files = []
    for env_file in env_files:
        if os.path.exists(env_file):
            found_files.append(env_file)
            print(f"📁 检查文件: {env_file}")
            result = checker.check_env_file(env_file)
            
            if result['issues']:
                print("\n❌ 发现安全问题:")
                for issue in result['issues']:
                    print(f"  - {issue}")
                    
            if result['warnings']:
                print("\n⚠️  安全警告:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
                    
            # 生成安全模板
            template_path = checker.generate_secure_template(env_file)
            print(f"\n📝 已生成安全模板: {template_path}")
            
    if not found_files:
        print("❌ 未找到环境配置文件")
        return
        
    # 创建安全指南
    guide_path = checker.create_security_guide()
    print(f"\n📚 已创建安全指南: {guide_path}")
    
    print("\n" + "=" * 50)
    print("✅ 安全检查完成")
    
    # 总结
    total_issues = len(checker.issues)
    total_warnings = len(checker.warnings)
    
    if total_issues > 0:
        print(f"🚨 发现 {total_issues} 个安全问题需要立即修复")
    if total_warnings > 0:
        print(f"⚠️  发现 {total_warnings} 个安全警告建议优化")
        
    if total_issues == 0 and total_warnings == 0:
        print("🎉 未发现明显的安全问题")

if __name__ == '__main__':
    main()