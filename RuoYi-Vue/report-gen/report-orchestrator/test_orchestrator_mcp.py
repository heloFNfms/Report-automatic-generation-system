import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.mcp_client import MCPClient

async def test_orchestrator_mcp_call():
    """测试 orchestrator 中的 MCP 调用"""
    try:
        # 使用与 orchestrator 相同的配置
        mcp_base = os.getenv("MCP_BASE", "http://localhost:8000")
        print(f"MCP Base URL: {mcp_base}")
        
        mcp = MCPClient(mcp_base)
        
        # 模拟 orchestrator 中的调用
        query = "AI Test Test AI applications 项目背景与意义"
        print(f"Query: {query}")
        
        result = await mcp.invoke("arxiv_search", {"query": query, "max_results": 8})
        
        print(f"Result type: {type(result)}")
        print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            items = result.get("items", [])
            print(f"Items found: {len(items)}")
            if items:
                print(f"First item keys: {items[0].keys() if isinstance(items[0], dict) else 'Not a dict'}")
                print(f"First item title: {items[0].get('title', 'No title')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"Error in orchestrator MCP call: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(test_orchestrator_mcp_call())
    print(f"Orchestrator MCP Call: {'OK' if result else 'FAILED'}")