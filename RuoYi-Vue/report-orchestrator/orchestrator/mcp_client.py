import httpx
import os


class MCPClient:
    def __init__(self, base_url: str):
        self.base = base_url.rstrip('/')


    async def invoke(self, tool: str, args: dict):
        url = f"{self.base}/invoke"
        payload = {'tool': tool, 'args': args}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json().get('result', r.json())
