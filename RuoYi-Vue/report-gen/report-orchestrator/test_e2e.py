#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整端到端测试脚本
测试报告生成系统的完整流程：Step1→Step5→导出→上传→下载
以及单步重跑/回滚场景
"""

import requests
import json
import time
from datetime import datetime
import os

class E2ETestRunner:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.task_id = None
        
    def log_test(self, test_name, success, message="", response_data=None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def test_health_check(self):
        """测试健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_test("健康检查", True, "服务正常运行")
                return True
            else:
                self.log_test("健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("健康检查", False, f"连接失败: {str(e)}")
            return False
            
    def test_step1_topic_generation(self):
        """测试Step1：主题生成"""
        try:
            payload = {
                "project_name": "人工智能在医疗领域的应用研究",
                "company_name": "测试公司",
                "research_content": "分析AI在医疗诊断、药物研发、医疗影像分析等方面的应用现状、技术挑战和发展趋势"
            }
            response = self.session.post(f"{self.base_url}/step1", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "task_id" in data:
                    self.task_id = data["task_id"]
                    self.log_test("Step1主题生成", True, f"任务创建成功，ID: {self.task_id}")
                    return True
                else:
                    self.log_test("Step1主题生成", False, "响应中缺少task_id")
                    return False
            else:
                self.log_test("Step1主题生成", False, f"请求失败: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Step1主题生成", False, f"请求失败: {str(e)}")
            return False
            
    def test_step2_outline_generation(self):
        """测试Step2：大纲生成"""
        if not self.task_id:
            self.log_test("Step2大纲生成", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step2", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Step2大纲生成", True, "大纲生成成功")
                return True
            else:
                self.log_test("Step2大纲生成", False, f"请求失败: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("Step2大纲生成", False, f"请求失败: {str(e)}")
            return False
            
    def test_step3_content_collection(self):
        """测试Step3：资料搜集"""
        if not self.task_id:
            self.log_test("Step3资料搜集", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step3", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Step3资料搜集", True, "资料搜集成功")
                return True
            else:
                self.log_test("Step3资料搜集", False, f"请求失败: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("Step3资料搜集", False, f"请求失败: {str(e)}")
            return False
            
    def test_step4_content_generation(self):
        """测试Step4：内容生成"""
        if not self.task_id:
            self.log_test("Step4内容生成", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step4", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Step4内容生成", True, "内容生成成功")
                return True
            else:
                self.log_test("Step4内容生成", False, f"请求失败: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("Step4内容生成", False, f"请求失败: {str(e)}")
            return False
            
    def test_step5_review_optimization(self):
        """测试Step5：审核优化"""
        if not self.task_id:
            self.log_test("Step5审核优化", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step5", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Step5审核优化", True, "审核优化成功")
                return True
            else:
                self.log_test("Step5审核优化", False, f"请求失败: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("Step5审核优化", False, f"请求失败: {str(e)}")
            return False
            
    def test_export_pdf(self):
        """测试PDF导出"""
        if not self.task_id:
            self.log_test("PDF导出", False, "缺少task_id")
            return False
            
        try:
            payload = {
                "task_id": self.task_id,
                "format": "pdf",
                "upload_to_oss": False
            }
            response = self.session.post(f"{self.base_url}/export", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("PDF导出", True, "PDF导出成功")
                return True
            else:
                self.log_test("PDF导出", False, f"导出失败: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("PDF导出", False, f"导出失败: {str(e)}")
            return False
            
    def test_export_word(self):
        """测试Word导出"""
        if not self.task_id:
            self.log_test("Word导出", False, "缺少task_id")
            return False
            
        try:
            payload = {
                "task_id": self.task_id,
                "format": "docx",
                "upload_to_oss": False
            }
            response = self.session.post(f"{self.base_url}/export", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Word导出", True, "Word导出成功")
                return True
            else:
                self.log_test("Word导出", False, f"导出失败: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("Word导出", False, f"导出失败: {str(e)}")
            return False
            
    def test_step_history(self):
        """测试步骤历史查询"""
        if not self.task_id:
            self.log_test("步骤历史查询", False, "缺少task_id")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/task/{self.task_id}/history/step2")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("步骤历史查询", True, "历史查询成功")
                return True
            else:
                self.log_test("步骤历史查询", False, f"查询失败: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("步骤历史查询", False, f"查询失败: {str(e)}")
            return False
            
    def test_step_rerun(self):
        """测试步骤重跑"""
        if not self.task_id:
            self.log_test("步骤重跑", False, "缺少task_id")
            return False
            
        try:
            payload = {
                "task_id": self.task_id,
                "step": "step2"
            }
            response = self.session.post(f"{self.base_url}/rerun", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("步骤重跑", True, "重跑成功")
                return True
            else:
                self.log_test("步骤重跑", False, f"重跑失败: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("步骤重跑", False, f"重跑失败: {str(e)}")
            return False
            
    def test_step_rollback(self):
        """测试步骤回滚"""
        if not self.task_id:
            self.log_test("步骤回滚", False, "缺少task_id")
            return False
            
        try:
            payload = {
                "task_id": self.task_id,
                "step": "step2",
                "version": 1
            }
            response = self.session.post(f"{self.base_url}/rollback", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("步骤回滚", True, "回滚成功")
                return True
            else:
                self.log_test("步骤回滚", False, f"回滚失败: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("步骤回滚", False, f"回滚失败: {str(e)}")
            return False
            
    def run_full_pipeline_test(self):
        """运行完整流水线测试"""
        print("\n=== 完整端到端测试开始 ===")
        print(f"测试目标: {self.base_url}")
        print(f"开始时间: {datetime.now().isoformat()}")
        print()
        
        # 基础检查
        if not self.test_health_check():
            print("❌ 健康检查失败，停止测试")
            return
            
        # 完整流水线测试
        pipeline_tests = [
            ("Step1主题生成", self.test_step1_topic_generation),
            ("Step2大纲生成", self.test_step2_outline_generation),
            ("Step3资料搜集", self.test_step3_content_collection),
            ("Step4内容生成", self.test_step4_content_generation),
            ("Step5审核优化", self.test_step5_review_optimization),
        ]
        
        # 执行流水线测试
        pipeline_success = True
        for test_name, test_func in pipeline_tests:
            if not test_func():
                pipeline_success = False
                print(f"❌ {test_name}失败，跳过后续步骤")
                break
            time.sleep(2)  # 步骤间延迟
            
        # 如果流水线成功，测试导出功能
        if pipeline_success:
            print("\n--- 测试导出功能 ---")
            self.test_export_pdf()
            time.sleep(1)
            self.test_export_word()
            
            print("\n--- 测试历史和重跑功能 ---")
            self.test_step_history()
            time.sleep(1)
            self.test_step_rerun()
            time.sleep(1)
            self.test_step_rollback()
        
        self.generate_report()
        
    def generate_report(self):
        """生成测试报告"""
        print("\n=== 测试报告 ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print(f"\n测试完成时间: {datetime.now().isoformat()}")
        
        # 保存详细报告到文件
        with open("e2e_test_report.json", "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100,
                    "task_id": self.task_id
                },
                "details": self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print("\n详细报告已保存到: e2e_test_report.json")

if __name__ == "__main__":
    runner = E2ETestRunner()
    runner.run_full_pipeline_test()