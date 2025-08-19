import httpx, os, json, re
class DeepSeekClient:
    def __init__(self, base: str, key: str, model: str = None):
        self.base = base.rstrip('/')
        self.key = key
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    async def chat_json(self, system: str, prompt: str, instruction: str):
        headers = {"Authorization": f"Bearer {self.key}"} if self.key else {}
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt+"\n"+instruction}
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{self.base}/v1/chat/completions", json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
        
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 增强 JSON 解析容错性
        try:
            # 尝试直接解析
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # 尝试提取 JSON 代码块
                json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                
                # 尝试提取花括号内容
                brace_match = re.search(r'{.*}', text, re.DOTALL)
                if brace_match:
                    return json.loads(brace_match.group(0))
                    
            except json.JSONDecodeError:
                pass
            
            # 如果都失败，返回包装的文本内容
            return {"content": text, "parse_error": True}
