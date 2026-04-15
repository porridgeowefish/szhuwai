# 认证与配置修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复三个阻断性 Bug：MySQL 密码未加载、用户名验证过严、前端首页无鉴权守卫。

**Architecture:** 三个独立修复点——后端配置层、认证 Schema 层、前端路由层。每个修复点只改一个文件，互不依赖。

**Tech Stack:** Python 3.10+ / FastAPI / Pydantic V2 / React 18 / React Router v6

---

## Task 1: 修复 `.env` 文件路径解析（MySQL 密码未加载的根因）

**Files:**
- Modify: `backend/src/api/config.py:282-357` (`from_env` 方法)

**根因分析:**
`from_env()` 使用相对路径 `.env` 查找环境文件。当用户从 `backend/` 目录执行 `python main.py` 时，`os.path.exists(".env")` 在 `backend/` 下找不到 `.env`（文件在项目根目录），导致 `MYSQL_PASSWORD` 回退为默认空字符串 `""`，连接 MySQL 时报 `Access denied (using password: NO)`。

用户终端可能通过系统环境变量设置了 `MYSQL_HOST=localhost` 和 `MYSQL_PORT=3307`（所以启动日志显示正确的主机端口），但 `MYSQL_PASSWORD` 没有设置，又找不到 `.env` 文件来补充。

- [ ] **Step 1: 修改 `from_env` 方法，增加向上搜索 `.env` 的逻辑**

在 `backend/src/api/config.py` 的 `from_env` 方法中，将 `.env` 查找逻辑从单一相对路径改为：先检查当前目录，再向上搜索父目录（最多 5 层），找到第一个存在的 `.env` 文件。

```python
@classmethod
def from_env(cls, env_file: str = ".env") -> "APIConfig":
    """从环境文件加载配置

    加载顺序：
    1. 优先从系统环境变量加载（Docker/云端部署方式）
    2. 从 .env 文件加载（自动搜索当前目录及父目录）
    """
    config_data = {}

    # 环境变量映射
    env_mapping = {
        "QWEATHER_API_KEY": "WEATHER_API_KEY",
        "AMAP_API_KEY": "MAP_API_KEY",
        "LLM_API_KEY": "LLM_API_KEY",
        "TAVILY_API_KEY": "SEARCH_API_KEY",
        "WEATHER_DEVELOPER_HOST": "WEATHER_DEVELOPER_HOST",
        # MySQL 环境变量
        "MYSQL_HOST": "MYSQL_HOST",
        "MYSQL_PORT": "MYSQL_PORT",
        "MYSQL_USER": "MYSQL_USER",
        "MYSQL_PASSWORD": "MYSQL_PASSWORD",
        "MYSQL_DATABASE": "MYSQL_DATABASE",
        "MYSQL_POOL_SIZE": "MYSQL_POOL_SIZE",
        # MongoDB 环境变量
        "MONGO_HOST": "MONGO_HOST",
        "MONGO_PORT": "MONGO_PORT",
        "MONGO_USER": "MONGO_USER",
        "MONGO_PASSWORD": "MONGO_PASSWORD",
        "MONGO_DATABASE": "MONGO_DATABASE",
        # Redis 环境变量
        "REDIS_HOST": "REDIS_HOST",
        "REDIS_PORT": "REDIS_PORT",
        "REDIS_PASSWORD": "REDIS_PASSWORD",
        "REDIS_DB": "REDIS_DB",
        # JWT 环境变量
        "JWT_SECRET_KEY": "JWT_SECRET_KEY",
        "JWT_ALGORITHM": "JWT_ALGORITHM",
        "JWT_EXPIRE_SECONDS": "JWT_EXPIRE_SECONDS",
        # 阿里云短信环境变量
        "ALIYUN_ACCESS_KEY_ID": "ALIYUN_ACCESS_KEY_ID",
        "ALIYUN_ACCESS_KEY_SECRET": "ALIYUN_ACCESS_KEY_SECRET",
        "SMS_SIGN_NAME": "SMS_SIGN_NAME",
        "SMS_TEMPLATE_REGISTER": "SMS_TEMPLATE_REGISTER",
        "SMS_TEMPLATE_LOGIN": "SMS_TEMPLATE_LOGIN",
        "SMS_TEMPLATE_BIND": "SMS_TEMPLATE_BIND",
        "SMS_TEMPLATE_UNBIND": "SMS_TEMPLATE_UNBIND",
        "SMS_TEMPLATE_RESET_PASSWORD": "SMS_TEMPLATE_RESET_PASSWORD",
    }

    # 1. 从系统环境变量加载
    for env_var, config_key in env_mapping.items():
        env_value = os.getenv(env_var)
        if env_value:
            config_data[config_key] = env_value

    # 2. 搜索 .env 文件：当前目录 → 父目录（最多 5 层）
    resolved_env_file = None
    if os.path.isabs(env_file):
        if os.path.exists(env_file):
            resolved_env_file = env_file
    else:
        current = os.path.abspath(".")
        for _ in range(6):
            candidate = os.path.join(current, env_file)
            if os.path.exists(candidate):
                resolved_env_file = candidate
                break
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

    if resolved_env_file:
        with open(resolved_env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 处理环境变量映射
                    if key in env_mapping:
                        if env_mapping[key] not in config_data:
                            config_data[env_mapping[key]] = value
                    elif key == 'PROXY_HTTP':
                        if 'PROXY' not in config_data:
                            config_data['PROXY'] = {}
                        config_data['PROXY']['http'] = value
                    elif key == 'PROXY_HTTPS':
                        if 'PROXY' not in config_data:
                            config_data['PROXY'] = {}
                        config_data['PROXY']['https'] = value
                    elif key in cls.model_fields and key not in config_data:
                        config_data[key] = value

    return cls(**config_data)
```

