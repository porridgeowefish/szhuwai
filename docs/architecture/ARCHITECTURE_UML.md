# Outdoor Agent Planner — 系统架构 UML 图

> 生成日期: 2026-04-16  
> 分支: worktree-agent-architecture

---

## 1. 系统上下文图 (System Context)

```mermaid
graph TB
    User[👤 用户]
    
    subgraph "Outdoor Agent Planner"
        FE["React Frontend<br/>Vite + TypeScript + Tailwind"]
        BE["FastAPI Backend<br/>Python 3.10+"]
    end
    
    subgraph "数据层"
        MySQL[("MySQL<br/>用户/额度/短信")]
        MongoDB[("MongoDB<br/>报告/记忆")]
        Redis[("Redis<br/>会话缓存")]
        PostgreSQL[("PostgreSQL + PostGIS<br/>线路空间数据")]
    end
    
    subgraph "外部服务"
        QWeather[和风天气 API]
        Gaode[高德地图 API]
        SiliconFlow[SiliconFlow LLM<br/>Kimi-K2.5]
        Aliyun[阿里云短信]
    end
    
    User --> FE
    FE -->|REST + SSE| BE
    BE --> MySQL
    BE --> MongoDB
    BE --> Redis
    BE --> PostgreSQL
    BE -->|HTTP| QWeather
    BE -->|HTTP| Gaode
    BE -->|OpenAI Compatible| SiliconFlow
    BE -->|SDK| Aliyun
    
    style FE fill:#61dafb,color:#000
    style BE fill:#009688,color:#fff
    style MySQL fill:#4479a1,color:#fff
    style MongoDB fill:#47a248,color:#fff
    style Redis fill:#dc382d,color:#fff
    style PostgreSQL fill:#336791,color:#fff
```

---

## 2. 后端模块依赖图 (Package Diagram)

```mermaid
graph TB
    subgraph "API Layer"
        routes["api.routes<br/>11 路由模块"]
        deps["api.deps<br/>依赖注入"]
        config["api.config<br/>APIConfig"]
    end
    
    subgraph "Agent Layer"
        graph_mod["agent.graph<br/>LangGraph 图"]
        state["agent.state<br/>AgentState"]
        prompt["agent.system_prompt"]
        session["agent.session<br/>SessionManager"]
        context["agent.context<br/>ContextManager"]
        memory["agent.memory<br/>UserMemoryStore"]
        tools["agent.tools<br/>7 工具"]
    end
    
    subgraph "Domain Layer"
        orchestrator["domain.orchestrator<br/>OutdoorPlannerRouter"]
    end
    
    subgraph "Service Layer"
        track_svc["TrackService"]
        weather_svc["WeatherService"]
        transport_svc["TransportService"]
        search_svc["SearchService"]
        llm_svc["LLMService"]
        auth_svc["AuthService"]
        quota_svc["QuotaService"]
        report_svc["ReportService"]
        route_svc["RouteService"]
    end
    
    subgraph "Repository Layer"
        user_repo["UserRepository<br/>MySQL"]
        quota_repo["QuotaRepo<br/>MySQL"]
        report_repo["ReportRepo<br/>MongoDB"]
        route_repo["RouteRepo<br/>PostgreSQL"]
    end
    
    subgraph "Infrastructure"
        mysql_client["MySQLClient"]
        mongo_client["MongoClient"]
        redis_client["RedisClient<br/>+ InMemoryRedis"]
        pg_client["PostgresClient"]
        jwt_handler["JWTHandler"]
        sms_client["AliyunSmsClient"]
    end
    
    routes --> deps
    routes --> config
    
    routes --> graph_mod
    routes --> orchestrator
    routes --> track_svc
    routes --> weather_svc
    routes --> transport_svc
    routes --> search_svc
    routes --> auth_svc
    routes --> quota_svc
    routes --> report_svc
    
    graph_mod --> tools
    graph_mod --> state
    graph_mod --> config
    tools --> track_svc
    tools --> weather_svc
    tools --> transport_svc
    tools --> search_svc
    tools --> orchestrator
    tools --> route_svc
    context --> session
    memory --> mongo_client
    
    orchestrator --> track_svc
    orchestrator --> weather_svc
    orchestrator --> transport_svc
    orchestrator --> search_svc
    orchestrator --> llm_svc
    
    track_svc --> track_parser
    weather_svc --> weather_client
    transport_svc --> map_client
    search_svc --> search_client
    
    auth_svc --> user_repo
    quota_svc --> quota_repo
    report_svc --> report_repo
    route_svc --> route_repo
    
    user_repo --> mysql_client
    quota_repo --> mysql_client
    report_repo --> mongo_client
    route_repo --> pg_client
    
    routes --> session
    session --> redis_client
    
    style graph_mod fill:#ff9800,color:#000
    style orchestrator fill:#9c27b0,color:#fff
    style tools fill:#ff5722,color:#fff
```

