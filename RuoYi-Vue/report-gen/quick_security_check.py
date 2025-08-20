#!/usr/bin/env python3
"""
快速安全检查脚本
检查关键安全配置问题
"""

import os
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_env_security():
    """检查环境变量安全性"""
    logger.info("=== 检查环境变量安全性 ===")
    issues = []
    
    # 检查项目中的.env文件
    project_root = Path('D:/报告自动化生成系统/RuoYi-Vue')
    env_files = list(project_root.rglob('.env'))
    
    for env_file in env_files:
        if env_file.name in ['.env.template', '.env.example']:
            continue
            
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查空的API密钥
            if re.search(r'DEEPSEEK_API_KEY\s*=\s*$', content, re.MULTILINE):
                issues.append(f"❌ {env_file.relative_to(project_root)}: DeepSeek API密钥为空")
            
            # 检查硬编码的数据库密码
            db_match = re.search(r'MYSQL_DSN\s*=\s*(.+)', content)
            if db_match and 'password' not in db_match.group(1).lower():
                if re.search(r'://[^:]+:[^@]+@', db_match.group(1)):
                    issues.append(f"⚠️  {env_file.relative_to(project_root)}: 数据库连接字符串包含明文密码")
            
            logger.info(f"✅ 检查完成: {env_file.relative_to(project_root)}")
            
        except Exception as e:
            logger.error(f"❌ 无法读取 {env_file}: {e}")
    
    return issues

def check_cors_config():
    """检查CORS配置"""
    logger.info("=== 检查CORS配置 ===")
    issues = []
    
    project_root = Path('D:/报告自动化生成系统/RuoYi-Vue')
    
    # 检查Spring Boot配置文件
    config_files = (
        list(project_root.rglob('application*.yml')) +
        list(project_root.rglob('application*.yaml')) +
        list(project_root.rglob('application*.properties'))
    )
    
    for config_file in config_files:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查危险的CORS配置
            if re.search(r'allowed-origins.*\*', content, re.IGNORECASE):
                issues.append(f"❌ {config_file.relative_to(project_root)}: CORS允许所有来源 (*)")
            
            if (re.search(r'allow-credentials.*true', content, re.IGNORECASE) and 
                re.search(r'allowed-origins.*\*', content, re.IGNORECASE)):
                issues.append(f"❌ {config_file.relative_to(project_root)}: CORS同时允许凭据和所有来源")
            
            logger.info(f"✅ 检查完成: {config_file.relative_to(project_root)}")
            
        except Exception as e:
            logger.debug(f"无法读取 {config_file}: {e}")
    
    return issues

def check_upload_security():
    """检查文件上传安全性"""
    logger.info("=== 检查文件上传安全性 ===")
    issues = []
    
    project_root = Path('D:/报告自动化生成系统/RuoYi-Vue')
    
    # 检查Java文件中的上传逻辑
    java_files = list(project_root.rglob('*Controller.java'))
    
    for java_file in java_files:
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查文件上传方法
            if re.search(r'MultipartFile', content):
                # 检查是否有文件类型验证
                if not re.search(r'(getContentType|getOriginalFilename.*\.(jpg|png|pdf|doc))', content, re.IGNORECASE):
                    issues.append(f"⚠️  {java_file.relative_to(project_root)}: 文件上传缺少类型验证")
                
                # 检查是否有文件大小限制
                if not re.search(r'(getSize|maxFileSize|file.*size)', content, re.IGNORECASE):
                    issues.append(f"⚠️  {java_file.relative_to(project_root)}: 文件上传缺少大小限制")
                
                logger.info(f"✅ 检查完成: {java_file.relative_to(project_root)}")
            
        except Exception as e:
            logger.debug(f"无法读取 {java_file}: {e}")
    
    return issues