- [ ] **Step 2: 验证 `.env` 文件能被正确找到**

Run: `cd D:/2_Study/Outdoor-Agent-Planner/03_Code/backend && python -c "from src.api.config import APIConfig; c = APIConfig.from_env(); print(f'MYSQL_PASSWORD={repr(c.MYSQL_PASSWORD)}')"` 
Expected: `MYSQL_PASSWORD='123456'`（而非空字符串）

---

## Task 2: 放宽用户名验证正则（允许数字开头）

**Files:**
- Modify: `backend/src/schemas/auth.py:14` (UsernameRegisterRequest)

**根因分析:**
`UsernameRegisterRequest.username` 的 pattern 为 `^[a-zA-Z][a-zA-Z0-9_]*$`，要求首字符必须为字母。用户输入 `14r65t12q`（数字开头）被拒绝，返回 422。应放宽为允许数字开头，同时保留长度和字符集限制。

- [ ] **Step 1: 修改用户名验证正则**

将 `backend/src/schemas/auth.py` 第 14 行的 pattern 从 `^[a-zA-Z][a-zA-Z0-9_]*$` 改为 `^[a-zA-Z0-9][a-zA-Z0-9_]*$`。

修改前:
```python
username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
```

修改后:
```python
username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_]*$")
```

- [ ] **Step 2: 验证正则修改正确**

Run: `cd D:/2_Study/Outdoor-Agent-Planner/03_Code/backend && python -c "from src.schemas.auth import UsernameRegisterRequest; r = UsernameRegisterRequest(username='14r65t12q', password='123456'); print(f'OK: {r.username}')"`
Expected: `OK: 14r65t12q`（不再报 validation error）

---

## Task 3: 前端首页加入鉴权守卫

**Files:**
- Modify: `frontend/src/App.tsx:32-38` (路由配置)

**根因分析:**
`App.tsx` 中 `/`（HomePage）被放在公开路由区域（PublicLayout），用户访问首页直接看到策划生成表单，无需登录。业务要求用户必须先注册/登录才能使用核心功能。

修改方案：将 `/` 路由从公开区域移到受保护区域。`ProtectedLayout` 已包含「首页」导航链接（指向 `/`），所以移动后 HomePage 自然使用 ProtectedLayout，用户体验一致。

- [ ] **Step 1: 修改路由配置**

将 `frontend/src/App.tsx` 中 HomePage 路由从公开路由移到受保护路由。

修改后的完整 Routes 部分:
```tsx
<Routes>
  {/* 公开路由 */}
  <Route element={<PublicLayout />}>
    <Route path="/auth/login" element={<LoginPage />} />
    <Route path="/auth/register" element={<RegisterPage />} />
  </Route>

  {/* 需认证路由 */}
  <Route
    element={
      <ProtectedRoute>
        <ProtectedLayout />
      </ProtectedRoute>
    }
  >
    <Route path="/" element={<HomePage />} />
    <Route path="/reports" element={<ReportListPage />} />
    <Route path="/reports/:id" element={<ReportDetailPage />} />
    <Route path="/tools" element={<ToolsPage />} />
    <Route path="/profile" element={<ProfilePage />} />
    <Route path="/profile/password" element={<ChangePasswordPage />} />
    <Route path="/tools/track" element={<TrackAnalysisPage />} />
    <Route path="/tools/weather" element={<WeatherQueryPage />} />
    <Route path="/tools/transport" element={<TransportPage />} />
    <Route path="/tools/search" element={<SearchPage />} />
    <Route path="/admin/users" element={<UserManagementPage />} />
  </Route>

  {/* 404 重定向 */}
  <Route path="*" element={<Navigate to="/" replace />} />
</Routes>
```

- [ ] **Step 2: 验证前端路由守卫生效**

Run: `cd D:/2_Study/Outdoor-Agent-Planner/03_Code/frontend && npm run build 2>&1 | tail -5`
Expected: 构建成功，无 TypeScript 错误

- [ ] **Step 3: 手动验证**

在浏览器中访问 `http://localhost:5173`，应自动跳转到 `/auth/login` 登录页面。登录成功后跳转回首页 `/`。

---

## Self-Review

**1. Spec coverage:**
- MySQL 密码未加载 → Task 1（.env 路径搜索）
- 用户名验证过严 → Task 2（正则放宽）
- 前端无鉴权守卫 → Task 3（路由调整）

**2. Placeholder scan:**
- 无 TBD、TODO、fill in details
- 每一步都有具体代码和验证命令

**3. Type consistency:**
- config.py: `MYSQL_PASSWORD` 类型不变（str）
- auth.py: `username` 类型不变（str），仅改 pattern
- App.tsx: 路由结构不变，仅移动位置