---

## 3. Agent 核心类图 (Class Diagram)

```mermaid
classDiagram
    class AgentState {
        <<TypedDict>>
        +messages: List~BaseMessage~
        +conversation_meta: ConversationMeta
        +tool_results: List~ToolResult~
        +active_plan: Dict
        +user_preferences: Dict
    }
    
    class ConversationMeta {
        <<TypedDict>>
        +session_id: str
        +user_id: int
        +created_at: str
        +plan_title: str
    }
    
    class ToolResult {
        <<TypedDict>>
        +tool_name: str
        +status: str
        +data: Any
        +display_type: str
    }
    
    class SessionManager {
        -redis: Redis|InMemoryRedis
        -ttl: int
        +create_session(session_id, user_id)
        +get_session(session_id, user_id) Dict
        +get_user_sessions(user_id) List
        +get_messages(session_id) List~BaseMessage~
        +append_message(session_id, role, content)
        +set_attachment(session_id, key, value)
        +get_attachment(session_id, key) str
        +delete_session(session_id)
    }
    
    class ContextManager {
        -session_manager: SessionManager
        -max_turns: int
        -summary_threshold: int
        +build_messages_for_llm(session_id, new_msg, prompt) List~BaseMessage~
        -_summarize_old_turns(turns) str
    }
    
    class UserMemoryStore {
        -mongo_client: MongoClient
        +get_preferences(user_id) Dict
        +update_preferences(user_id, prefs)
        +add_extracted_fact(user_id, fact)
        +get_context_for_prompt(user_id) str
    }
    
    class CompiledGraph {
        +invoke(state) Dict
        +astream_events(state, config) AsyncGenerator
    }
    
    class ToolRegistry {
        +get_all_tools() List~BaseTool~
    }
    
    class BaseTool {
        <<LangChain Tool>>
        +name: str
        +description: str
        +args_schema: BaseModel
        +invoke(input) str
    }
    
    AgentState --> ConversationMeta
    AgentState --> ToolResult
    SessionManager <-- ContextManager : uses
    ToolRegistry --> BaseTool : registers 7 tools
    CompiledGraph --> AgentState : manages
    CompiledGraph --> BaseTool : calls via ToolNode
    
    note for BaseTool "track_analyze\nweather_query\ntransport_route\nweb_search\nreport_generate\nroute_save\nroute_search"
```

---

## 4. LangGraph 状态机图 (State Diagram)

```mermaid
stateDiagram-v2
    [*] --> AgentNode : 用户发送消息
    
    state AgentNode {
        [*] --> BuildMessages : 加载历史 + 系统提示
        BuildMessages --> CallLLM : 调用 LLM
        CallLLM --> CheckToolCalls : 解析响应
    }
    
    AgentNode --> ToolNode : 有 tool_calls
    AgentNode --> [*] : 无 tool_calls (直接回复)
    
    state ToolNode {
        [*] --> ParseToolCall
        ParseToolCall --> ExecuteTool
        ExecuteTool --> ReturnResult
        state "工具列表" as Tools {
            track_analyze
            weather_query
            transport_route
            web_search
            report_generate
            route_save
            route_search
        }
        ExecuteTool --> Tools
        Tools --> ReturnResult
    }
    
    ToolNode --> AgentNode : 工具结果追加到 messages
    
    note right of AgentNode
        LLM = ChatOpenAI
        model = Kimi-K2.5
        base_url = SiliconFlow
    end note
    
    note right of ToolNode
        使用 LangGraph 内置 ToolNode
        同步调用现有 Service 层
    end note
```

