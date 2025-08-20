#!/usr/bin/env python3
"""
安全修复脚本
自动修复安全审计中发现的问题
"""

import os
import re
import json
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityFixer:
    def __init__(self):
        self.project_root = Path('D:/报告自动化生成系统/RuoYi-Vue')
        self.ui_root = self.project_root / 'ruoyi-ui'
        self.report_gen_root = self.project_root / 'report-gen'
        self.fixes_applied = []
        
    def fix_xss_vulnerabilities(self):
        """修复XSS漏洞"""
        logger.info("=== 修复XSS漏洞 ===")
        
        # 1. 安装DOMPurify
        self._install_dompurify()
        
        # 2. 创建安全的HTML渲染组件
        self._create_safe_html_component()
        
        # 3. 修复v-html使用
        self._fix_vhtml_usage()
        
    def _install_dompurify(self):
        """安装DOMPurify依赖"""
        logger.info("安装DOMPurify依赖...")
        
        try:
            # 切换到前端项目目录
            os.chdir(self.ui_root)
            
            # 安装DOMPurify
            subprocess.run(['npm', 'install', 'dompurify', '@types/dompurify'], 
                         check=True, capture_output=True, text=True)
            
            logger.info("✅ DOMPurify安装成功")
            self.fixes_applied.append("安装DOMPurify依赖")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ DOMPurify安装失败: {e}")
        except Exception as e:
            logger.error(f"❌ 安装过程出错: {e}")
            
    def _create_safe_html_component(self):
        """创建安全的HTML渲染组件"""
        logger.info("创建安全HTML组件...")
        
        component_content = '''<template>
  <div ref="safeHtml"></div>
</template>

<script>
import DOMPurify from 'dompurify'

export default {
  name: 'SafeHtml',
  props: {
    content: {
      type: String,
      default: ''
    },
    config: {
      type: Object,
      default: () => ({
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th'],
        ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'style'],
        ALLOW_DATA_ATTR: false
      })
    }
  },
  watch: {
    content: {
      immediate: true,
      handler(newContent) {
        this.updateContent(newContent)
      }
    }
  },
  methods: {
    updateContent(content) {
      if (this.$refs.safeHtml) {
        const cleanHtml = DOMPurify.sanitize(content || '', this.config)
        this.$refs.safeHtml.innerHTML = cleanHtml
      }
    }
  },
  mounted() {
    this.updateContent(this.content)
  }
}
</script>

<style scoped>
/* 安全HTML组件样式 */
</style>
'''
        
        # 创建组件目录
        components_dir = self.ui_root / 'src' / 'components' / 'Security'
        components_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入组件文件
        component_file = components_dir / 'SafeHtml.vue'
        with open(component_file, 'w', encoding='utf-8') as f:
            f.write(component_content)
            
        logger.info(f"✅ 安全HTML组件创建成功: {component_file}")
        self.fixes_applied.append("创建SafeHtml安全组件")
        
    def _fix_vhtml_usage(self):
        """修复v-html使用"""
        logger.info("修复v-html使用...")
        
        # 需要修复的文件列表
        files_to_fix = [
            self.ui_root / 'src' / 'views' / 'system' / 'report' / 'index.vue',
            self.ui_root / 'src' / 'views' / 'system' / 'report' / 'wizard.vue',
            self.ui_root / 'src' / 'views' / 'system' / 'report' / 'editor.vue'
        ]
        
        for file_path in files_to_fix:
            if file_path.exists():
                self._fix_file_vhtml(file_path)
                
    def _fix_file_vhtml(self, file_path: Path):
        """修复单个文件的v-html使用"""
        logger.info(f"修复文件: {file_path.relative_to(self.ui_root)}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 备份原文件
            backup_path = file_path.with_suffix('.vue.backup')
            shutil.copy2(file_path, backup_path)
            
            # 替换v-html为安全组件
            # 匹配 <div v-html="xxx"></div> 模式
            pattern = r'<div([^>]*?)v-html="([^"]+)"([^>]*?)>([^<]*)</div>'
            
            def replace_vhtml(match):
                attrs_before = match.group(1)
                content_var = match.group(2)
                attrs_after = match.group(3)
                inner_content = match.group(4)
                
                # 构建SafeHtml组件
                return f'<SafeHtml{attrs_before}{attrs_after} :content="{content_var}" />'
            
            new_content = re.sub(pattern, replace_vhtml, content)
            
            # 添加组件导入
            if 'SafeHtml' in new_content and 'import SafeHtml' not in content:
                # 在script标签中添加导入
                script_pattern = r'(<script[^>]*>)'
                import_statement = '\n import SafeHtml from "@/components/Security/SafeHtml.vue"'
                
                def add_import(match):
                    return match.group(1) + import_statement
                
                new_content = re.sub(script_pattern, add_import, new_content)
                
                # 在components中注册组件
                components_pattern = r'(components\s*:\s*{)'
                component_registration = '\n    SafeHtml,'
                
                def add_component(match):
                    return match.group(1) + component_registration
                
                new_content = re.sub(components_pattern, add_component, new_content)
            
            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            logger.info(f"✅ 文件修复完成: {file_path.relative_to(self.ui_root)}")
            self.fixes_applied.append(f"修复v-html: {file_path.name}")
            
        except Exception as e:
            logger.error(f"❌ 文件修复失败 {file_path}: {e}")
            
    def fix_env_security(self):
        """修复环境变量安全问题"""
        logger.info("=== 修复环境变量安全问题 ===")
        
        # 检查.env文件
        env_files = [
            self.report_gen_root / 'report-orchestrator' / '.env',
            self.project_root / '.env'
        ]
        
        for env_file in env_files:
            if env_file.exists():
                self._fix_env_file(env_file)
                
    def _fix_env_file(self, env_file: Path):
        """修复单个环境变量文件"""
        logger.info(f"检查环境变量文件: {env_file.relative_to(self.project_root)}")
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查空的API密钥
            if re.search(r'DEEPSEEK_API_KEY\s*=\s*$', content, re.MULTILINE):
                logger.warning(f"⚠️  {env_file.name}: DeepSeek API密钥为空，需要手动设置")
                
                # 添加注释提示
                content = re.sub(
                    r'(DEEPSEEK_API_KEY\s*=\s*)$',
                    r'\1# TODO: 设置实际的API密钥',
                    content,
                    flags=re.MULTILINE
                )
                
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.fixes_applied.append(f"添加API密钥提示: {env_file.name}")
                
        except Exception as e:
            logger.error(f"❌ 环境变量文件处理失败 {env_file}: {e}")
            
    def create_security_guidelines(self):
        """创建安全开发指南"""
        logger.info("=== 创建安全开发指南 ===")
        
        guidelines_content = '''# 安全开发指南

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
'''
        
        guidelines_file = self.project_root / 'SECURITY_GUIDELINES.md'
        with open(guidelines_file, 'w', encoding='utf-8') as f:
            f.write(guidelines_content)
            
        logger.info(f"✅ 安全开发指南创建成功: {guidelines_file}")
        self.fixes_applied.append("创建安全开发指南")
        
    def generate_report(self):
        """生成修复报告"""
        logger.info("=== 生成修复报告 ===")
        
        report_content = f'''# 安全修复报告

生成时间: {os.popen('date').read().strip()}

## 已应用的修复

'''
        
        for i, fix in enumerate(self.fixes_applied, 1):
            report_content += f"{i}. {fix}\n"
            
        report_content += '''

## 需要手动处理的问题

1. **DeepSeek API密钥配置**
   - 文件: `report-orchestrator/.env`
   - 操作: 设置 `DEEPSEEK_API_KEY=your_actual_api_key`

2. **数据库密码安全**
   - 检查所有数据库连接字符串
   - 使用环境变量存储密码

3. **生产环境部署**
   - 确保HTTPS配置
   - 设置适当的文件权限
   - 配置防火墙规则

## 验证步骤

1. 运行前端项目，检查SafeHtml组件是否正常工作
2. 运行安全审计脚本验证修复效果
3. 进行渗透测试

## 后续建议

1. 定期进行安全审计
2. 实施代码审查流程
3. 建立安全培训计划
4. 配置自动化安全扫描
'''
        
        report_file = self.project_root / 'SECURITY_FIX_REPORT.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        logger.info(f"✅ 修复报告生成成功: {report_file}")
        
    def run_all_fixes(self):
        """运行所有修复"""
        logger.info("开始安全修复...")
        
        try:
            # 1. 修复XSS漏洞
            self.fix_xss_vulnerabilities()
            
            # 2. 修复环境变量安全问题
            self.fix_env_security()
            
            # 3. 创建安全指南
            self.create_security_guidelines()
            
            # 4. 生成修复报告
            self.generate_report()
            
            logger.info(f"\n=== 修复完成 ===")
            logger.info(f"共应用 {len(self.fixes_applied)} 项修复")
            
            return True
            
        except Exception as e:
            logger.error(f"修复过程出错: {e}")
            return False

def main():
    """主函数"""
    fixer = SecurityFixer()
    success = fixer.run_all_fixes()
    
    if success:
        logger.info("\n✅ 安全修复成功完成！")
        logger.info("请查看 SECURITY_FIX_REPORT.md 了解详细信息")
        return 0
    else:
        logger.error("\n❌ 安全修复过程中出现错误")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)