import os
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class DeepSeekConfig:
    """DeepSeek API配置"""
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    timeout: float = 60.0
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 3600
    
    @classmethod
    def from_env(cls) -> 'DeepSeekConfig':
        """从环境变量创建配置"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE", "https://api.deepseek.com"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            max_retries=int(os.getenv("DEEPSEEK_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("DEEPSEEK_RETRY_DELAY", "1.0")),
            retry_backoff=float(os.getenv("DEEPSEEK_RETRY_BACKOFF", "2.0")),
            timeout=float(os.getenv("DEEPSEEK_TIMEOUT", "60.0")),
            rate_limit_per_minute=int(os.getenv("DEEPSEEK_RATE_LIMIT_PER_MINUTE", "60")),
            rate_limit_per_hour=int(os.getenv("DEEPSEEK_RATE_LIMIT_PER_HOUR", "3600"))
        )
    
    def validate(self) -> None:
        """验证配置"""
        if not self.api_key:
            raise ValueError("API key is required")
        if not self.base_url:
            raise ValueError("Base URL is required")
        if not self.model:
            raise ValueError("Model is required")
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("Retry delay must be non-negative")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, per_minute: int = 60, per_hour: int = 3600):
        self.per_minute = per_minute
        self.per_hour = per_hour
        self.minute_requests = []
        self.hour_requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """获取请求许可"""
        async with self._lock:
            now = datetime.now()
            
            # 清理过期的请求记录
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            
            self.minute_requests = [req for req in self.minute_requests if req > minute_ago]
            self.hour_requests = [req for req in self.hour_requests if req > hour_ago]
            
            # 检查是否超过限制
            if len(self.minute_requests) >= self.per_minute:
                logger.warning(f"Rate limit exceeded: {len(self.minute_requests)} requests in last minute")
                return False
            
            if len(self.hour_requests) >= self.per_hour:
                logger.warning(f"Rate limit exceeded: {len(self.hour_requests)} requests in last hour")
                return False
            
            # 记录请求
            self.minute_requests.append(now)
            self.hour_requests.append(now)
            return True
    
    def get_wait_time(self) -> float:
        """获取需要等待的时间（秒）"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        # 清理过期记录
        recent_minute = [req for req in self.minute_requests if req > minute_ago]
        recent_hour = [req for req in self.hour_requests if req > hour_ago]
        
        if len(recent_minute) >= self.per_minute:
            # 等到最早的请求过期
            oldest_in_minute = min(recent_minute)
            wait_time = (oldest_in_minute + timedelta(minutes=1) - now).total_seconds()
            return max(0, wait_time)
        
        if len(recent_hour) >= self.per_hour:
            # 等到最早的请求过期
            oldest_in_hour = min(recent_hour)
            wait_time = (oldest_in_hour + timedelta(hours=1) - now).total_seconds()
            return max(0, wait_time)
        
        return 0

class DeepSeekAlert:
    """DeepSeek告警管理"""
    
    def __init__(self):
        self.error_count = 0
        self.last_error_time = None
        self.consecutive_errors = 0
        self.alert_threshold = 5
        self.alert_cooldown = 300  # 5分钟
        self.last_alert_time = None
    
    def record_error(self, error: Exception, context: Dict[str, Any] = None):
        """记录错误"""
        self.error_count += 1
        self.consecutive_errors += 1
        self.last_error_time = datetime.now()
        
        logger.error(f"DeepSeek API error #{self.error_count}: {error}", extra={
            "error_type": type(error).__name__,
            "consecutive_errors": self.consecutive_errors,
            "context": context or {}
        })
        
        # 检查是否需要发送告警
        if self._should_alert():
            self._send_alert(error, context)
    
    def record_success(self):
        """记录成功请求"""
        self.consecutive_errors = 0
    
    def _should_alert(self) -> bool:
        """判断是否应该发送告警"""
        if self.consecutive_errors < self.alert_threshold:
            return False
        
        if self.last_alert_time is None:
            return True
        
        time_since_last_alert = (datetime.now() - self.last_alert_time).total_seconds()
        return time_since_last_alert >= self.alert_cooldown
    
    def _send_alert(self, error: Exception, context: Dict[str, Any] = None):
        """发送告警"""
        self.last_alert_time = datetime.now()
        
        alert_message = (
            f"DeepSeek API Alert: {self.consecutive_errors} consecutive errors\n"
            f"Latest error: {error}\n"
            f"Time: {self.last_error_time}\n"
            f"Context: {context or {}}"
        )
        
        logger.critical(alert_message, extra={
            "alert_type": "deepseek_api_failure",
            "consecutive_errors": self.consecutive_errors,
            "error_count": self.error_count
        })
        
        # 这里可以集成实际的告警系统（如邮件、钉钉、Slack等）
        # self._send_to_alert_system(alert_message)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_errors": self.error_count,
            "consecutive_errors": self.consecutive_errors,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "last_alert_time": self.last_alert_time.isoformat() if self.last_alert_time else None
        }

# 全局实例
_rate_limiter = None
_alert_manager = None

def get_rate_limiter(config: DeepSeekConfig) -> RateLimiter:
    """获取全局速率限制器"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            per_minute=config.rate_limit_per_minute,
            per_hour=config.rate_limit_per_hour
        )
    return _rate_limiter

def get_alert_manager() -> DeepSeekAlert:
    """获取全局告警管理器"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = DeepSeekAlert()
    return _alert_manager