"""
短信验证码数据仓库
==================
"""

from datetime import datetime, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.models.sms_code import SmsCode


class SmsCodeRepository:
    """短信验证码数据仓库

    提供验证码的创建、查询、验证和过期清理操作。

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
        self, phone: str, code: str, scene: str, expire_seconds: int = 300
    ) -> SmsCode:
        """创建验证码

        Args:
            phone: 手机号
            code: 验证码
            scene: 使用场景
            expire_seconds: 有效期（秒），默认 300 秒

        Returns:
            创建的验证码对象
        """
        expire_at = datetime.now() + timedelta(seconds=expire_seconds)
        sms_code = SmsCode(
            phone=phone, code=code, scene=scene, expire_at=expire_at
        )
        self.session.add(sms_code)
        self.session.flush()
        self.session.commit()  # 立即提交，确保其他 session 可见
        logger.info(f"创建验证码: {phone}, 场景: {scene}")
        return sms_code

    def get_valid_code(self, phone: str, scene: str) -> Optional[SmsCode]:
        """获取有效验证码

        有效条件：未过期、未使用。

        Args:
            phone: 手机号
            scene: 使用场景

        Returns:
            验证码对象，不存在或无效则返回 None
        """
        return (
            self.session.query(SmsCode)
            .filter(
                SmsCode.phone == phone,
                SmsCode.scene == scene,
                SmsCode.used == 0,
                SmsCode.expire_at > datetime.now(),
            )
            .order_by(SmsCode.created_at.desc())
            .first()
        )

    def mark_used(self, code_id: int) -> bool:
        """标记验证码已使用

        Args:
            code_id: 验证码 ID

        Returns:
            标记成功返回 True，验证码不存在返回 False
        """
        code = self.session.query(SmsCode).filter(SmsCode.id == code_id).first()
        if code is None:
            return False

        code.used = 1
        self.session.flush()
        logger.info(f"标记验证码已使用: {code_id}")
        return True

    def verify_code(self, phone: str, code: str, scene: str) -> bool:
        """验证验证码

        验证成功后会自动标记为已使用。

        Args:
            phone: 手机号
            code: 验证码
            scene: 使用场景

        Returns:
            验证成功返回 True，否则返回 False
        """
        valid_code = self.get_valid_code(phone, scene)
        if valid_code is None:
            return False

        if valid_code.code != code:
            return False

        # 验证成功，标记为已使用
        self.mark_used(valid_code.id)
        logger.info(f"验证码验证成功: {phone}, 场景: {scene}")
        return True

    def delete_expired(self) -> int:
        """清理过期验证码

        删除所有过期时间早于当前时间的验证码。

        Returns:
            删除的记录数
        """
        count = (
            self.session.query(SmsCode)
            .filter(SmsCode.expire_at < datetime.now())
            .delete()
        )
        self.session.flush()
        logger.info(f"清理过期验证码: {count} 条")
        return count
