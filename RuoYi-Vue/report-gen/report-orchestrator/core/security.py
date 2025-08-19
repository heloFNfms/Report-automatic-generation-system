import time
from typing import Dict, List, Optional
from fastapi import HTTPException, Request
from collections import defaultdict, deque
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, client_id: str) -> bool:
        """检查是否允许请求"""
        async with self.lock:
            now = time.time()
            window_start = now - self.window_seconds
            
            # 清理过期请求
            client_requests = self.requests[client_id]
            while client_requests and client_requests[0] < window_start:
                client_requests.popleft()
            
            # 检查是否超过限制
            if len(client_requests) >= self.max_requests:
                return False
            
            # 记录新请求
            client_requests.append(now)
            return True
    
    def get_remaining_requests(self, client_id: str) -> int:
        """获取剩余请求数"""
        return max(0, self.max_requests - len(self.requests[client_id]))

class ConcurrencyLimiter:
    """并发限制器"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests: Dict[str, int] = defaultdict(int)
        self.lock = asyncio.Lock()
    
    async def acquire(self, client_id: str) -> bool:
        """获取并发许可"""
        await self.semaphore.acquire()
        async with self.lock:
            self.active_requests[client_id] += 1
        return True
    
    async def release(self, client_id: str):
        """释放并发许可"""
        async with self.lock:
            self.active_requests[client_id] = max(0, self.active_requests[client_id] - 1)
        self.semaphore.release()

class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=3600)  # 每小时100次
        self.concurrency_limiter = ConcurrencyLimiter(max_concurrent=10)  # 最大10个并发
        self.whitelist: List[str] = self._load_whitelist()
        self.blacklist: List[str] = self._load_blacklist()
    
    def _load_whitelist(self) -> List[str]:
        """加载白名单"""
        import os
        whitelist_str = os.getenv('API_WHITELIST', '')
        if whitelist_str:
            return [ip.strip() for ip in whitelist_str.split(',') if ip.strip()]
        return ['127.0.0.1', 'localhost']  # 默认白名单
    
    def _load_blacklist(self) -> List[str]:
        """加载黑名单"""
        import os
        blacklist_str = os.getenv('API_BLACKLIST', '')
        if blacklist_str:
            return [ip.strip() for ip in blacklist_str.split(',') if ip.strip()]
        return []
    
    def get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用 X-Forwarded-For 头
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # 使用客户端IP
        if request.client:
            return request.client.host
        
        return 'unknown'
    
    def is_whitelisted(self, client_ip: str) -> bool:
        """检查是否在白名单中"""
        return client_ip in self.whitelist or any(client_ip.startswith(prefix) for prefix in self.whitelist)
    
    def is_blacklisted(self, client_ip: str) -> bool:
        """检查是否在黑名单中"""
        return client_ip in self.blacklist or any(client_ip.startswith(prefix) for prefix in self.blacklist)
    
    async def check_access(self, request: Request) -> bool:
        """检查访问权限"""
        client_id = self.get_client_id(request)
        
        # 检查黑名单
        if self.is_blacklisted(client_id):
            raise HTTPException(status_code=403, detail="Access denied: IP blacklisted")
        
        # 如果有白名单且不在白名单中，拒绝访问
        if self.whitelist and not self.is_whitelisted(client_id):
            raise HTTPException(status_code=403, detail="Access denied: IP not whitelisted")
        
        # 检查速率限制
        if not await self.rate_limiter.is_allowed(client_id):
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded",
                headers={"Retry-After": "3600"}
            )
        
        return True
    
    async def acquire_concurrency(self, request: Request):
        """获取并发许可"""
        client_id = self.get_client_id(request)
        await self.concurrency_limiter.acquire(client_id)
    
    async def release_concurrency(self, request: Request):
        """释放并发许可"""
        client_id = self.get_client_id(request)
        await self.concurrency_limiter.release(client_id)

# 全局安全管理器实例
security_manager = SecurityManager()