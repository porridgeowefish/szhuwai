"""
数据仓库模块
=============

定义所有数据访问仓库。
"""

from src.repositories.sms_code_repo import SmsCodeRepository
from src.repositories.sms_log_repo import SmsLogRepository
from src.repositories.user_repo import UserRepository

__all__ = ["UserRepository", "SmsCodeRepository", "SmsLogRepository"]
