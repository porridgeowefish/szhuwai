# TASK-008 短信验证码服务

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 1 天 |
| 前置任务 | TASK-006, TASK-007 |
| 后继任务 | TASK-009 |

## 任务目标

实现短信验证码业务服务，整合验证码仓库和短信客户端，提供完整的验证码发送和验证功能。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/services/sms_service.py` | 新建，验证码服务 |
| `src/services/__init__.py` | 扩展，导出验证码服务 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `src/infrastructure/aliyun_sms_client.py` | 由 TASK-007 负责 |
| `src/repositories/sms_code_repo.py` | 由 TASK-006 负责 |
| `src/repositories/sms_log_repo.py` | 由 TASK-006 负责 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/services/sms_service.py` | 验证码服务 |
| `test/services/test_sms_service.py` | 单元测试 |

## 技术规格

### 接口定义

```python
# src/services/sms_service.py
from dataclasses import dataclass
from src.repositories.sms_code_repo import SmsCodeRepository
from src.repositories.sms_log_repo import SmsLogRepository
from src.infrastructure.aliyun_sms_client import AliyunSmsClient


@dataclass
class SendCodeResult:
    """发送验证码结果"""
    success: bool
    expire_in: int = 0
    cooldown: int = 0
    error_code: str | None = None
    error_message: str | None = None


@dataclass
class RateLimitResult:
    """频率限制检查结果"""
    can_send: bool
    remaining: int  # 今日剩余次数
    cooldown_remaining: int  # 冷却剩余秒数


class SmsService:
    """短信验证码服务"""

    def __init__(
        self,
        sms_code_repo: SmsCodeRepository,
        sms_log_repo: SmsLogRepository,
        sms_client: AliyunSmsClient,
        config: "APIConfig"
    ) -> None:
        pass

    def send_code(self, phone: str, scene: str, ip: str | None = None) -> SendCodeResult:
        """发送验证码

        Args:
            phone: 手机号
            scene: 场景
            ip: 请求 IP

        Returns:
            发送结果
        """
        pass

    def verify_code(self, phone: str, code: str, scene: str) -> bool:
        """验证验证码

        Args:
            phone: 手机号
            code: 验证码
            scene: 场景

        Returns:
            是否验证成功
        """
        pass

    def check_rate_limit(self, phone: str) -> RateLimitResult:
        """检查发送频率限制

        Args:
            phone: 手机号

        Returns:
            频率限制检查结果
        """
        pass

    def _generate_code(self) -> str:
        """生成验证码"""
        pass

    def _check_cooldown(self, phone: str) -> int:
        """检查冷却时间，返回剩余秒数"""
        pass

    def _check_daily_limit(self, phone: str) -> tuple[bool, int]:
        """检查每日限制，返回 (是否超限, 剩余次数)"""
        pass
```

### 业务规则

```python
# 验证码发送流程
def send_code(self, phone: str, scene: str, ip: str | None = None) -> SendCodeResult:
    # 1. 检查手机号格式
    if not self._validate_phone(phone):
        return SendCodeResult(success=False, error_code="INVALID_PHONE")

    # 2. 检查冷却时间
    cooldown = self._check_cooldown(phone)
    if cooldown > 0:
        return SendCodeResult(
            success=False,
            error_code="RATE_LIMITED",
            error_message=f"请 {cooldown} 秒后重试",
            cooldown=cooldown
        )

    # 3. 检查每日限制
    can_send, remaining = self._check_daily_limit(phone)
    if not can_send:
        return SendCodeResult(
            success=False,
            error_code="DAILY_LIMIT_EXCEEDED",
            error_message="今日发送次数已达上限"
        )

    # 4. 生成验证码
    code = self._generate_code()

    # 5. 发送短信
    send_result = self.sms_client.send_verification_code(
        phone, code, self.sms_client.get_template_id(scene)
    )

    # 6. 记录日志
    self.sms_log_repo.create(phone, scene, ip, send_result.success, send_result.error_message)

    # 7. 如果发送成功，保存验证码
    if send_result.success:
        self.sms_code_repo.create(phone, code, scene, self.config.SMS_EXPIRE_SECONDS)

    return SendCodeResult(
        success=send_result.success,
        expire_in=self.config.SMS_EXPIRE_SECONDS,
        cooldown=self.config.SMS_COOLDOWN_SECONDS,
        error_code=send_result.error_code,
        error_message=send_result.error_message
    )
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| SmsCodeRepository | TASK-006 | 待完成 |
| SmsLogRepository | TASK-006 | 待完成 |
| AliyunSmsClient | TASK-007 | 待完成 |
| APIConfig | 已存在 | 可用 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/services/test_sms_service.py
import pytest
from unittest.mock import MagicMock, patch


class TestSmsService:
    """验证码服务测试"""

    def test_send_code_success(self):
        """测试发送成功"""
        pass

    def test_send_code_rate_limited(self):
        """测试冷却时间限制"""
        pass

    def test_send_code_daily_limit_exceeded(self):
        """测试每日上限"""
        pass

    def test_send_code_invalid_phone(self):
        """测试无效手机号"""
        pass

    def test_verify_code_success(self):
        """测试验证成功"""
        pass

    def test_verify_code_wrong(self):
        """测试验证失败（错误验证码）"""
        pass

    def test_verify_code_expired(self):
        """测试验证失败（已过期）"""
        pass

    def test_verify_code_used(self):
        """测试验证失败（已使用）"""
        pass

    def test_check_rate_limit_can_send(self):
        """测试频率检查通过"""
        pass

    def test_check_rate_limit_cooldown(self):
        """测试频率检查冷却中"""
        pass
```

**测试用例清单**：
- [ ] 发送成功返回正确结果
- [ ] 冷却时间内拒绝发送
- [ ] 超过每日上限拒绝发送
- [ ] 无效手机号拒绝发送
- [ ] 验证成功返回 True
- [ ] 验证失败返回 False
- [ ] 频率检查正确

### Step 2: 实现功能

1. 创建 `src/services/sms_service.py`
2. 实现发送验证码逻辑
3. 实现验证验证码逻辑
4. 实现频率限制检查

### Step 3: 验证通过

```bash
pytest test/services/test_sms_service.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）
- [ ] 无破坏性变更

## 参考资源

### 现有代码参考

| 文件 | 参考内容 |
|------|----------|
| `src/services/weather_service.py` | 服务类结构参考 |

### 相关文档

- [ITERATION_AUTH_PLAN.md - 2.5 短信验证码规则](../ITERATION_AUTH_PLAN.md#25-短信验证码规则)

## 注意事项

1. **验证码生成**: 使用 secrets 模块生成安全的随机验证码
2. **频率限制**: 60 秒冷却 + 每日 10 次上限
3. **验证后失效**: 验证成功后立即标记为已使用
4. **日志记录**: 无论发送成功失败都记录日志
