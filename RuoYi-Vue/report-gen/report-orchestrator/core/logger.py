import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
import sys

# 请求ID上下文变量
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

class StructuredFormatter(logging.Formatter):
    """结构化日志格式器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(''),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)

class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self, logger_name: str = "report_orchestrator"):
        self.logger = logging.getLogger(logger_name)
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器"""
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(StructuredFormatter())
            
            # 文件处理器
            file_handler = logging.FileHandler('logs/orchestrator.log', encoding='utf-8')
            file_handler.setFormatter(StructuredFormatter())
            
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)
    
    def set_request_id(self, request_id: Optional[str] = None) -> str:
        """设置请求ID"""
        if not request_id:
            request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        return request_id
    
    def info(self, message: str, **extra_fields):
        """记录信息日志"""
        record = self.logger.makeRecord(
            self.logger.name, logging.INFO, '', 0, message, (), None
        )
        if extra_fields:
            record.extra_fields = extra_fields
        self.logger.handle(record)
    
    def error(self, message: str, **extra_fields):
        """记录错误日志"""
        record = self.logger.makeRecord(
            self.logger.name, logging.ERROR, '', 0, message, (), None
        )
        if extra_fields:
            record.extra_fields = extra_fields
        self.logger.handle(record)
    
    def warning(self, message: str, **extra_fields):
        """记录警告日志"""
        record = self.logger.makeRecord(
            self.logger.name, logging.WARNING, '', 0, message, (), None
        )
        if extra_fields:
            record.extra_fields = extra_fields
        self.logger.handle(record)
    
    def debug(self, message: str, **extra_fields):
        """记录调试日志"""
        record = self.logger.makeRecord(
            self.logger.name, logging.DEBUG, '', 0, message, (), None
        )
        if extra_fields:
            record.extra_fields = extra_fields
        self.logger.handle(record)

class PerformanceLogger:
    """性能监控日志"""
    
    def __init__(self, logger: RequestLogger):
        self.logger = logger
        self.start_time = None
    
    def start_timer(self, operation: str):
        """开始计时"""
        import time
        self.start_time = time.time()
        self.logger.info(f"Started {operation}", operation=operation, event="start")
    
    def end_timer(self, operation: str, success: bool = True, **extra_fields):
        """结束计时"""
        import time
        if self.start_time:
            duration = time.time() - self.start_time
            self.logger.info(
                f"Completed {operation} in {duration:.3f}s",
                operation=operation,
                duration=duration,
                success=success,
                event="complete",
                **extra_fields
            )
            self.start_time = None

# 全局日志实例
logger = RequestLogger()
perf_logger = PerformanceLogger(logger)

# 创建日志目录
import os
os.makedirs('logs', exist_ok=True)