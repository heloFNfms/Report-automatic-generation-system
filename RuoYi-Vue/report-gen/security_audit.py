#!/usr/bin/env python3
"""
安全审计脚本
检查报告自动化生成系统的安全配置
"""

import os
import re
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityAuditor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        self.info = []
    
    def add_issue(self, category: str, severity: str, message: str, file_path: str = None):
        """添加安全问题"""
        issue = {
            'category': category,
            'severity': severity,
            'message': message,
            'file': file_path
        }
        
        if severity == 'HIGH':
            self.issues.append(issue)
        elif severity == 'MEDIUM':
            self.warnings.append(issue)
        else:
            self.info.append(issue)
    
    def check_hardcoded_secrets(self):
        """检查硬编码的密钥和敏感信息"""
        logger.info("=== 检查硬编码密钥 ===")
        
        # 敏感信息模式
        patterns = {
            'api_key': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
            'password': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\';,]{8,})["\']?',
            'secret': r'(?i)(secret|token)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
            'database_url': r'(?i)(database_url|db_url|dsn)\s*[=:]\s*["\']?([^\s"\';,]+://[^\s"\';,]+)["\']?',
            'jwt_secret': r'(?i)(jwt[_-]?secret|jwt[_-]?key)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?'
        }
        
        # 排除的文件类型和路径
        exclude_patterns = [
            r'\.git/',
            r'node_modules/',
            r'\.pyc$',
            r'\.class$',
            r'\.jar$',
            r'\.log$',
            r'security_audit\.py$',
            r'\.env\.template$',
            r'\.env\.example$'
        ]
        
        def should_exclude(file_path: str) -> bool:
            for pattern in exclude_patterns:
                if re.search(pattern, file_path):
                    return True
            return False
        
        # 扫描文件
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and not should_exclude(str(file_path)):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern_name, pattern in patterns.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            # 检查是否是注释或示例
                            line_start = content.rfind('\n', 0, match.start()) + 1
                            line_end = content.find('\n', match.end())
                            if line_end == -1:
                                line_end = len(content)
                            line = content[line_start:line_end]
                            
                            # 跳过注释行和示例
                            if (line.strip().startswith('#') or 
                                line.strip().startswith('//') or
                                'example' in line.lower() or
                                'your_' in match.group(2).lower() or
                                'placeholder' in match.group(2).lower() or
                                match.group(2) in ['password', 'secret', 'key']):
                                continue
                            
                            self.add_issue(
                                'hardcoded_secrets',
                                'HIGH',
                                f"发现硬编码的{pattern_name}: {match.group(2)[:10]}...",
                                str(file_path.relative_to(self.project_root))
                            )
                            
                except Exception as e:
                    logger.debug(f"无法读取文件 {file_path}: {e}")
    
    def check_env_files(self):
        """检查环境变量文件的安全性"""
        logger.info("=== 检查环境变量文件 ===")
        
        env_files = list(self.project_root.rglob('.env*'))
        
        for env_file in env_files:
            if env_file.name in ['.env.template', '.env.example']:
                continue
                
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含实际的密钥值
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        # 检查敏感键值
                        sensitive_keys = ['API_KEY', 'PASSWORD', 'SECRET', 'TOKEN', 'DSN']
                        if any(sk in key.upper() for sk in sensitive_keys):
                            if value and value not in ['', 'your_key_here', 'placeholder']:
                                self.add_issue(
                                    'env_security',
                                    'MEDIUM',
                                    f"环境变量文件包含实际密钥值: {key}",
                                    str(env_file.relative_to(self.project_root))
                                )
                
                # 检查文件权限（Windows上权限检查有限）
                if env_file.stat().st_mode & 0o077:
                    self.add_issue(
                        'file_permissions',
                        'MEDIUM',
                        f"环境变量文件权限过于宽松",
                        str(env_file.relative_to(self.project_root))
                    )
                    
            except Exception as e:
                logger.debug(f"无法读取环境变量文件 {env_file}: {e}")
    
    def check_sql_injection(self):
        """检查SQL注入风险"""
        logger.info("=== 检查SQL注入风险 ===")
        
        # SQL注入风险模式
        patterns = [
            r'(?i)\+\s*["\']\s*\+',  # 字符串拼接
            r'(?i)format\s*\([^)]*%[sd][^)]*\)',  # 格式化字符串
            r'(?i)execute\s*\([^)]*\+[^)]*\)',  # 执行拼接的SQL
            r'(?i)query\s*\([^)]*\+[^)]*\)',  # 查询拼接的SQL
        ]
        
        java_files = list(self.project_root.rglob('*.java'))
        python_files = list(self.project_root.rglob('*.py'))
        
        for file_path in java_files + python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # 获取匹配行
                        line_start = content.rfind('\n', 0, match.start()) + 1
                        line_end = content.find('\n', match.end())
                        if line_end == -1:
                            line_end = len(content)
                        line = content[line_start:line_end].strip()
                        
                        # 跳过注释
                        if line.startswith('//') or line.startswith('#'):
                            continue
                        
                        self.add_issue(
                            'sql_injection',
                            'HIGH',
                            f"潜在SQL注入风险: {line[:50]}...",
                            str(file_path.relative_to(self.project_root))
                        )
                        
            except Exception as e:
                logger.debug(f"无法读取文件 {file_path}: {e}")
    
    def check_xss_vulnerabilities(self):
        """检查XSS漏洞"""
        logger.info("=== 检查XSS漏洞 ===")
        
        # XSS风险模式
        patterns = [
            r'(?i)innerHTML\s*=\s*[^;]+\+',  # innerHTML拼接
            r'(?i)document\.write\s*\([^)]*\+',  # document.write拼接
            r'(?i)eval\s*\([^)]*\+',  # eval拼接
            r'(?i)\$\{[^}]*\}',  # 模板字符串（可能的XSS）
        ]
        
        web_files = (
            list(self.project_root.rglob('*.js')) +
            list(self.project_root.rglob('*.vue')) +
            list(self.project_root.rglob('*.html')) +
            list(self.project_root.rglob('*.jsp'))
        )
        
        for file_path in web_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # 获取匹配行
                        line_start = content.rfind('\n', 0, match.start()) + 1
                        line_end = content.find('\n', match.end())
                        if line_end == -1:
                            line_end = len(content)
                        line = content[line_start:line_end].strip()
                        
                        # 跳过注释
                        if line.startswith('//') or line.startswith('<!--'):
                            continue
                        
                        self.add_issue(
                            'xss_vulnerability',
                            'MEDIUM',
                            f"潜在XSS风险: {line[:50]}...",
                            str(file_path.relative_to(self.project_root))
                        )
                        
            except Exception as e:
                logger.debug(f"无法读取文件 {file_path}: {e}")
    
    def check_cors_configuration(self):
        """检查CORS配置"""
        logger.info("=== 检查CORS配置 ===")
        
        # 查找CORS配置文件
        config_files = (
            list(self.project_root.rglob('*.properties')) +
            list(self.project_root.rglob('*.yml')) +
            list(self.project_root.rglob('*.yaml')) +
            list(self.project_root.rglob('*.java'))
        )
        
        for file_path in config_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 检查危险的CORS配置
                if re.search(r'(?i)allowedOrigins.*\*', content):
                    self.add_issue(
                        'cors_security',
                        'HIGH',
                        "CORS配置允许所有来源 (*)",
                        str(file_path.relative_to(self.project_root))
                    )
                
                if re.search(r'(?i)allowCredentials.*true', content) and re.search(r'(?i)allowedOrigins.*\*', content):
                    self.add_issue(
                        'cors_security',
                        'HIGH',
                        "CORS配置同时允许凭据和所有来源",
                        str(file_path.relative_to(self.project_root))
                    )
                    
            except Exception as e:
                logger.debug(f"无法读取文件 {file_path}: {e}")
    
    def check_upload_security(self):
        """检查文件上传安全性"""
        logger.info("=== 检查文件上传安全性 ===")
        
        java_files = list(self.project_root.rglob('*.java'))
        python_files = list(self.project_root.rglob('*.py'))
        
        for file_path in java_files + python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 检查文件上传相关代码
                if re.search(r'(?i)(MultipartFile|FileUpload|upload)', content):
                    # 检查是否有文件类型验证
                    if not re.search(r'(?i)(contentType|mimeType|extension|suffix)', content):
                        self.add_issue(
                            'upload_security',
                            'MEDIUM',
                            "文件上传缺少类型验证",
                            str(file_path.relative_to(self.project_root))
                        )
                    
                    # 检查是否有文件大小限制
                    if not re.search(r'(?i)(size|length|maxSize)', content):
                        self.add_issue(
                            'upload_security',
                            'LOW',
                            "文件上传缺少大小限制",
                            str(file_path.relative_to(self.project_root))
                        )
                        
            except Exception as e:
                logger.debug(f"无法读取文件 {file_path}: {e}")
    
    def check_authentication(self):
        """检查认证配置"""
        logger.info("=== 检查认证配置 ===")
        
        # 查找认证相关文件
        auth_files = (
            list(self.project_root.rglob('*Security*.java')) +
            list(self.project_root.rglob('*Auth*.java')) +
            list(self.project_root.rglob('*Login*.java'))
        )
        
        for file_path in auth_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 检查是否禁用了CSRF保护
                if re.search(r'(?i)csrf\(\)\.disable\(\)', content):
                    self.add_issue(
                        'authentication',
                        'MEDIUM',
                        "CSRF保护被禁用",
                        str(file_path.relative_to(self.project_root))
                    )
                
                # 检查是否使用了弱密码策略
                if re.search(r'(?i)permitAll\(\)', content):
                    self.add_issue(
                        'authentication',
                        'LOW',
                        "存在允许所有访问的端点",
                        str(file_path.relative_to(self.project_root))
                    )
                    
            except Exception as e:
                logger.debug(f"无法读取文件 {file_path}: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """生成安全审计报告"""
        report = {
            'summary': {
                'high_issues': len(self.issues),
                'medium_issues': len(self.warnings),
                'low_issues': len(self.info),
                'total_issues': len(self.issues) + len(self.warnings) + len(self.info)
            },
            'high_severity': self.issues,
            'medium_severity': self.warnings,
            'low_severity': self.info
        }
        
        return report
    
    def run_audit(self):
        """运行完整的安全审计"""
        logger.info("开始安全审计...")
        
        self.check_hardcoded_secrets()
        self.check_env_files()
        self.check_sql_injection()
        self.check_xss_vulnerabilities()
        self.check_cors_configuration()
        self.check_upload_security()
        self.check_authentication()
        
        return self.generate_report()

def main():
    project_root = os.getenv('PROJECT_ROOT', 'D:\\报告自动化生成系统\\RuoYi-Vue')
    
    auditor = SecurityAuditor(project_root)
    report = auditor.run_audit()
    
    # 输出报告
    logger.info("\n=== 安全审计报告 ===")
    logger.info(f"高危问题: {report['summary']['high_issues']}")
    logger.info(f"中危问题: {report['summary']['medium_issues']}")
    logger.info(f"低危问题: {report['summary']['low_issues']}")
    logger.info(f"总计问题: {report['summary']['total_issues']}")
    
    # 详细问题列表
    if report['high_severity']:
        logger.error("\n=== 高危问题 ===")
        for issue in report['high_severity']:
            logger.error(f"[{issue['category']}] {issue['message']}")
            if issue['file']:
                logger.error(f"  文件: {issue['file']}")
    
    if report['medium_severity']:
        logger.warning("\n=== 中危问题 ===")
        for issue in report['medium_severity']:
            logger.warning(f"[{issue['category']}] {issue['message']}")
            if issue['file']:
                logger.warning(f"  文件: {issue['file']}")
    
    if report['low_severity']:
        logger.info("\n=== 低危问题 ===")
        for issue in report['low_severity']:
            logger.info(f"[{issue['category']}] {issue['message']}")
            if issue['file']:
                logger.info(f"  文件: {issue['file']}")
    
    # 保存报告到文件
    report_file = Path(project_root) / 'security_audit_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n详细报告已保存到: {report_file}")
    
    # 返回退出码
    if report['summary']['high_issues'] > 0:
        return 1
    elif report['summary']['medium_issues'] > 0:
        return 2
    else:
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)