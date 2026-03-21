# TASK-006 短信验证码模型与仓库

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 0.5 天 |
| 前置任务 | TASK-001（MySQL 连接） |
| 后继任务 | TASK-008 |

## 任务目标

实现短信验证码数据模型和数据访问仓库，支持验证码的存储、验证和频率限制。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/models/sms_code.py` | 新建，验证码 ORM 模型 |
| `src/models/sms_send_log.py` | 新建，发送日志 ORM 模型 |
| `src/repositories/sms_code_repo.py` | 新建，验证码仓库 |
| `src/repositories/sms_log_repo.py` | 新建，发送日志仓库 |
| `src/schemas/sms.py` | 新建，短信相关 Pydantic 模型 |
| `src/models/__init__.py` | 扩展，导出新模型 |
| `src/repositories/__init__.py` | 扩展，导出新仓库 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/infrastructure/mysql_client.py` | 由 TASK-001 负责不变 |
| `src/models/user.py` | 由 TASK-005 负责 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/models/sms_code.py` | 验证码 ORM 模型 |
| `src/models/sms_send_log.py` | 发送日志 ORM 模型 |
| `src/repositories/sms_code_repo.py` | 验证码仓库 |
| `src/repositories/sms_log_repo.py` | 发送日志仓库 |
| `src/schemas/sms.py` | 短信 Pydantic 模型 |
| `test/repositories/test_sms_code_repo.py` | 单元测试 |

## 技术规格

### ORM 模型

```python
# src/models/sms_code.py
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.mysql_client import Base


class SmsCode(Base):
    """验证码表"""
    __tablename__ = "sms_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    scene: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# src/models/sms_send_log.py
class SmsSendLog(Base):
    """短信发送日志表"""
    __tablename__ = "sms_send_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scene: Mapped[str] = mapped_column(String(20), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    success: Mapped[int] = mapped_column(Integer, nullable=False)
    error_msg: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### Pydantic 模型

```python
# src/schemas/sms.py
from enum import Enum
from pydantic import BaseModel, Field


class SmsScene(str, Enum):
    """验证码场景"""
    REGISTER = "register"
    LOGIN = "login"
    BIND = "bind"
    UNBIND = "unbind"
    RESET_PASSWORD = "reset_password"


class SmsSendRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    scene: SmsScene = Field(..., description="场景")


class SmsSendResponse(BaseModel):
    """发送验证码响应"""
    expire_in: int = Field(..., description="有效期（秒）")
    cooldown: int = Field(..., description="冷却时间（秒）")
```

### Repository 接口

```python
# src/repositories/sms_code_repo.py
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from src.models.sms_code import SmsCode


class SmsCodeRepository:
    """验证码数据仓库"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, phone: str, code: str, scene: str, expire_seconds: int = 300) -> SmsCode:
        """创建验证码"""
        pass

    def get_valid_code(self, phone: str, scene: str) -> Optional[SmsCode]:
        """获取有效验证码（未过期、未使用）"""
        pass

    def mark_used(self, code_id: int) -> bool:
        """标记验证码已使用"""
        pass

    def verify_code(self, phone: str, code: str, scene: str) -> bool:
        """验证验证码"""
        pass

    def delete_expired(self) -> int:
        """清理过期验证码"""
        pass


# src/repositories/sms_log_repo.py
class SmsLogRepository:
    """短信发送日志仓库"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, phone: str, scene: str, ip: str | None, success: bool, error_msg: str | None = None) -> None:
        """记录发送日志"""
        pass

    def count_today_by_phone(self, phone: str) -> int:
        """统计今日发送次数"""
        pass

    def get_latest_by_phone(self, phone: str) -> Optional[datetime]:
        """获取最近一次发送时间"""
        pass
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| MySQLClient | TASK-001 | 待完成 |
| SQLAlchemy Base | TASK-001 | 待完成 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/repositories/test_sms_code_repo.py
import pytest
from datetime import datetime, timedelta


class TestSmsCodeRepository:
    """验证码仓库测试"""

    def test_create_code(self, db_session):
        """测试创建验证码"""
        pass

    def test_get_valid_code(self, db_session):
        """测试获取有效验证码"""
        pass

    def test_get_valid_code_expired(self, db_session):
        """测试获取过期验证码返回 None"""
        pass

    def test_get_valid_code_used(self, db_session):
        """测试获取已使用验证码返回 None"""
        pass

    def test_mark_used(self, db_session):
        """测试标记已使用"""
        pass

    def test_verify_code_success(self, db_session):
        """测试验证成功"""
        pass

    def test_verify_code_wrong(self, db_session):
        """测试验证失败（错误验证码）"""
        pass

    def test_verify_code_expired(self, db_session):
        """测试验证失败（已过期）"""
        pass


class TestSmsLogRepository:
    """发送日志仓库测试"""

    def test_create_log(self, db_session):
        """测试创建日志"""
        pass

    def test_count_today(self, db_session):
        """测试统计今日发送次数"""
        pass

    def test_get_latest_time(self, db_session):
        """测试获取最近发送时间"""
        pass
```

**测试用例清单**：
- [ ] 创建验证码成功
- [ ] 获取有效验证码成功
- [ ] 过期验证码返回 None
- [ ] 已使用验证码返回 None
- [ ] 标记已使用成功
- [ ] 验证成功返回 True
- [ ] 验证失败返回 False
- [ ] 统计发送次数正确
- [ ] 获取最近发送时间正确

### Step 2: 实现功能

1. 创建 ORM 模型
2. 创建 Pydantic 模型
3. 创建 Repository 类
4. 更新 __init__.py 导出

### Step 3: 验证通过

```bash
pytest test/repositories/test_sms_code_repo.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）
- [ ] 无破坏性变更

## 参考资源

### 相关文档

- [ITERATION_AUTH_PLAN.md - 4.2.2 sms_codes 表](../ITERATION_AUTH_PLAN.md#422-sms_codes验证码表)
- [ITERATION_AUTH_PLAN.md - 4.2.3 sms_send_logs 表](../ITERATION_AUTH_PLAN.md#423-sms_send_logs短信发送日志表)

## 注意事项

1. **验证码安全**: 验证码只能使用一次，验证后标记为已使用
2. **过期清理**: 实现定时清理过期验证码的方法
3. **频率限制**: 通过 sms_send_logs 表实现发送频率限制
4. **索引优化**: phone 和 scene 字段需要联合索引
