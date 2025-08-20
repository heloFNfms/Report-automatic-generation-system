#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的数据库完整性校验脚本
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

class SimpleDBTest:
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
        
    async def test_basic_operations(self):
        """测试基础操作"""
        try:
            # 1. 数据库连接
            await init_db()
            self.log_test("数据库连接", True, "数据库初始化成功")
            
            # 2. 任务创建
            self.task_id = await create_task(
                project_name="测试项目",
                company_name="测试公司", 
                research_content="测试研究内容"
            )
            
            if self.task_id:
                task = await get_task(self.task_id)
                if task:
                    self.log_test("任务创建", True, f"任务创建成功，ID: {self.task_id}")
                else:
                    self.log_test("任务创建", False, "任务创建后无法查询")
                    return False
            else:
                self.log_test("任务创建", False, "任务ID为空")
                return False
                
            # 3. 步骤保存（简化版本，不使用复杂的datetime）
            step_output = {"content": "测试内容", "version": 1}
            version = await save_step(self.task_id, "step1", step_output)
            if version == 1:
                self.log_test("步骤保存", True, f"步骤保存成功，版本: {version}")
            else:
                self.log_test("步骤保存", False, f"步骤保存版本异常: {version}")
                return False
                
            # 4. 历史查询
            history = await get_step_history(self.task_id, "step1")
            if len(history) >= 1:
                self.log_test("历史查询", True, f"历史记录查询成功，数量: {len(history)}")
            else:
                self.log_test("历史查询", False, "历史记录查询失败")
                return False
                
            # 5. 最新版本获取
            latest = await latest_step(self.task_id, "step1")
            if latest and latest.get("content") == "测试内容":
                self.log_test("最新版本获取", True, "最新版本获取成功")
            else:
                self.log_test("最新版本获取", False, f"最新版本获取失败: {latest}")
                return False
                
            # 6. 多版本保存
            for i in range(2, 4):
                step_output = {"content": f"测试内容{i}", "version": i}
                version = await save_step(self.task_id, "step1", step_output)
                if version != i:
                    self.log_test("多版本保存", False, f"版本号不匹配: 期望{i}, 实际{version}")
                    return False
                    
            self.log_test("多版本保存", True, "多版本保存成功")
            
            # 7. 回滚测试
            rollback_success = await rollback_to_version(self.task_id, "step1", 1)
            if rollback_success:
                latest_after_rollback = await latest_step(self.task_id, "step1")
                if latest_after_rollback and latest_after_rollback.get("content") == "测试内容":
                    self.log_test("回滚功能", True, "回滚功能正常")
                else:
                    self.log_test("回滚功能", False, f"回滚后内容不正确: {latest_after_rollback}")
                    return False
            else:
                self.log_test("回滚功能", False, "回滚操作失败")
                return False
                
            # 8. 权限校验（无效版本回滚）
            invalid_rollback = await rollback_to_version(self.task_id, "step1", 999)
            if not invalid_rollback:
                self.log_test("权限校验", True, "无效版本回滚被正确拒绝")
            else:
                self.log_test("权限校验", False, "无效版本回滚未被拒绝")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("基础操作测试", False, f"测试失败: {str(e)}")
            return False
            
    async def run_tests(self):
        """运行测试"""
        print("\n🔍 开始简化数据库校验...\n")
        
        success = await self.test_basic_operations()
        
        # 生成测试报告
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r["success"]),
                "failed": sum(1 for r in self.test_results if not r["success"]),
                "success_rate": f"{(sum(1 for r in self.test_results if r['success']) / len(self.test_results) * 100):.1f}%" if self.test_results else "0%",
                "overall_status": "PASS" if success else "FAIL"
            },
            "test_details": self.test_results,
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存测试报告
        with open("simple_db_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📊 测试完成！")
        print(f"总测试数: {report['test_summary']['total_tests']}")
        print(f"通过: {report['test_summary']['passed']}")
        print(f"失败: {report['test_summary']['failed']}")
        print(f"成功率: {report['test_summary']['success_rate']}")
        print(f"整体状态: {report['test_summary']['overall_status']}")
        print(f"详细报告已保存到: simple_db_report.json")
        
        return success

async def main():
    """主函数"""
    tester = SimpleDBTest()
    success = await tester.run_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main())