---

## 5. Chat SSE 交互时序图 (Sequence Diagram)

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant API as FastAPI ChatRouter
    participant SM as SessionManager
    participant Agent as LangGraph Agent
    participant LLM as SiliconFlow LLM
    participant Tools as ToolNode
    participant Redis as Redis/InMemory
    participant Mongo as MongoDB
    
    User->>FE: 打开 /chat
    FE->>API: POST /chat/sessions
    API->>SM: create_session(session_id, user_id)
    SM->>Redis: SET session:xxx:meta
    SM->>Redis: SET session:xxx:messages []
    Redis-->>SM: OK
    SM-->>API: session created
    API-->>FE: {session_id, created_at}
    
    User->>FE: 输入消息 "帮我分析这个轨迹"
    FE->>API: POST /chat/sessions/{id}/messages<br/>Content-Type: application/json<br/>body: {message: "..."}
    
    Note over API,FE: SSE 连接建立
    
    API->>SM: get_session() 验证归属
    API->>SM: append_message(session_id, "user", msg)
    SM->>Redis: GET/SET session:xxx:messages
    
    API->>SM: get_messages(session_id)
    SM-->>API: 历史消息列表
    API->>Agent: agent.astream_events({messages})
    
    Agent->>LLM: ChatOpenAI.invoke(messages)
    
    loop SSE 流式传输
        LLM-->>Agent: token chunk
        Agent-->>API: on_chat_model_stream
        API-->>FE: event: token\ndata: {"content": "..."}
    end
    
    alt LLM 返回 tool_calls
        Agent-->>API: on_tool_start
        API-->>FE: event: tool_start\ndata: {"tool": "track_analyze"}
        Agent->>Tools: 执行工具
        Tools-->>Agent: 工具结果
        Agent-->>API: on_tool_end
        API-->>FE: event: tool_end\ndata: {"tool": "track_analyze", "output": "..."}
        Agent->>LLM: 再次调用 (带工具结果)
        LLM-->>Agent: 最终回复
    end
    
    Agent-->>API: stream 完成
    API-->>FE: event: done\ndata: {}
    
    API->>SM: append_message(session_id, "assistant", full_reply)
    SM->>Redis: SET session:xxx:messages
    
    Note over FE: 渲染消息气泡 + 工具卡片
```

---

## 6. 报告生成编排时序图 (Orchestrator Sequence)

```mermaid
sequenceDiagram
    actor User
    participant Tool as report_generate Tool
    participant Orch as OutdoorPlannerRouter
    participant Track as TrackService
    participant Weather as WeatherService
    participant Transport as TransportService
    participant Search as SearchService
    participant LLM as LLMService
    participant Prompt as PromptManager
    participant Mongo as MongoDB
    
    User->>Tool: 触发报告生成
    Tool->>Orch: execute_planning(trip_date, departure, gpx_path, ...)
    
    rect rgb(232, 245, 233)
        Note over Orch,Track: Step 1: 轨迹分析
        Orch->>Track: analyze(gpx_path)
        Track-->>Orch: TrackAnalysis (距离/海拔/难度)
        Orch->>Track: correct_coordinates(analysis)
    end
    
    rect rgb(227, 242, 253)
        Note over Orch,Weather: Step 2: 天气查询
        Orch->>Weather: get_summary(lon, lat, date)
        Weather-->>Orch: WeatherSummary (逐小时/多日/格点)
    end
    
    rect rgb(243, 229, 245)
        Note over Orch,Transport: Step 3: 交通规划
        Orch->>Transport: plan(departure, destination)
        Transport-->>Orch: TransportResult (驾车/步行路线)
    end
    
    rect rgb(255, 243, 224)
        Note over Orch,Search: Step 4: 周边搜索
        Orch->>Search: search(keywords, types)
        Search-->>Orch: SearchResult (POI 列表)
    end
    
    rect rgb(255, 235, 238)
        Note over Orch,LLM: Step 5: LLM 综合生成
        Orch->>Prompt: get_prompt("outdoor_planning")
        Prompt-->>Orch: 系统提示词模板
        Orch->>LLM: generate(prompt + 全部数据)
        LLM-->>Orch: OutdoorActivityPlan (完整策划书)
    end
    
    Orch-->>Tool: plan 对象
    Tool-->>User: "策划书生成成功！是否保存？"
    
    Note over Tool,Mongo: 保存流程（用户确认后）
    Tool->>Mongo: report_repo.create(plan)
