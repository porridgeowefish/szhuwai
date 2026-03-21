# TASK-007 阿里云短信客户端

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P1 |
| 预估工时 | 1 天 |
| 前置任务 | 无 |
| 后继任务 | TASK-008 |

## 任务目标

实现阿里云短信服务客户端，支持发送短信验证码。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/infrastructure/aliyun_sms_client.py` | 新建，阿里云短信客户端 |
| `src/infrastructure/__init__.py` | 扩展，导出短信客户端 |
| `src/api/config.py` | 扩展，添加短信配置项 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| 任何现有服务文件 | 本任务为独立新模块 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/infrastructure/aliyun_sms_client.py` | 阿里云短信客户端 |
| `test/infrastructure/test_aliyun_sms_client.py` | 单元测试 |

## 技术规格

### 配置项扩展

```python
# src/api/config.py 新增配置
class APIConfig(BaseModel):
    # ... 现有配置 ...

    # 阿里云短信配置
    ALIYUN_ACCESS_KEY_ID: str = Field(default="", description="阿里云 AccessKey ID")
    ALIYUN_ACCESS_KEY_SECRET: str = Field(default="", description="阿里云 AccessKey Secret")
    SMS_SIGN_NAME: str = Field(default="户外规划助手", description="短信签名")
    SMS_TEMPLATE_REGISTER: str = Field(default="", description="注册模板 ID")
    SMS_TEMPLATE_LOGIN: str = Field(default="", description="登录模板 ID")
    SMS_TEMPLATE_BIND: str = Field(default="", description="绑定模板 ID")
    SMS_TEMPLATE_UNBIND: str = Field(default="", description="解绑模板 ID")
    SMS_TEMPLATE_RESET_PASSWORD: str = Field(default="", description="重置密码模板 ID")

    # 短信业务配置
    SMS_CODE_LENGTH: int = Field(default=6, description="验证码长度")
    SMS_EXPIRE_SECONDS: int = Field(default=300, description="验证码有效期（秒）")
    SMS_COOLDOWN_SECONDS: int = Field(default=60, description="发送冷却时间（秒）")
    SMS_DAILY_LIMIT: int = Field(default=10, description="每日发送上限")
```

### 接口定义

```python
# src/infrastructure/aliyun_sms_client.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class SmsSendResult:
    """短信发送结果"""
    success: bool
    biz_id: Optional[str] = None  # 阿里云返回的发送回执 ID
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class AliyunSmsClient:
    """阿里云短信客户端"""

    def __init__(self, config: "APIConfig") -> None:
        """初始化客户端"""
        pass

    def send_verification_code(
        self,
        phone: str,
        code: str,
        template_id: str
    ) -> SmsSendResult:
        """发送验证码短信

        Args:
            phone: 手机号
            code: 验证码
            template_id: 短信模板 ID

        Returns:
            发送结果
        """
        pass

    def get_template_id(self, scene: str) -> str:
        """根据场景获取模板 ID"""
        pass


# 全局实例
aliyun_sms_client: AliyunSmsClient | None = None


def get_aliyun_sms_client() -> AliyunSmsClient:
    """获取全局短信客户端实例"""
    pass


def init_aliyun_sms_client(config: "APIConfig") -> AliyunSmsClient:
    """初始化全局短信客户端"""
    pass
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| alibabacloud-dysmsapi20170525 | 需新增依赖 | 待安装 |
| APIConfig | 已存在 | 可用 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/infrastructure/test_aliyun_sms_client.py
import pytest
from unittest.mock import patch, MagicMock


class TestAliyunSmsClient:
    """阿里云短信客户端测试"""

    def test_init_with_config(self):
        """测试初始化"""
        pass

    @patch("src.infrastructure.aliyun_sms_client.Client")
    def test_send_verification_code_success(self, mock_client):
        """测试发送成功"""
        pass

    @patch("src.infrastructure.aliyun_sms_client.Client")
    def test_send_verification_code_failure(self, mock_client):
        """测试发送失败"""
        pass

    def test_get_template_id(self):
        """测试获取模板 ID"""
        pass

    @patch("src.infrastructure.aliyun_sms_client.Client")
    def test_send_with_invalid_phone(self, mock_client):
        """测试无效手机号"""
        pass
```

**测试用例清单**：
- [ ] 初始化成功
- [ ] 发送验证码成功
- [ ] 发送失败返回错误信息
- [ ] 获取模板 ID 正确
- [ ] 无效手机号处理

### Step 2: 实现功能

1. 扩展 `src/api/config.py` 添加短信配置
2. 创建 `src/infrastructure/aliyun_sms_client.py`
3. 实现发送验证码功能
4. 实现 Mock 模式（开发环境）

### Step 3: 验证通过

```bash
pytest test/infrastructure/test_aliyun_sms_client.py -v
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）
- [ ] 无破坏性变更

## 参考资源

### 相关文档

- [阿里云短信 API 文档](https://help.aliyun.com/document_detail/101414.html)
- [ITERATION_AUTH_PLAN.md - 5.6 配置项](../ITERATION_AUTH_PLAN.md#56-配置项)

## 注意事项

1. **Mock 模式**: 在没有配置 AccessKey 时，使用 Mock 模式返回成功
2. **错误处理**: 捕获阿里云 SDK 异常，转换为统一错误格式
3. **模板变量**: 验证码模板通常需要 `code` 变量
4. **签名一致**: 确保短信签名已在阿里云审核通过
5. **敏感信息**: AccessKey 从环境变量加载，不硬编码
