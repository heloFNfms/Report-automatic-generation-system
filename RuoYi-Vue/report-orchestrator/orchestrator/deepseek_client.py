import httpx
import os


class DeepSeekClient:
    def __init__(self, base_url: str, api_key: str):
        self.base = base_url.rstrip('/')
        self.key = api_key


    async def chat_json(self, payload: dict):
# payload expects: {'prompt': str, 'instruction': str}
        url = f"{self.base}/v1/chat/completions" # adapt if DeepSeek path differs
        headers = {'Authorization': f'Bearer {self.key}'} if self.key else {}
        body = {
            'messages': [
            {'role':'system','content':'You are a helpful research assistant.'},
            {'role':'user','content': payload.get('prompt','') + '\n' + payload.get('instruction','')}
            ],
            'max_tokens': 1500
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
            # try to parse content
            choices = data.get('choices') or []
            if choices:
                content = choices[0].get('message', {}).get('content') or choices[0].get('text')
# attempt to parse JSON in content
                try:
                    import json
                    j = json.loads(content)
                    return j
                except Exception:
                    return {'content': content}
            return {'raw': data}