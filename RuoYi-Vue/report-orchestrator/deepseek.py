import os, httpx

BASE = os.getenv("DEEPSEEK_BASE_URL")
KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

async def ask_deepseek(system: str, user: str) -> str:
    url = f"{BASE}/v1/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.3
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload, headers={"Authorization": f"Bearer {KEY}"})
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
