#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化端到端测试脚本
用于验证报告生成系统的基础功能
"""

import requests
import json
import time
from datetime import datetime

class SimpleE2ETestRunner:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
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
        """测试健康检查接口"""
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
            
    def test_api_docs(self):
        """测试API文档访问"""
        try:
            response = self.session.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                self.log_test("API文档访问", True, "文档页面可访问")
                return True
            else:
                self.log_test("API文档访问", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API文档访问", False, f"访问失败: {str(e)}")
            return False
            
    def test_step1_basic(self):
        """测试Step1基本功能"""
        try:
            payload = {
                "project_name": "人工智能在医疗领域的应用研究",
                "company_name": "测试公司",
                "research_content": "分析AI在医疗诊断、药物研发等方面的应用现状和发展趋势"
            }
            response = self.session.post(f"{self.base_url}/step1", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "task_id" in data:
                    self.task_id = data["task_id"]
                    self.log_test("Step1基本功能", True, f"主题生成成功，任务ID: {self.task_id}")
                    return True
                else:
                    self.log_test("Step1基本功能", False, "响应中缺少task_id")
                    return False
            else:
                self.log_test("Step1基本功能", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_test("Step1基本功能", False, f"请求失败: {str(e)}")
            return False
            
    def test_task_query(self):
        """测试任务查询功能"""
        if not hasattr(self, 'task_id'):
            self.log_test("任务查询", False, "没有可用的task_id")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/task/{self.task_id}")
            if response.status_code == 200:
                data = response.json()
                self.log_test("任务查询", True, f"任务信息获取成功")
                return True
            else:
                self.log_test("任务查询", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_test("任务查询", False, f"查询失败: {str(e)}")
            return False
            
    def test_step2_error_handling(self):
        """测试Step2错误处理"""
        try:
            payload = {
                "task_id": "test_task_id"
            }
            response = self.session.post(f"{self.base_url}/step2", json=payload)
            
            # 期望这里会有错误，因为task_id不存在
            if response.status_code in [400, 404, 422]:
                self.log_test("Step2错误处理", True, f"正确返回错误状态码: {response.status_code}")
                return True
            elif response.status_code == 401:
                self.log_test("Step2错误处理", False, f"API认证失败: {response.status_code}")
                return False
            else:
                self.log_test("Step2错误处理", False, f"意外状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Step2错误处理", False, f"请求失败: {str(e)}")
            return False
            
    def test_cache_api(self):
        """测试缓存API"""
        try:
            response = self.session.get(f"{self.base_url}/api/cache/stats")
            if response.status_code == 200:
                data = response.json()
                self.log_test("缓存API访问", True, "缓存统计信息获取成功")
                return True
            else:
                self.log_test("缓存API访问", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_test("缓存API访问", False, f"访问失败: {str(e)}")
            return False
            
    def test_export_params(self):
        """测试导出参数验证"""
        try:
            payload = {
                "task_id": "invalid_task_id",
                "format": "pdf"
            }
            response = self.session.post(f"{self.base_url}/export", json=payload)
            
            # 期望返回错误，因为task_id无效
            if response.status_code in [400, 404, 422]:
                self.log_test("导出参数验证", True, f"正确验证无效参数: {response.status_code}")
                return True
            else:
                self.log_test("导出参数验证", False, f"参数验证失败: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("导出参数验证", False, f"请求失败: {str(e)}")
            return False
            
    def run_all_tests(self):
        """运行所有测试"""
        print("\n=== 简化端到端测试开始 ===")
        print(f"测试目标: {self.base_url}")
        print(f"开始时间: {datetime.now().isoformat()}")
        print()
        
        # 按顺序执行测试
        tests = [
            self.test_health_check,
            self.test_api_docs,
            self.test_step1_basic,
            self.test_task_query,
            self.test_step2_error_handling,
            self.test_cache_api,
            self.test_export_params
        ]
        
        for test in tests:
            test()
            time.sleep(0.5)  # 短暂延迟
            
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
        with open("simple_test_report.json", "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "details": self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print("\n详细报告已保存到: simple_test_report.json")

if __name__ == "__main__":
    runner = SimpleE2ETestRunner()
    runner.run_all_tests()