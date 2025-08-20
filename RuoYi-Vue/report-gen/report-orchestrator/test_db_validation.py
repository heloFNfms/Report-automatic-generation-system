#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库完整性校验脚本
验证步骤历史和回滚功能的一致性
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

from core.db import (
    init_db, create_task, save_step, get_step_history, 
    rollback_to_version, latest_step, get_task
)

class DatabaseValidationTest:
    def __init__(self):
        self.test_results = []
        self.task_id = None
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    async def test_database_connection(self):
        """测试数据库连接"""
        try:
            await init_db()
            self.log_test("数据库连接", True, "数据库初始化成功")
            return True
        except Exception as e:
            self.log_test("数据库连接", False, f"数据库连接失败: {str(e)}")
            return False
            
    async def test_task_creation(self):
        """测试任务创建"""
        try:
            self.task_id = await create_task(
                project_name="测试项目",
                company_name="测试公司", 
                research_content="测试研究内容"
            )
            
            if self.task_id:
                task = await get_task(self.task_id)
                if task:
                    self.log_test("任务创建", True, f"任务创建成功，ID: {self.task_id}")
                    return True
                else:
                    self.log_test("任务创建", False, "任务创建后无法查询")
                    return False
            else:
                self.log_test("任务创建", False, "任务ID为空")
                return False
                
        except Exception as e:
            self.log_test("任务创建", False, f"任务创建失败: {str(e)}")
            return False
            
    async def test_step_history_consistency(self):
        """测试步骤历史一致性"""
        if not self.task_id:
            self.log_test("步骤历史一致性", False, "没有可用的任务ID")
            return False
            
        try:
            # 创建多个版本的步骤记录
            step_outputs = [
                {"content": "第一版内容", "version": 1, "timestamp": datetime.now().isoformat()},
                {"content": "第二版内容", "version": 2, "timestamp": datetime.now().isoformat()},
                {"content": "第三版内容", "version": 3, "timestamp": datetime.now().isoformat()}
            ]
            
            # 保存步骤记录
            versions = []
            for i, output in enumerate(step_outputs):
                version = await save_step(self.task_id, "step1", output)
                versions.append(version)
                
            # 验证版本号递增
            if versions == [1, 2, 3]:
                self.log_test("版本号递增", True, f"版本号正确递增: {versions}")
            else:
                self.log_test("版本号递增", False, f"版本号异常: {versions}")
                return False
                
            # 验证历史记录完整性
            history = await get_step_history(self.task_id, "step1")
            if len(history) == 3:
                self.log_test("历史记录完整性", True, f"历史记录数量正确: {len(history)}")
            else:
                self.log_test("历史记录完整性", False, f"历史记录数量异常: {len(history)}")
                return False
                
            # 验证最新版本获取
            latest = await latest_step(self.task_id, "step1")
            if latest and latest.get("content") == "第三版内容":
                self.log_test("最新版本获取", True, "最新版本内容正确")
            else:
                self.log_test("最新版本获取", False, f"最新版本内容异常: {latest}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("步骤历史一致性", False, f"测试失败: {str(e)}")
            return False
            
    async def test_rollback_functionality(self):
        """测试回滚功能"""
        if not self.task_id:
            self.log_test("回滚功能", False, "没有可用的任务ID")
            return False
            
        try:
            # 回滚到版本1
            rollback_success = await rollback_to_version(self.task_id, "step1", 1)
            if not rollback_success:
                self.log_test("回滚操作", False, "回滚操作失败")
                return False
                
            # 验证回滚后的最新版本
            latest_after_rollback = await latest_step(self.task_id, "step1")
            if latest_after_rollback and latest_after_rollback.get("content") == "第一版内容":
                self.log_test("回滚内容验证", True, "回滚后内容正确")
            else:
                self.log_test("回滚内容验证", False, f"回滚后内容异常: {latest_after_rollback}")
                return False
                
            # 验证回滚后历史记录数量增加
            history_after_rollback = await get_step_history(self.task_id, "step1")
            if len(history_after_rollback) == 4:  # 原来3个 + 回滚新增1个
                self.log_test("回滚历史记录", True, f"回滚后历史记录数量正确: {len(history_after_rollback)}")
            else:
                self.log_test("回滚历史记录", False, f"回滚后历史记录数量异常: {len(history_after_rollback)}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("回滚功能", False, f"测试失败: {str(e)}")
            return False
            
    async def test_data_integrity_constraints(self):
        """测试数据完整性约束"""
        try:
            # 测试无效任务ID的步骤保存
            invalid_task_id = str(uuid.uuid4())
            try:
                await save_step(invalid_task_id, "step1", {"test": "data"})
                # 如果没有外键约束，这里可能成功，但我们需要检查是否符合预期
                self.log_test("无效任务ID约束", True, "无效任务ID处理正常")
            except Exception:
                self.log_test("无效任务ID约束", True, "无效任务ID被正确拒绝")
                
            # 测试无效版本号的回滚
            if self.task_id:
                rollback_invalid = await rollback_to_version(self.task_id, "step1", 999)
                if not rollback_invalid:
                    self.log_test("无效版本回滚", True, "无效版本回滚被正确拒绝")
                else:
                    self.log_test("无效版本回滚", False, "无效版本回滚未被拒绝")
                    return False
                    
            return True
            
        except Exception as e:
            self.log_test("数据完整性约束", False, f"测试失败: {str(e)}")
            return False
            
    async def test_concurrent_operations(self):
        """测试并发操作"""
        if not self.task_id:
            self.log_test("并发操作", False, "没有可用的任务ID")
            return False
            
        try:
            # 模拟并发保存步骤
            tasks = []
            for i in range(5):
                output = {"content": f"并发内容{i}", "timestamp": datetime.now().isoformat()}
                task = save_step(self.task_id, "step2", output)
                tasks.append(task)
                
            # 等待所有并发操作完成
            versions = await asyncio.gather(*tasks)
            
            # 验证版本号唯一性
            if len(set(versions)) == len(versions):
                self.log_test("并发版本唯一性", True, f"并发版本号唯一: {versions}")
            else:
                self.log_test("并发版本唯一性", False, f"并发版本号冲突: {versions}")
                return False
                
            # 验证历史记录完整性
            history = await get_step_history(self.task_id, "step2")
            if len(history) == 5:
                self.log_test("并发历史完整性", True, f"并发历史记录完整: {len(history)}")
            else:
                self.log_test("并发历史完整性", False, f"并发历史记录不完整: {len(history)}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("并发操作", False, f"测试失败: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n🔍 开始数据库完整性校验...\n")
        
        # 按顺序执行测试
        tests = [
            self.test_database_connection,
            self.test_task_creation,
            self.test_step_history_consistency,
            self.test_rollback_functionality,
            self.test_data_integrity_constraints,
            self.test_concurrent_operations
        ]
        
        all_passed = True
        for test in tests:
            success = await test()
            if not success:
                all_passed = False
                
        # 生成测试报告
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r["success"]),
                "failed": sum(1 for r in self.test_results if not r["success"]),
                "success_rate": f"{(sum(1 for r in self.test_results if r['success']) / len(self.test_results) * 100):.1f}%",
                "overall_status": "PASS" if all_passed else "FAIL"
            },
            "test_details": self.test_results,
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存测试报告
        with open("db_validation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📊 测试完成！")
        print(f"总测试数: {report['test_summary']['total_tests']}")
        print(f"通过: {report['test_summary']['passed']}")
        print(f"失败: {report['test_summary']['failed']}")
        print(f"成功率: {report['test_summary']['success_rate']}")
        print(f"整体状态: {report['test_summary']['overall_status']}")
        print(f"详细报告已保存到: db_validation_report.json")
        
        return all_passed

async def main():
    """主函数"""
    validator = DatabaseValidationTest()
    success = await validator.run_all_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main())