def check_sql_injection_basic():
    """基础SQL注入检查"""
    logger.info("=== 检查SQL注入风险 ===")
    issues = []
    
    project_root = Path('D:/报告自动化生成系统/RuoYi-Vue')
    
    # 检查Mapper文件
    mapper_files = list(project_root.rglob('*Mapper.xml'))
    
    for mapper_file in mapper_files:
        try:
            with open(mapper_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否使用了${}而不是#{}
            dollar_matches = re.findall(r'\$\{[^}]+\}', content)
            if dollar_matches:
                # 排除ORDER BY等合理使用场景
                for match in dollar_matches:
                    if not re.search(r'(order|sort|column)', match, re.IGNORECASE):
                        issues.append(f"⚠️  {mapper_file.relative_to(project_root)}: 使用${{}}可能存在SQL注入风险: {match}")
            
            logger.info(f"✅ 检查完成: {mapper_file.relative_to(project_root)}")
            
        except Exception as e:
            logger.debug(f"无法读取 {mapper_file}: {e}")
    
    return issues

def check_xss_basic():
    """基础XSS检查"""
    logger.info("=== 检查XSS风险 ===")
    issues = []
    
    project_root = Path('D:/报告自动化生成系统/RuoYi-Vue')
    
    # 检查Vue文件
    vue_files = list(project_root.rglob('*.vue'))
    
    for vue_file in vue_files:
        try:
            with open(vue_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查v-html的使用
            if re.search(r'v-html\s*=', content):
                issues.append(f"⚠️  {vue_file.relative_to(project_root)}: 使用v-html可能存在XSS风险")
            
            # 检查innerHTML的使用
            if re.search(r'innerHTML\s*=', content):
                issues.append(f"⚠️  {vue_file.relative_to(project_root)}: 使用innerHTML可能存在XSS风险")
            
            logger.info(f"✅ 检查完成: {vue_file.relative_to(project_root)}")
            
        except Exception as e:
            logger.debug(f"无法读取 {vue_file}: {e}")
    
    return issues

def check_deepseek_config():
    """检查DeepSeek配置安全性"""
    logger.info("=== 检查DeepSeek配置安全性 ===")
    issues = []
    
    project_root = Path('D:/报告自动化生成系统/RuoYi-Vue')
    
    # 检查Python文件中的硬编码API密钥
    python_files = list(project_root.rglob('*.py'))
    
    for py_file in python_files:
        if 'security_check' in py_file.name:
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查硬编码的API密钥
            api_key_match = re.search(r'["\']sk-[a-zA-Z0-9]{20,}["\']', content)
            if api_key_match:
                issues.append(f"❌ {py_file.relative_to(project_root)}: 发现硬编码的API密钥")
            
            # 检查不安全的API调用
            if re.search(r'verify\s*=\s*False', content):
                issues.append(f"⚠️  {py_file.relative_to(project_root)}: SSL验证被禁用")
            
            logger.info(f"✅ 检查完成: {py_file.relative_to(project_root)}")
            
        except Exception as e:
            logger.debug(f"无法读取 {py_file}: {e}")
    
    return issues

def main():
    """主函数"""
    logger.info("开始快速安全检查...")
    
    all_issues = []
    
    # 执行各项检查
    all_issues.extend(check_env_security())
    all_issues.extend(check_cors_config())
    all_issues.extend(check_upload_security())
    all_issues.extend(check_sql_injection_basic())
    all_issues.extend(check_xss_basic())
    all_issues.extend(check_deepseek_config())
    
    # 输出结果
    logger.info("\n=== 安全检查结果 ===")
    
    if not all_issues:
        logger.info("✅ 未发现明显的安全问题")
        return 0
    
    logger.warning(f"发现 {len(all_issues)} 个安全问题:")
    for i, issue in enumerate(all_issues, 1):
        logger.warning(f"  {i}. {issue}")
    
    # 统计问题类型
    high_issues = [issue for issue in all_issues if issue.startswith('❌')]
    medium_issues = [issue for issue in all_issues if issue.startswith('⚠️')]
    
    logger.info(f"\n问题统计:")
    logger.info(f"  高危问题: {len(high_issues)}")
    logger.info(f"  中危问题: {len(medium_issues)}")
    
    if high_issues:
        return 1
    elif medium_issues:
        return 2
    else:
        return 0

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)