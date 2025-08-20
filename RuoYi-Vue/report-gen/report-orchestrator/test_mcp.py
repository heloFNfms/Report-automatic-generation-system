import asyncio
import aiohttp

async def test_mcp_connection():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/health') as resp:
                print(f'MCP Health Status: {resp.status}')
                print(f'Response: {await resp.text()}')
                return resp.status == 200
    except Exception as e:
        print(f'Error connecting to MCP: {e}')
        return False

if __name__ == '__main__':
    result = asyncio.run(test_mcp_connection())
    print(f'MCP Connection: {"OK" if result else "FAILED"}')