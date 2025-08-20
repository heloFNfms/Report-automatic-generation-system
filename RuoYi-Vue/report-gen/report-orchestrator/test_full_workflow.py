#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工作流测试
测试从Step1到Step5的完整报告生成流程
"""

import requests
import json
import time
from datetime import datetime

class FullWorkflowTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.task_id = None
        self.results = []
        
    def log_result(self, test_name, success, message, details=None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            result["details"] = details
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def test_step1_create_task(self):
        """测试Step1：创建任务"""
        try:
            payload = {
                "project_name": "AI技术发展趋势研究",
                "company_name": "科技研究院",
                "research_content": "分析人工智能在各行业的应用现状和未来发展趋势"
            }
            
            response = self.session.post(f"{self.base_url}/step1", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.task_id = data.get("task_id")
                if self.task_id:
                    self.log_result("Step1创建任务", True, f"任务创建成功，ID: {self.task_id}")
                    return True
                else:
                    self.log_result("Step1创建任务", False, "响应中缺少task_id")
                    return False
            else:
                self.log_result("Step1创建任务", False, f"HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Step1创建任务", False, f"异常: {str(e)}")
            return False
            
    def test_step2_generate_outline(self):
        """测试Step2：生成大纲"""
        if not self.task_id:
            self.log_result("Step2生成大纲", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step2", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                outline = data.get("研究大纲")
                if outline and isinstance(outline, list) and len(outline) > 0:
                    self.log_result("Step2生成大纲", True, f"大纲生成成功，包含{len(outline)}个主要章节")
                    return True
                else:
                    self.log_result("Step2生成大纲", False, "大纲格式异常或为空")
                    return False
            else:
                self.log_result("Step2生成大纲", False, f"HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Step2生成大纲", False, f"异常: {str(e)}")
            return False
            
    def test_step3_generate_content(self):
        """测试Step3：生成内容"""
        if not self.task_id:
            self.log_result("Step3生成内容", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step3", json=payload, timeout=120)  # 增加超时时间
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and len(data) > 0:
                    # 检查是否包含章节内容
                    content_sections = 0
                    for key, value in data.items():
                        if isinstance(value, dict) and "研究内容" in value:
                            content_sections += 1
                    
                    if content_sections > 0:
                        self.log_result("Step3生成内容", True, f"内容生成成功，包含{content_sections}个章节")
                        return True
                    else:
                        self.log_result("Step3生成内容", False, "内容格式异常")
                        return False
                else:
                    self.log_result("Step3生成内容", False, "内容为空或格式错误")
                    return False
            else:
                self.log_result("Step3生成内容", False, f"HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Step3生成内容", False, f"异常: {str(e)}")
            return False
            
    def test_step4_assemble_report(self):
        """测试Step4：组装报告"""
        if not self.task_id:
            self.log_result("Step4组装报告", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step4", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, str) and len(data) > 100:  # 报告应该有一定长度
                    self.log_result("Step4组装报告", True, f"报告组装成功，长度: {len(data)}字符")
                    return True
                else:
                    self.log_result("Step4组装报告", False, "报告内容异常或过短")
                    return False
            else:
                self.log_result("Step4组装报告", False, f"HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Step4组装报告", False, f"异常: {str(e)}")
            return False
            
    def test_step5_finalize_report(self):
        """测试Step5：完成报告"""
        if not self.task_id:
            self.log_result("Step5完成报告", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step5", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "摘要" in data and "关键词" in data and "完整文章" in data:
                    self.log_result("Step5完成报告", True, "最终报告生成成功，包含摘要、关键词和完整文章")
                    return True
                else:
                    self.log_result("Step5完成报告", False, "最终报告格式异常")
                    return False
            else:
                self.log_result("Step5完成报告", False, f"HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Step5完成报告", False, f"异常: {str(e)}")
            return False
            
    def run_full_test(self):
        """运行完整测试流程"""
        print("\n=== 完整工作流测试开始 ===")
        print(f"测试目标: {self.base_url}")
        print(f"开始时间: {datetime.now().isoformat()}")
        print()
        
        # 按顺序执行所有步骤
        steps = [
            self.test_step1_create_task,
            self.test_step2_generate_outline,
            self.test_step3_generate_content,
            self.test_step4_assemble_report,
            self.test_step5_finalize_report
        ]
        
        success_count = 0
        for step in steps:
            if step():
                success_count += 1
            else:
                print("\n❌ 测试失败，停止后续步骤")
                break
            time.sleep(2)  # 步骤间等待
            
        # 生成测试报告
        total_tests = len(steps)
        success_rate = (success_count / total_tests) * 100
        
        print("\n=== 测试报告 ===")
        print(f"总测试数: {total_tests}")
        print(f"通过: {success_count}")
        print(f"失败: {total_tests - success_count}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"\n测试完成时间: {datetime.now().isoformat()}")
        
        # 保存详细报告
        report = {
            "test_type": "full_workflow",
            "total_tests": total_tests,
            "passed": success_count,
            "failed": total_tests - success_count,
            "success_rate": success_rate,
            "task_id": self.task_id,
            "results": self.results,
            "generated_at": datetime.now().isoformat()
        }
        
        with open("full_workflow_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print("\n详细报告已保存到: full_workflow_report.json")
        
        return success_rate == 100.0

if __name__ == "__main__":
    tester = FullWorkflowTester()
    success = tester.run_full_test()
    exit(0 if success else 1)