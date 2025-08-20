import sys
sys.path.append('report-orchestrator')

from core.export import export_manager
import asyncio

async def test_pdf_export():
    # 简单的测试数据
    test_data = {
        'task_id': 'test123',
        'project_name': 'Test Project',
        'company_name': 'Test Company',
        'research_content': 'Test Content',
        'final_report': 'This is a test report content.'
    }
    
    print("Testing PDF export...")
    result = await export_manager.export_to_pdf(test_data)
    print("PDF export result:", result)

if __name__ == "__main__":
    asyncio.run(test_pdf_export())