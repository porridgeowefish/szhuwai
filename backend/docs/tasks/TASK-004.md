# TASK-004 密码加密工具类

## 基本信息

| 属性 | 值 |
|------|-----|
| 优先级 | P0 |
| 预估工时 | 0.5 天 |
| 前置任务 | 无 |
| 后继任务 | TASK-009 |

## 任务目标

实现密码加密和验证工具类，使用 bcrypt 算法确保密码安全存储。

## 开发边界

### ✅ 可以修改的文件

| 文件路径 | 修改说明 |
|----------|----------|
| `src/infrastructure/password_hasher.py` | 新建，密码工具类 |
| `src/infrastructure/__init__.py` | 扩展，导出密码工具 |

### ❌ 禁止修改的文件

| 文件路径 | 原因 |
|----------|------|
| `main.py` | 入口文件，其他任务负责集成 |
| 任何现有文件 | 本任务只需新建，不需修改现有代码 |

### 🆕 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `src/infrastructure/password_hasher.py` | 密码加密工具类 |
| `test/infrastructure/test_password_hasher.py` | 单元测试 |

## 技术规格

### 接口定义

```python
# src/infrastructure/password_hasher.py
import bcrypt


class PasswordHasher:
    """密码加密工具类"""

    # bcrypt 工作因子（越高越安全，但越慢）
    ROUNDS: int = 12

    def hash_password(self, password: str) -> str:
        """加密密码

        Args:
            password: 明文密码

        Returns:
            加密后的密码哈希（包含 salt）
        """
        pass

    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码

        Args:
            password: 明文密码
            hashed: 存储的密码哈希

        Returns:
            密码是否匹配
        """
        pass

    def needs_rehash(self, hashed: str) -> bool:
        """检查是否需要重新哈希

        当工作因子改变时，旧的哈希可能需要更新。

        Args:
            hashed: 存储的密码哈希

        Returns:
            是否需要重新哈希
        """
        pass


# 全局实例
password_hasher: PasswordHasher = PasswordHasher()


def get_password_hasher() -> PasswordHasher:
    """获取全局密码加密器实例"""
    return password_hasher
```

### 依赖项

| 依赖 | 来源 | 状态 |
|------|------|------|
| passlib[bcrypt] | 需新增依赖 | 待安装 |
| 或 bcrypt | 需新增依赖 | 待安装 |

## 实现步骤

### Step 1: 编写测试用例

```python
# test/infrastructure/test_password_hasher.py
import pytest


class TestPasswordHasher:
    """密码加密器测试"""

    def test_hash_password(self):
        """测试密码加密"""
        pass

    def test_verify_password_correct(self):
        """测试验证正确密码"""
        pass

    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        pass

    def test_hash_password_empty(self):
        """测试空密码"""
        pass

    def test_hash_password_unicode(self):
        """测试 Unicode 密码"""
        pass

    def test_hash_uniqueness(self):
        """测试相同密码生成不同哈希（因为有 salt）"""
        pass

    def test_needs_rehash(self):
        """测试是否需要重新哈希"""
        pass
```

**测试用例清单**：
- [ ] 密码加密成功
- [ ] 验证正确密码返回 True
- [ ] 验证错误密码返回 False
- [ ] 空密码处理正确
- [ ] Unicode 密码处理正确
- [ ] 相同密码生成不同哈希
- [ ] 哈希格式正确（bcrypt 格式）

### Step 2: 实现功能

1. 创建 `src/infrastructure/password_hasher.py`
2. 实现 `hash_password` 方法
3. 实现 `verify_password` 方法
4. 实现 `needs_rehash` 方法（可选）

### Step 3: 验证通过

```bash
# 运行测试
pytest test/infrastructure/test_password_hasher.py -v

# 代码检查
ruff check src/infrastructure/password_hasher.py
```

## 验收标准

- [ ] 所有测试用例通过
- [ ] 代码风格检查通过（ruff）
- [ ] 类型检查通过（mypy --strict）
- [ ] 无破坏性变更（现有测试仍通过）

## 参考资源

### 现有代码参考

| 文件 | 参考内容 |
|------|----------|
| 无 | 本任务为独立新模块 |

### 相关文档

- [ITERATION_AUTH_PLAN.md - 1.3 技术选型](../ITERATION_AUTH_PLAN.md#13-技术选型)
- [bcrypt 文档](https://pypi.org/project/bcrypt/)

## 注意事项

1. **工作因子**: 使用 12 轮，平衡安全性和性能
2. **编码处理**: 密码需要编码为 bytes 再加密
3. **返回格式**: 返回字符串格式，便于数据库存储
4. **Salt 自动**: bcrypt 自动生成和存储 salt，无需单独处理
