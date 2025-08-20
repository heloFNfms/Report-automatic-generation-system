import asyncio
import aiohttp
import json

async def test_arxiv_search():
    try:
        url = 'http://localhost:8000/invoke'
        payload = {
            "tool": "arxiv_search",
            "args": {
                "query": "AI Test applications",
                "max_results": 3
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                print(f'ArXiv Search Status: {resp.status}')
                response_text = await resp.text()
                print(f'Response: {response_text[:500]}...')
                
                if resp.status == 200:
                    try:
                        result = json.loads(response_text)
                        print(f'Items found: {len(result.get("items", []))}')
                        return True
                    except json.JSONDecodeError as e:
                        print(f'JSON decode error: {e}')
                        return False
                else:
                    return False
    except Exception as e:
        print(f'Error testing arxiv search: {e}')
        return False

if __name__ == '__main__':
    result = asyncio.run(test_arxiv_search())
    print(f'ArXiv Search: {"OK" if result else "FAILED"}')