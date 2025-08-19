import httpx, os
class MCPClient:
    def __init__(self, base: str):
        self.base = base.rstrip('/')
    async def invoke(self, tool: str, args: dict):
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{self.base}/invoke", json={"tool": tool, "args": args})
            r.raise_for_status()
            data = r.json()
            return data.get("result", data)



