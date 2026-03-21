"""
结构化日志模块
==============

提供 JSON 格式的结构化日志输出，便于日志分析和监控。
"""

import json
import logging
import sys
from datetime import datetime
from typing import Optional
from functools import lru_cache


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # 添加额外字段
        if self.include_extra and hasattr(record, '__dict__'):
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                              'levelname', 'levelno', 'lineno', 'module', 'msecs',
                              'pathname', 'process', 'processName', 'relativeCreated',
                              'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                              'message', 'taskName']:
                    try:
                        # 尝试 JSON 序列化
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)

            if extra_fields:
                log_data["extra"] = extra_fields

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 避免重复添加 handler
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)

    def _log(self, level: int, message: str, **kwargs):
        """记录日志"""
        extra = kwargs.pop('extra', {})
        extra.update(kwargs)
        self.logger.log(level, message, extra=extra)

    def info(self, message: str, **kwargs):
        """记录 INFO 级别日志"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录 WARNING 级别日志"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录 ERROR 级别日志"""
        self._log(logging.ERROR, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """记录 DEBUG 级别日志"""
        self._log(logging.DEBUG, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录 CRITICAL 级别日志"""
        self._log(logging.CRITICAL, message, **kwargs)


@lru_cache(maxsize=32)
def get_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """获取结构化日志记录器（带缓存）"""
    return StructuredLogger(name, level)


def setup_structured_logging(level: str = "INFO", output_file: Optional[str] = None):
    """
    配置全局结构化日志

    Args:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        output_file: 可选的日志文件路径
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有的 handlers
    root_logger.handlers.clear()

    # 添加控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # 添加文件 handler（如果指定）
    if output_file:
        file_handler = logging.FileHandler(output_file, encoding='utf-8')
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)


# 预定义的日志上下文字段
class LogContext:
    """日志上下文常量"""

    # API 相关
    API_TYPE = "api_type"
    ENDPOINT = "endpoint"
    STATUS_CODE = "status_code"
    RESPONSE_TIME_MS = "response_time_ms"

    # 轨迹相关
    TRACK_ID = "track_id"
    TRACK_DISTANCE_KM = "track_distance_km"
    TRACK_ASCENT_M = "track_ascent_m"

    # 天气相关
    WEATHER_LOCATION = "weather_location"
    TRIP_DATE = "trip_date"

    # LLM 相关
    LLM_MODEL = "llm_model"
    LLM_TOKENS_USED = "llm_tokens_used"
    LLM_RESPONSE_TIME_MS = "llm_response_time_ms"

    # 计划相关
    PLAN_ID = "plan_id"
    PLAN_TITLE = "plan_title"
