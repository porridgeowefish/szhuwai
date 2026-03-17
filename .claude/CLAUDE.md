# CLAUDE.md: 开发准则

## 技术栈
- **后端**: FastAPI + Python 3.10+
- **前端**: React 18 + TypeScript + Vite + Tailwind CSS
- **部署**: Docker + Docker Compose

## 核心原则
- **克制、防御、模块化**：保持代码简洁，严禁"面条代码"。
- **TDD 与 CI 优先**：先写 `pytest` 测试，后写逻辑。必须通过 `ruff` 和 `mypy --strict`。
- **契约式编程**：所有输入输出必须使用 `Pydantic V2` 模型，严禁传递原始 JSON 字典。
- **防御性 API 调用**：必须包含 `try-except`、超时处理和重试机制。
- **零幻觉**：Prompt 必须强制要求"仅基于已知信息，严禁捏造"。

## 项目结构
```
03_Code/
├── backend/          # Python 后端
│   ├── src/          # 源码
│   ├── test/         # 测试
│   ├── docs/         # 文档
│   └── main.py       # 入口
├── frontend/         # React 前端
│   ├── src/          # 源码
│   └── index.html
├── docker-compose.yml
└── Makefile
```

## 开发命令

### 后端
```bash
cd backend
pytest test/ -v              # 运行测试
python main.py               # 启动服务 (http://localhost:8000)
```

### 前端
```bash
cd frontend
npm install                  # 安装依赖
npm run dev                  # 启动开发服务器 (http://localhost:5173)
npm run build                # 构建生产版本
npm run lint                 # 代码检查
```

### Docker
```bash
docker-compose up --build    # 启动完整服务 (http://localhost)
```

## 结构规范
- **代码目录**：`backend/src/`
- **测试目录**：`backend/test/`，严格按模块对应
- **文档管理**：README.md 放在根目录，其余放在 `backend/docs/`，禁止创建 `_v1`, `_v2` 等冗余文档
- **语言要求**：全部文件和文档用中文撰写
- **执行协议**：**思考逻辑 -> 概述方案 -> 确认 -> 编码 -> 架构师审查 -> 执行反馈**

## 前端工作流协议
1. **开发前**：检查 `npm run lint` 无错误
2. **API 调用**：前端通过 Vite 代理访问 `/api/*`，自动转发到后端
3. **类型安全**：TypeScript 严格模式，禁止使用 `any`
4. **样式规范**：使用 Tailwind CSS，避免内联样式

## 架构师审查要求
每次编码任务结束，必须自省：
1. **代码复用性**：是否有可抽象的公共模块？
2. **测试覆盖率**：关键路径是否都有对应的测试覆盖？
3. **可维护性**：逻辑是否单一职责（SOLID）？
4. **简洁性**：是否引入了不必要的复杂性？

自我反省结束后，执行反馈，进行重构，删除不必要内容。