```

---

## 7. 前端组件树 (Component Diagram)

```mermaid
graph TB
    subgraph "App Root"
        App["App.tsx<br/>BrowserRouter"]
        AuthCtx["AuthProvider<br/>AuthContext"]
        QuotaCtx["QuotaProvider<br/>QuotaContext"]
    end
    
    subgraph "Public Routes"
        PublicLayout["PublicLayout"]
        HomePage["HomePage /"]
        LoginPage["LoginPage /auth/login"]
        RegisterPage["RegisterPage /auth/register"]
    end
    
    subgraph "Protected Routes"
        ProtectedLayout["ProtectedLayout"]
        ChatPage["ChatPage /chat"]
        ReportListPage["ReportListPage /reports"]
        ReportDetailPage["ReportDetailPage /reports/:id"]
        ProfilePage["ProfilePage /profile"]
        ChangePwdPage["ChangePasswordPage /profile/password"]
        ToolsPage["ToolsPage /tools"]
        UserMgmtPage["UserManagementPage /admin/users"]
        
        subgraph "Tool Pages"
            TrackPage["TrackAnalysisPage /tools/track"]
            WeatherPage["WeatherQueryPage /tools/weather"]
            TransportPage["TransportPage /tools/transport"]
            SearchPage["SearchPage /tools/search"]
        end
    end
    
    subgraph "Chat Components"
        ChatSidebar["ChatSidebar"]
        MessageList["MessageList"]
        MessageBubble["MessageBubble"]
        ToolCallCard["ToolCallCard"]
        ChatInput["ChatInput"]
    end
    
    subgraph "Shared Components"
        HeroSection["HeroSection"]
        ElevationChart["ElevationChart"]
        RouteBrief["RouteBrief"]
        TrackDetailSection["TrackDetailSection"]
        ProtectedRoute["ProtectedRoute"]
    end
    
    App --> AuthCtx
    AuthCtx --> QuotaCtx
    QuotaCtx --> PublicLayout
    QuotaCtx --> ProtectedLayout
    
    PublicLayout --> HomePage
    PublicLayout --> LoginPage
    PublicLayout --> RegisterPage
    
    ProtectedLayout --> ProtectedRoute
    ProtectedRoute --> ChatPage
    ProtectedRoute --> ReportListPage
    ProtectedRoute --> ReportDetailPage
    ProtectedRoute --> ProfilePage
    ProtectedRoute --> ChangePwdPage
    ProtectedRoute --> ToolsPage
    ProtectedRoute --> UserMgmtPage
    
    ToolsPage --> TrackPage
    ToolsPage --> WeatherPage
    ToolsPage --> TransportPage
    ToolsPage --> SearchPage
    
    ChatPage --> ChatSidebar
    ChatPage --> MessageList
    MessageList --> MessageBubble
    MessageList --> ToolCallCard
    ChatPage --> ChatInput
    
    HomePage --> HeroSection
    ReportDetailPage --> RouteBrief
    ReportDetailPage --> TrackDetailSection
    TrackDetailSection --> ElevationChart
    
    style ChatPage fill:#ff9800,color:#000
    style ChatInput fill:#ff9800,color:#000
    style MessageBubble fill:#ff9800,color:#000
    style ToolCallCard fill:#ff9800,color:#000
