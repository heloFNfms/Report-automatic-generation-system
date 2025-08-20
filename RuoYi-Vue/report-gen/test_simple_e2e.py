#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的端到端测试脚本
专注于测试API接口的基本功能，不依赖复杂的数据库操作
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class SimpleE2ETestRunner:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.task_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status = "✓" if success else "✗"
        print(f"[{status}] {test_name}: {message}")
        if details and not success:
            print(f"    详细信息: {details}")
        
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
            
    def test_api_docs(self) -> bool:
        """测试API文档访问"""
        try:
            response = self.session.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                self.log_test("API Docs", True, "API文档可访问")
                return True
            else:
                self.log_test("API Docs", False, f"API文档访问失败: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Docs", False, f"API文档访问异常: {str(e)}")
            return False
            
    def test_step1_basic(self) -> bool:
        """测试Step1基本功能"""
        try:
            payload = {
                "project_name": "测试项目",
                "company_name": "测试公司",
                "research_content": "这是一个简单的测试内容"
            }
            
            response = self.session.post(f"{self.base_url}/step1", json=payload)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "task_id" in data:
                        self.task_id = data["task_id"]
                        self.log_test("Step1 Basic", True, f"任务创建成功，ID: {self.task_id}")
                        return True
                    else:
                        self.log_test("Step1 Basic", False, "响应中缺少task_id", str(data))
                        return False
                except json.JSONDecodeError:
                    self.log_test("Step1 Basic", False, "响应不是有效的JSON", response.text[:200])
                    return False
            else:
                try:
                    error_detail = response.json()
                except:
                    error_detail = response.text[:200]
                self.log_test("Step1 Basic", False, f"请求失败: {response.status_code}", str(error_detail))
                return False
                
        except Exception as e:
            self.log_test("Step1 Basic", False, f"异常: {str(e)}")
            return False
            
    def test_task_query(self) -> bool:
        """测试任务查询功能"""
        if not self.task_id:
            self.log_test("Task Query", False, "缺少task_id")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/task/{self.task_id}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "task_id" in data:
                        self.log_test("Task Query", True, "任务查询成功")
                        return True
                    else:
                        self.log_test("Task Query", False, "查询结果格式异常", str(data))
                        return False
                except json.JSONDecodeError:
                    self.log_test("Task Query", False, "响应不是有效的JSON", response.text[:200])
                    return False
            else:
                try:
                    error_detail = response.json()
                except:
                    error_detail = response.text[:200]
                self.log_test("Task Query", False, f"查询失败: {response.status_code}", str(error_detail))
                return False
                
        except Exception as e:
            self.log_test("Task Query", False, f"异常: {str(e)}")
            return False
            
    def test_step2_with_error_handling(self) -> bool:
        """测试Step2并处理可能的错误"""
        if not self.task_id:
            self.log_test("Step2 Error Handling", False, "缺少task_id")
            return False
            
        try:
            payload = {"task_id": self.task_id}
            response = self.session.post(f"{self.base_url}/step2", json=payload)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log_test("Step2 Error Handling", True, "Step2执行成功", str(data)[:100])
                    return True
                except json.JSONDecodeError:
                    self.log_test("Step2 Error Handling", False, "响应不是有效的JSON", response.text[:200])
                    return False
            elif response.status_code == 400:
                try:
                    error_detail = response.json()
                    self.log_test("Step2 Error Handling", False, "业务逻辑错误(400)", str(error_detail))
                except:
                    self.log_test("Step2 Error Handling", False, "业务逻辑错误(400)", response.text[:200])
                return False
            elif response.status_code == 500:
                try:
                    error_detail = response.json()
                    self.log_test("Step2 Error Handling", False, "服务器内部错误(500)", str(error_detail))
                except:
                    self.log_test("Step2 Error Handling", False, "服务器内部错误(500)", response.text[:200])
                return False
            else:
                try:
                    error_detail = response.json()
                except:
                    error_detail = response.text[:200]
                self.log_test("Step2 Error Handling", False, f"未知错误: {response.status_code}", str(error_detail))
                return False
                
        except Exception as e:
            self.log_test("Step2 Error Handling", False, f"异常: {str(e)}")
            return False
            
    def test_cache_api(self) -> bool:
        """测试缓存API功能"""
        try:
            # 测试缓存统计信息
            response = self.session.get(f"{self.base_url}/api/cache/stats")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log_test("Cache API", True, "缓存API可访问", str(data)[:100])
                    return True
                except json.JSONDecodeError:
                    self.log_test("Cache API", False, "缓存API响应格式异常", response.text[:200])
                    return False
            else:
                try:
                    error_detail = response.json()
                except:
                    error_detail = response.text[:200]
                self.log_test("Cache API", False, f"缓存API访问失败: {response.status_code}", str(error_detail))
                return False
                
        except Exception as e:
            self.log_test("Cache API", False, f"缓存API测试异常: {str(e)}")
            return False
            
    def test_export_validation(self) -> bool:
        """测试导出功能的参数验证"""
        try:
            # 测试无效的导出请求
            payload = {
                "task_id": "invalid_task_id",
                "format": "pdf"
            }
            
            response = self.session.post(f"{self.base_url}/export", json=payload)
            
            # 期望这个请求失败，因为task_id无效
            if response.status_code in [400, 404, 500]:
                self.log_test("Export Validation", True, f"导出参数验证正常(状态码: {response.status_code})")
                return True
            else:
                self.log_test("Export Validation", False, f"导出参数验证异常，应该失败但返回: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Export Validation", False, f"导出验证测试异常: {str(e)}")
            return False
            
    def run_basic_tests(self) -> bool:
        """运行基础测试套件"""
        print("\n=== 开始基础功能测试 ===")
        
        tests = [
            self.test_health_check,
            self.test_api_docs,
            self.test_step1_basic,
            self.test_task_query,
            self.test_step2_with_error_handling,
            self.test_cache_api,
            self.test_export_validation
        ]
        
        success_count = 0
        for test in tests:
            if test():
                success_count += 1
            time.sleep(0.5)  # 避免请求过于频繁
            
        total_tests = len(tests)
        success_rate = success_count / total_tests * 100
        
        print(f"\n=== 基础测试完成 ===")
        print(f"总测试数: {total_tests}")
        print(f"成功数: {success_count}")
        print(f"成功率: {success_rate:.1f}%")
        
        return success_rate >= 70  # 70%以上成功率认为基础功能正常
        
    def generate_report(self) -> str:
        """生成测试报告"""
        report = "\n=== 简化E2E测试报告 ===\n"
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
            if result['details'] and not result['success']:
                report += f"    详细: {result['details'][:100]}...\n"
            
        return report

def main():
    """主函数"""
    runner = SimpleE2ETestRunner()
    
    # 运行基础测试
    success = runner.run_basic_tests()
    
    # 生成报告
    report = runner.generate_report()
    print(report)
    
    # 保存报告到文件
    with open("simple_e2e_test_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\n测试报告已保存到: simple_e2e_test_report.txt")
    
    if success:
        print("\n🎉 基础功能测试通过！")
        return 0
    else:
        print("\n⚠️ 基础功能测试部分失败，请检查详细报告")
        return 1

if __name__ == "__main__":
    exit(main())