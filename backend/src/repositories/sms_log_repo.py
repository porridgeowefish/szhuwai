"""
短信发送日志仓库
================
"""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.models.sms_send_log import SmsSendLog


class SmsLogRepository:
    """短信发送日志仓库

    提供日志记录和频率统计功能。

    Args:
        session: SQLAlchemy 数据库会话
    """

    def __init__(self, session: Session) -> None:
        """初始化仓库

        Args:
            session: 数据库会话
        """
        self.session = session

    def create(
        self,
        phone: str,
        scene: str,
        ip: str | None,
        success: bool,
        error_msg: str | None = None,
    ) -> None:
        """记录发送日志

        Args:
            phone: 手机号
            scene: 使用场景
            ip: 请求 IP 地址（可选）
            success: 是否成功
            error_msg: 错误信息（可选）
        """
        log = SmsSendLog(
            phone=phone,
            scene=scene,
            ip=ip,
            success=1 if success else 0,
            error_msg=error_msg,
        )
        self.session.add(log)
        self.session.flush()
        logger.debug(f"记录发送日志: {phone}, 成功: {success}")

    def count_today_by_phone(self, phone: str) -> int:
        """统计今日发送次数

        Args:
            phone: 手机号

        Returns:
            今日发送次数
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = (
            self.session.query(SmsSendLog)
            .filter(
                SmsSendLog.phone == phone,
                SmsSendLog.created_at >= today_start,
            )
            .count()
        )
        return count

    def get_latest_by_phone(self, phone: str) -> Optional[datetime]:
        """获取最近一次发送时间

        Args:
            phone: 手机号

        Returns:
            最近发送时间，无记录则返回 None
        """
        log = (
            self.session.query(SmsSendLog)
            .filter(SmsSendLog.phone == phone)
            .order_by(SmsSendLog.created_at.desc())
            .first()
        )
        return log.created_at if log else None
