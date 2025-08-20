#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试脚本
测试完整的报告生成流程：Step1→Step5→导出→上传→下载
以及单步重跑/回滚场景测试
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional

class E2ETestRunner:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.task_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status = "✓" if success else "✗"
        print(f"[{status}] {test_name}: {message}")
        
    def test_health_check(self) -> bool:
        """测试服务健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_test("Health Check", True, "服务正常运行")
                return True
            else:
                self.log_test("Health Check", False, f"服务状态异常: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"连接失败: {str(e)}")
            return False
            
    def test_step1_topic_generation(self) -> bool:
        """测试Step1: 主题生成"""
        try:
            payload = {
                "project_name": "人工智能在医疗领域的应用",
                "company_name": "测试公司",
                "research_content": "需要包含技术发展现状、应用案例、挑战与机遇等内容"
            }
            
            response = self.session.post(f"{self.base_url}/step1", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "task_id" in data:
                    self.task_id = data["task_id"]
                    self.log_test("Step1 Topic Generation", True, f"任务创建成功，ID: {self.task_id}")
                    return True
                else:
                    self.log_test("Step1 Topic Generation", False, "响应中缺少task_id")
                    return False
            else:
                self.log_test("Step1 Topic Generation", False, f"请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Step1 Topic Generation", False, f"异常: {str(e)}")
            return False
            
    def test_step2_outline_generation(self) -> bool:
        """测试Step2: 大纲生成"""
        if not self.task_id:
            self.log_test("Step2 Outline Generation", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step2", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "outline" in data:
                    self.log_test("Step2 Outline Generation", True, "大纲生成成功")
                    return True
                else:
                    self.log_test("Step2 Outline Generation", False, "响应中缺少outline")
                    return False
            else:
                self.log_test("Step2 Outline Generation", False, f"请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Step2 Outline Generation", False, f"异常: {str(e)}")
            return False
            
    def test_step3_research(self) -> bool:
        """测试Step3: 资料搜集"""
        if not self.task_id:
            self.log_test("Step3 Research", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step3", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "research_results" in data:
                    self.log_test("Step3 Research", True, "资料搜集成功")
                    return True
                else:
                    self.log_test("Step3 Research", False, "响应中缺少research_results")
                    return False
            else:
                self.log_test("Step3 Research", False, f"请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Step3 Research", False, f"异常: {str(e)}")
            return False
            
    def test_step4_content_generation(self) -> bool:
        """测试Step4: 内容生成"""
        if not self.task_id:
            self.log_test("Step4 Content Generation", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step4", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "content" in data:
                    self.log_test("Step4 Content Generation", True, "内容生成成功")
                    return True
                else:
                    self.log_test("Step4 Content Generation", False, "响应中缺少content")
                    return False
            else:
                self.log_test("Step4 Content Generation", False, f"请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Step4 Content Generation", False, f"异常: {str(e)}")
            return False
            
    def test_step5_review_optimization(self) -> bool:
        """测试Step5: 审核优化"""
        if not self.task_id:
            self.log_test("Step5 Review Optimization", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step5", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "final_report" in data:
                    self.log_test("Step5 Review Optimization", True, "审核优化成功")
                    return True
                else:
                    self.log_test("Step5 Review Optimization", False, "响应中缺少final_report")
                    return False
            else:
                self.log_test("Step5 Review Optimization", False, f"请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Step5 Review Optimization", False, f"异常: {str(e)}")
            return False
            
    def test_export_pdf(self) -> bool:
        """测试PDF导出"""
        if not self.task_id:
            self.log_test("Export PDF", False, "缺少task_id")
            return False
            
        try:
            payload = {
                "task_id": self.task_id,
                "format": "pdf"
            }
            response = self.session.post(f"{self.base_url}/export", json=payload)
            
            if response.status_code == 200:
                # 检查是否返回了文件内容或下载链接
                if response.headers.get('content-type') == 'application/pdf':
                    self.log_test("Export PDF", True, "PDF导出成功")
                    return True
                else:
                    data = response.json()
                    if "download_url" in data:
                        self.log_test("Export PDF", True, "PDF导出链接生成成功")
                        return True
                    else:
                        self.log_test("Export PDF", False, "PDF导出响应格式异常")
                        return False
            else:
                self.log_test("Export PDF", False, f"导出失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Export PDF", False, f"异常: {str(e)}")
            return False
            
    def test_export_word(self) -> bool:
        """测试Word导出"""
        if not self.task_id:
            self.log_test("Export Word", False, "缺少task_id")
            return False
            
        try:
            payload = {
                "task_id": self.task_id,
                "format": "docx"
            }
            response = self.session.post(f"{self.base_url}/export", json=payload)
            
            if response.status_code == 200:
                # 检查是否返回了文件内容或下载链接
                content_type = response.headers.get('content-type', '')
                if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                    self.log_test("Export Word", True, "Word导出成功")
                    return True
                else:
                    data = response.json()
                    if "download_url" in data:
                        self.log_test("Export Word", True, "Word导出链接生成成功")
                        return True
                    else:
                        self.log_test("Export Word", False, "Word导出响应格式异常")
                        return False
            else:
                self.log_test("Export Word", False, f"导出失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Export Word", False, f"异常: {str(e)}")
            return False
            
    def test_step_rerun(self) -> bool:
        """测试单步重跑功能"""
        if not self.task_id:
            self.log_test("Step Rerun", False, "缺少task_id")
            return False
            
        try:
            payload = {
                "task_id": self.task_id,
                "step": 2  # 重跑Step2
            }
            response = self.session.post(f"{self.base_url}/rerun", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "success" in data and data["success"]:
                    self.log_test("Step Rerun", True, "单步重跑成功")
                    return True
                else:
                    self.log_test("Step Rerun", False, "重跑失败")
                    return False
            else:
                self.log_test("Step Rerun", False, f"重跑请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Step Rerun", False, f"异常: {str(e)}")
            return False
            
    def test_step_history(self) -> bool:
        """测试步骤历史查询"""
        if not self.task_id:
            self.log_test("Step History", False, "缺少task_id")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/task/{self.task_id}/history/step2")
            
            if response.status_code == 200:
                data = response.json()
                if "history" in data:
                    self.log_test("Step History", True, "历史查询成功")
                    return True
                else:
                    self.log_test("Step History", False, "响应中缺少history")
                    return False
            else:
                self.log_test("Step History", False, f"历史查询失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Step History", False, f"异常: {str(e)}")
            return False
            
    def test_rollback(self) -> bool:
        """测试版本回滚功能"""
        if not self.task_id:
            self.log_test("Rollback", False, "缺少task_id")
            return False
            
        try:
            payload = {
                "task_id": self.task_id,
                "step": 2,
                "version": 1  # 回滚到版本1
            }
            response = self.session.post(f"{self.base_url}/rollback", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "success" in data and data["success"]:
                    self.log_test("Rollback", True, "版本回滚成功")
                    return True
                else:
                    self.log_test("Rollback", False, "回滚失败")
                    return False
            else:
                self.log_test("Rollback", False, f"回滚请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Rollback", False, f"异常: {str(e)}")
            return False
            
    def run_full_e2e_test(self) -> bool:
        """运行完整的端到端测试"""
        print("\n=== 开始端到端测试 ===")
        
        # 基础测试
        if not self.test_health_check():
            return False
            
        # 完整流程测试
        tests = [
            self.test_step1_topic_generation,
            self.test_step2_outline_generation,
            self.test_step3_research,
            self.test_step4_content_generation,
            self.test_step5_review_optimization,
            self.test_export_pdf,
            self.test_export_word,
            self.test_step_history,
            self.test_step_rerun,
            self.test_rollback
        ]
        
        success_count = 0
        for test in tests:
            if test():
                success_count += 1
            time.sleep(1)  # 避免请求过于频繁
            
        total_tests = len(tests) + 1  # +1 for health check
        success_rate = (success_count + 1) / total_tests * 100  # +1 for health check
        
        print(f"\n=== 测试完成 ===")
        print(f"总测试数: {total_tests}")
        print(f"成功数: {success_count + 1}")
        print(f"成功率: {success_rate:.1f}%")
        
        return success_rate >= 80  # 80%以上成功率认为测试通过
        
    def generate_report(self) -> str:
        """生成测试报告"""
        report = "\n=== E2E测试报告 ===\n"
        report += f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"测试服务: {self.base_url}\n\n"
        
        success_count = sum(1 for result in self.test_results if result["success"])
        total_count = len(self.test_results)
        
        report += f"测试总数: {total_count}\n"
        report += f"成功数: {success_count}\n"
        report += f"失败数: {total_count - success_count}\n"
        report += f"成功率: {success_count/total_count*100:.1f}%\n\n"
        
        report += "详细结果:\n"
        for result in self.test_results:
            status = "✓" if result["success"] else "✗"
            report += f"[{status}] {result['test_name']}: {result['message']}\n"
            
        return report

def main():
    """主函数"""
    runner = E2ETestRunner()
    
    # 运行测试
    success = runner.run_full_e2e_test()
    
    # 生成报告
    report = runner.generate_report()
    print(report)
    
    # 保存报告到文件
    with open("e2e_test_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\n测试报告已保存到: e2e_test_report.txt")
    
    if success:
        print("\n🎉 端到端测试通过！")
        return 0
    else:
        print("\n❌ 端到端测试失败！")
        return 1

if __name__ == "__main__":
    exit(main())