```

---

## 8. 前端 API 层 (API Client Architecture)

```mermaid
graph TB
    subgraph "Pages (消费者)"
        HP[HomePage]
        LP[LoginPage]
        RP[ReportListPage]
        CP[ChatPage]
        PP[ProfilePage]
    end
    
    subgraph "API 客户端层"
        client["client.ts<br/>Axios Instance<br/>baseURL=/api/v1<br/>+ JWT Interceptor"]
        auth["auth.ts<br/>login/register/sms<br/>phone bind/unbind<br/>password change"]
        plan["plan.ts<br/>generate (multipart)"]
        reports["reports.ts<br/>list/get/delete"]
        quota["quota.ts<br/>getQuota"]
        chat["chat.ts<br/>createSession<br/>getSessions<br/>uploadTrack"]
        sse["sse.ts<br/>streamChatMessage<br/>SSE Event Parser"]
    end
    
    subgraph "SSE 事件类型"
        token["event: token<br/>onToken(content)"]
        tool_start["event: tool_start<br/>onToolStart(tool, input)"]
        tool_end["event: tool_end<br/>onToolEnd(tool, output)"]
        done["event: done<br/>onDone()"]
        error["event: error<br/>onError(message)"]
    end
    
    subgraph "Contexts"
        AuthCtx["AuthContext<br/>login/logout/updateUser"]
        QuotaCtx["QuotaContext<br/>fetchQuota"]
    end
    
    HP --> plan
    LP --> auth
    RP --> reports
    CP --> chat
    CP --> sse
    PP --> auth
    
    auth --> client
    plan --> client
    reports --> client
    quota --> client
    
    chat -->|"Native fetch<br/>(not Axios)"| Backend["Backend API"]
    sse -->|"ReadableStream<br/>SSE Parser"| Backend
    
    sse --> token
    sse --> tool_start
    sse --> tool_end
    sse --> done
    sse --> error
    
    AuthCtx --> auth
    AuthCtx --> client
    QuotaCtx --> quota
    
    style sse fill:#ff9800,color:#000
    style chat fill:#ff9800,color:#000
    style token fill:#4caf50,color:#fff
    style tool_start fill:#2196f3,color:#fff
    style tool_end fill:#2196f3,color:#fff
