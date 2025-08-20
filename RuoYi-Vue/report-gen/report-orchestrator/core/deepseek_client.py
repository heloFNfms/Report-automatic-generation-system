import httpx
import os
import json
import re
import asyncio
import logging
from typing import Dict, Any, Optional, Union
from .deepseek_config import DeepSeekConfig, get_rate_limiter, get_alert_manager

logger = logging.getLogger(__name__)

class DeepSeekClient:
    """增强的DeepSeek客户端，支持重试、限流和告警"""
    
    def __init__(self, base: str = None, key: str = None, model: str = None, config: DeepSeekConfig = None):
        if config:
            self.config = config
        else:
            # 兼容旧的初始化方式
            self.config = DeepSeekConfig(
                api_key=key or os.getenv("DEEPSEEK_API_KEY", ""),
                base_url=(base or os.getenv("DEEPSEEK_BASE", "https://api.deepseek.com")).rstrip('/'),
                model=model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            )
        
        self.config.validate()
        self.rate_limiter = get_rate_limiter(self.config)
        self.alert_manager = get_alert_manager()
        
        # 兼容属性
        self.base = self.config.base_url
        self.key = self.config.api_key
        self.model = self.config.model
    
    @classmethod
    def from_env(cls) -> 'DeepSeekClient':
        """从环境变量创建客户端"""
        config = DeepSeekConfig.from_env()
        return cls(config=config)
    
    async def chat_json(self, system: str, prompt: str, instruction: str = "") -> Dict[str, Any]:
        """发送聊天请求并返回JSON响应"""
        return await self._make_request(system, prompt, instruction)
    
    async def chat_async(self, prompt: str, system: str = "") -> str:
        """发送聊天请求并返回文本响应"""
        result = await self._make_request(system, prompt)
        if isinstance(result, dict):
            if "content" in result:
                return result["content"]
            return json.dumps(result, ensure_ascii=False)
        return str(result)
    
    async def _make_request(self, system: str, prompt: str, instruction: str = "") -> Union[Dict[str, Any], str]:
        """执行API请求，包含重试和错误处理"""
        # 速率限制检查
        if not await self.rate_limiter.acquire():
            wait_time = self.rate_limiter.get_wait_time()
            logger.warning(f"Rate limit exceeded, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
            
            # 再次尝试获取许可
            if not await self.rate_limiter.acquire():
                raise Exception("Rate limit exceeded and wait time expired")
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                result = await self._execute_request(system, prompt, instruction)
                self.alert_manager.record_success()
                return result
                
            except Exception as e:
                last_exception = e
                self.alert_manager.record_error(e, {
                    "attempt": attempt + 1,
                    "max_retries": self.config.max_retries,
                    "system_length": len(system),
                    "prompt_length": len(prompt)
                })
                
                if attempt < self.config.max_retries:
                    # 计算退避延迟
                    delay = self.config.retry_delay * (self.config.retry_backoff ** attempt)
                    
                    # 对401错误使用更长的延迟
                    if self._is_auth_error(e):
                        delay *= 2
                        logger.warning(f"Authentication error, using extended delay: {delay:.2f}s")
                    
                    logger.info(f"Request failed (attempt {attempt + 1}/{self.config.max_retries + 1}), retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.config.max_retries + 1} attempts: {e}")
        
        # 所有重试都失败了
        raise last_exception
    
    async def _execute_request(self, system: str, prompt: str, instruction: str = "") -> Union[Dict[str, Any], str]:
        """执行单次API请求"""
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        
        # 构建消息
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        
        user_content = prompt
        if instruction:
            user_content += "\n" + instruction
        messages.append({"role": "user", "content": user_content})
        
        body = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.base_url}/v1/chat/completions", 
                json=body, 
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
        
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 尝试解析JSON
        return self._parse_response(text)
    
    def _parse_response(self, text: str) -> Union[Dict[str, Any], str]:
        """解析响应文本，尝试提取JSON"""
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
            
            # 如果都失败，返回原始文本
            return text
    
    def _is_auth_error(self, error: Exception) -> bool:
        """判断是否为认证错误"""
        if hasattr(error, 'response'):
            return getattr(error.response, 'status_code', 0) == 401
        
        error_str = str(error).lower()
        return '401' in error_str or 'unauthorized' in error_str or 'authentication' in error_str
    
    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "config": {
                "base_url": self.config.base_url,
                "model": self.config.model,
                "max_retries": self.config.max_retries,
                "timeout": self.config.timeout
            },
            "rate_limiter": {
                "per_minute": self.rate_limiter.per_minute,
                "per_hour": self.rate_limiter.per_hour,
                "current_minute_requests": len(self.rate_limiter.minute_requests),
                "current_hour_requests": len(self.rate_limiter.hour_requests)
            },
            "alerts": self.alert_manager.get_stats()
        }
