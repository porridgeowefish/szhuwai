"""
认证模块测试数据 Fixtures
==========================

提供认证相关的测试数据生成器。
"""



def generate_user_data(
    username: str = "testuser",
    password: str = "Test@123456",
    phone: str | None = None
) -> dict:
    """生成用户注册数据

    Args:
        username: 用户名
        password: 密码
        phone: 手机号（可选）

    Returns:
        dict: 用户注册请求数据
    """
    data = {
        "username": username,
        "password": password
    }
    if phone:
        data["phone"] = phone
    return data


def generate_phone_register_data(
    phone: str = "13800138000",
    code: str = "123456",
    password: str | None = None,
    username: str | None = None
) -> dict:
    """生成手机号注册数据

    Args:
        phone: 手机号
        code: 验证码
        password: 密码（可选）
        username: 用户名（可选）

    Returns:
        dict: 手机号注册请求数据
    """
    data = {
        "phone": phone,
        "code": code
    }
    if password:
        data["password"] = password
    if username:
        data["username"] = username
    return data


def generate_sms_send_data(
    phone: str = "13800138000",
    scene: str = "register"
) -> dict:
    """生成短信发送请求数据

    Args:
        phone: 手机号
        scene: 使用场景

    Returns:
        dict: 短信发送请求数据
    """
    return {
        "phone": phone,
        "scene": scene
    }


def generate_login_data(
    username: str | None = None,
    password: str | None = None,
    phone: str | None = None,
    code: str | None = None
) -> dict:
    """生成登录请求数据

    Args:
        username: 用户名（用户名登录时使用）
        password: 密码（用户名登录时使用）
        phone: 手机号（手机号登录时使用）
        code: 验证码（手机号登录时使用）

    Returns:
        dict: 登录请求数据
    """
    if phone and code:
        return {
            "phone": phone,
            "code": code
        }
    return {
        "username": username,
        "password": password
    }


def generate_bind_phone_data(
    phone: str = "13800138000",
    code: str = "123456"
) -> dict:
    """生成绑定手机号请求数据

    Args:
        phone: 手机号
        code: 验证码

    Returns:
        dict: 绑定手机号请求数据
    """
    return {
        "phone": phone,
        "code": code
    }


def generate_reset_password_data(
    phone: str = "13800138000",
    code: str = "123456",
    new_password: str = "NewPass@123"
) -> dict:
    """生成重置密码请求数据

    Args:
        phone: 手机号
        code: 验证码
        new_password: 新密码

    Returns:
        dict: 重置密码请求数据
    """
    return {
        "phone": phone,
        "code": code,
        "newPassword": new_password
    }


# ============ 测试数据常量 ============

VALID_USERNAMES = [
    "abc",
    "user123",
    "test_user",
    "User123",
    "a1b2c3d4e5f6g7h8i9j0"
]

INVALID_USERNAMES = [
    "ab",  # 太短
    "a" * 21,  # 太长
    "1abc",  # 数字开头
    " abc",  # 空格开头
    "abc!",  # 特殊字符
    "中文用户名",  # 中文
    "user@example",  # @ 符号
]

VALID_PASSWORDS = [
    "123456",
    "password",
    "Pass@123",
    "a" * 32
]

INVALID_PASSWORDS = [
    "12345",  # 太短
    "a" * 33,  # 太长
]

VALID_PHONES = [
    "13800138000",
    "15912345678",
    "18600001111"
]

INVALID_PHONES = [
    "12345678901",  # 不是有效手机号
    "1380013800",  # 太短
    "138001380000",  # 太长
    "abcdefghijk",  # 非数字
    "138-0013-8000",  # 带横线
]

SMS_SCENES = [
    "register",
    "login",
    "bind",
    "reset_password"
]

USER_ROLES = [
    "user",
    "admin"
]

USER_STATUSES = [
    "active",
    "disabled"
]