```

---

## 9. 数据库 Schema 图 (Multi-Database Schema)

```mermaid
erDiagram
    subgraph "MySQL (关系数据)"
        USER {
            int id PK
            string username
            string phone "UK, nullable"
            string password_hash
            string role "user|admin"
            string status "active|disabled"
            datetime created_at
            datetime updated_at
            datetime last_login_at
        }
        QUOTA_USAGE {
            int id PK
            int user_id FK
            date usage_date
            int used_count
            string created_at
        }
        SMS_CODE {
            int id PK
            string phone
            string code
            string purpose
            datetime expires_at
            boolean used
        }
        SMS_SEND_LOG {
            int id PK
            string phone
            string purpose
            string template_id
            boolean success
            datetime created_at
        }
        USER ||--o{ QUOTA_USAGE : "每日额度"
        USER ||--o{ SMS_CODE : "验证码"
    end
    
    subgraph "MongoDB (文档数据)"
        REPORT {
            string _id PK
            int user_id FK
            string plan_name
            string trip_date
            string overall_rating
            object content "完整策划书JSON"
            datetime created_at
            datetime updated_at
        }
        USER_MEMORY {
            string _id PK
            int user_id FK
            object preferences "用户偏好"
            array facts "提取的事实"
            datetime updated_at
        }
    end
    
    subgraph "PostgreSQL + PostGIS (空间数据)"
        ROUTE {
            int id PK
            int user_id FK
            string name
            float start_lon
            float start_lat
            float end_lon
            float end_lat
            float total_distance_km
            float total_ascent_m
            string difficulty
            string region
            datetime created_at
        }
    end
    
    subgraph "Redis (缓存)"
        SESSION_META {
            string key "session:{id}:meta"
            string value "JSON {user_id, created_at}"
            int ttl "86400s"
        }
        SESSION_MESSAGES {
            string key "session:{id}:messages"
            string value "JSON array"
            int ttl "86400s"
        }
        SESSION_ATTACHMENT {
            string key "session:{id}:attachment:{key}"
            string value "string"
            int ttl "86400s"
        }
    end
```

---

## 10. API 端点全景图 (API Endpoint Map)

```mermaid
graph LR
    subgraph "认证 /auth"
        A1["POST /login"]
        A2["POST /register"]
        A3["POST /sms/login"]
        A4["POST /sms/register"]
        A5["POST /sms/send"]
        A6["GET /me"]
        A7["POST /password/change"]
        A8["POST /phone/bind"]
        A9["POST /phone/unbind"]
        A10["POST /check-exists"]
    end
    
    subgraph "智能对话 /chat"
        C1["POST /sessions"]
        C2["GET /sessions"]
        C3["POST /sessions/{id}/messages<br/>⚠️ SSE"]
        C4["POST /sessions/{id}/upload"]
    end
    
    subgraph "规划 /plan"
        P1["POST /generate<br/>multipart/form-data"]
    end
    
    subgraph "报告 /reports"
        R1["GET /"]
        R2["GET /{id}"]
        R3["DELETE /{id}"]
    end
    
    subgraph "工具箱"
        T1["POST /track/analyze"]
        T2["POST /weather/query"]
        T3["POST /transport/plan"]
        T4["POST /search/query"]
    end
    
    subgraph "额度 /quota"
        Q1["GET /"]
    end
    
    subgraph "管理 /users"
        U1["GET /"]
        U2["PATCH /{id}/status"]
    end
    
    style C1 fill:#ff9800,color:#000
    style C2 fill:#ff9800,color:#000
    style C3 fill:#ff9800,color:#000
    style C4 fill:#ff9800,color:#000
    style P1 fill:#9c27b0,color:#fff
```

---

## 11. 双路径架构对比 (Before vs After)

```mermaid
graph LR
    subgraph "原有路径：表单式"
        direction TB
        F1["HomePage 表单"] -->|POST multipart| F2["plan/generate"]
        F2 --> F3["Orchestrator<br/>串行编排"]
        F3 --> F4["完整策划报告"]
    end
    
    subgraph "新增路径：对话式"
        direction TB
        A1["ChatPage 对话"] -->|SSE| A2["Agent Graph"]
        A2 --> A3["渐进式工具调用"]
        A3 --> A4["实时流式反馈"]
        A2 --> A5["report_generate<br/>= 其中一个 Tool"]
        A5 --> A4
    end
    
    F4 -.->|"报告存储"| DB[("MongoDB")]
    A4 -.->|"报告存储"| DB
    
    style A2 fill:#ff9800,color:#000
    style A3 fill:#ff9800,color:#000
    style A5 fill:#ff5722,color:#fff
    style F3 fill:#9c27b0,color:#fff
```

---

## 12. 部署架构图 (Deployment Diagram)

```mermaid
graph TB
    subgraph "Docker Compose"
        subgraph "Frontend Container"
            Nginx["Nginx<br/>:80<br/>静态文件 + 反向代理"]
        end
        
        subgraph "Backend Container"
            Uvicorn["Uvicorn<br/>:8000<br/>FastAPI + Agent"]
        end
        
        subgraph "Data Services"
            MySQLC["MySQL 8<br/>:3306"]
            MongoC["MongoDB 7<br/>:27017"]
            RedisC["Redis 7<br/>:6379"]
            PGC["PostgreSQL 16<br/>+ PostGIS 3.4<br/>:5432"]
        end
    end
    
    Internet((Internet))
    User[👤]
    
    User --> Internet
    Internet --> Nginx
    Nginx -->|/api/*| Uvicorn
    Nginx -->|/*| Nginx
    
    Uvicorn --> MySQLC
    Uvicorn --> MongoC
    Uvicorn --> RedisC
    Uvicorn --> PGC
    
    subgraph "外部 API"
        QW[和风天气]
        AM[高德地图]
        SF[SiliconFlow]
        AL[阿里云短信]
    end
    
    Uvicorn --> QW
    Uvicorn --> AM
    Uvicorn --> SF
    Uvicorn --> AL
    
    style Uvicorn fill:#009688,color:#fff
    style Nginx fill:#009688,color:#fff
```
