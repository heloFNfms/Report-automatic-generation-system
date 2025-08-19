import httpx, os, json
class DeepSeekClient:
    def __init__(self, base: str, key: str):
        self.base = base.rstrip('/')
        self.key = key
    async def chat_json(self, system: str, prompt: str, instruction: str):
        headers = {"Authorization": f"Bearer {self.key}"} if self.key else {}
        body = {"messages": [{"role": "system", "content": system},{"role": "user", "content": prompt+"\n"+instruction}],"max_tokens": 2000}
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{self.base}/v1/chat", json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:
            return json.loads(text)
        except Exception:
            return {"content": text}
