# Newsloom FastAPI 后端搭建完成 ✅

## 项目概览

已为 Newsloom 项目成功搭建 FastAPI 后端 API 层，作为前端 Dashboard 的数据接口。

## 📁 目录结构

```
Newsloom/
├── server/                      # 🆕 FastAPI 后端
│   ├── __init__.py
│   ├── main.py                  # FastAPI app 入口
│   ├── config.py                # 服务器配置
│   ├── database.py              # SQLAlchemy 异步模型
│   ├── schemas.py               # Pydantic schemas
│   ├── README.md                # 详细文档
│   ├── routers/                 # API 路由
│   │   ├── reports.py           # 报告 CRUD
│   │   ├── sources.py           # 数据源管理
│   │   ├── pipeline.py          # Pipeline 控制
│   │   └── ws.py                # WebSocket 实时推送
│   └── services/                # 业务逻辑
│       ├── pipeline_service.py  # Pipeline 后台执行
│       └── report_service.py    # 报告查询服务
├── src/                         # 现有 Pipeline 代码
├── data/
│   └── newsloom.db              # 🆕 SQLite 数据库
├── start_server.sh              # 🆕 启动脚本
├── requirements.txt             # 🆕 更新（添加 FastAPI 依赖）
└── ...
```

## ✨ 核心功能

### 1️⃣ RESTful API

#### 报告接口 (`/api/v1/reports`)
- `GET /api/v1/reports/` - 获取所有报告（分页）
- `GET /api/v1/reports/latest` - 获取最新报告
- `GET /api/v1/reports/{date}` - 获取指定日期报告
- `POST /api/v1/reports/{date}/sync` - 同步报告到数据库

#### Pipeline 接口 (`/api/v1/pipeline`)
- `POST /api/v1/pipeline/run` - 触发 Pipeline 执行（后台运行）
- `GET /api/v1/pipeline/status` - 获取当前状态
- `GET /api/v1/pipeline/history` - 执行历史
- `GET /api/v1/pipeline/run/{run_id}` - 获取指定 run 详情
- `POST /api/v1/pipeline/run/{run_id}/sync-report` - 同步生成的报告

#### 数据源接口 (`/api/v1/sources`)
- `GET /api/v1/sources/` - 获取所有数据源
- `POST /api/v1/sources/` - 创建数据源
- `PUT /api/v1/sources/{id}` - 更新数据源
- `DELETE /api/v1/sources/{id}` - 删除数据源
- `POST /api/v1/sources/{id}/toggle` - 开关数据源

### 2️⃣ WebSocket 实时推送

- `ws://localhost:8080/ws` - Pipeline 进度实时推送

消息格式：
```json
{
  "type": "status|progress|log|error",
  "data": {
    "run_id": 1,
    "status": "running",
    "current_layer": "analyze",
    "progress_percent": 50
  },
  "timestamp": "2026-02-15T12:00:00"
}
```

### 3️⃣ 数据库（SQLite + SQLAlchemy Async）

#### 数据表
- **reports** - 日报元数据（日期、标题、摘要、文件路径、统计）
- **articles** - 文章详情（标题、URL、brief、priority、tags、评分）
- **pipeline_runs** - Pipeline 执行记录（状态、进度、耗时、错误）
- **source_configs** - 数据源配置（可通过 API 管理）
- **settings** - 应用设置（key-value 存储）

### 4️⃣ Pipeline 后台执行

- 使用 `ThreadPoolExecutor` 在后台线程运行 `PipelineV2`
- 不阻塞 API 请求
- 通过 WebSocket 实时推送进度
- 执行状态：`running`, `success`, `failed`, `timeout`

### 5️⃣ CORS 支持

默认允许：
- `http://localhost:3000`
- `http://127.0.0.1:3000`

可在 `server/config.py` 修改。

### 6️⃣ 自动 API 文档

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 🚀 快速开始

### 方法 1: 使用启动脚本（推荐）

```bash
./start_server.sh
```

### 方法 2: 手动启动

```bash
# 1. 安装依赖（如未安装）
pip install -r requirements.txt

# 2. 启动服务器
python -m server.main
```

服务器将在 `http://localhost:8080` 启动。

## 📝 使用示例

### 1. 触发 Pipeline 执行

```bash
curl -X POST http://localhost:8080/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "layers": ["fetch", "rank", "analyze", "generate"]
  }'
```

响应：
```json
{
  "id": 1,
  "date": "2026-02-15",
  "status": "running",
  "layers": ["fetch", "rank", "analyze", "generate"],
  "progress_percent": 0,
  "started_at": "2026-02-15T12:00:00"
}
```

### 2. 查询最新报告

```bash
curl http://localhost:8080/api/v1/reports/latest
```

响应：
```json
{
  "id": 1,
  "date": "2026-02-14",
  "title": "Newsloom 每日情报 2026-02-14",
  "executive_summary": "...",
  "total_articles": 120,
  "articles": [
    {
      "id": 1,
      "title": "Claude 4.6 Released",
      "brief": "Anthropic 发布 Claude 4.6...",
      "priority": "🔴",
      "tags": ["AI", "LLM"],
      "url": "https://...",
      ...
    }
  ],
  ...
}
```

### 3. WebSocket 监听进度

```javascript
// 前端代码
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  if (msg.type === 'progress') {
    console.log(`Pipeline ${msg.data.status}: ${msg.data.progress_percent}%`);
    console.log(`Current layer: ${msg.data.current_layer}`);
  }
};

// 心跳保活
setInterval(() => ws.send('ping'), 30000);
```

### 4. 同步报告到数据库

Pipeline 执行完成后：

```bash
# 方法 1: 根据日期同步
curl -X POST http://localhost:8080/api/v1/reports/2026-02-15/sync

# 方法 2: 根据 run_id 同步
curl -X POST http://localhost:8080/api/v1/pipeline/run/1/sync-report
```

## 🔧 配置

配置文件：`server/config.py`

```python
class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = True

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    db_url: str = "sqlite+aiosqlite:///./data/newsloom.db"
    ...
```

可通过环境变量覆盖：
```bash
export PORT=8000
export DEBUG=false
python -m server.main
```

## 📦 依赖更新

`requirements.txt` 新增：
```
# FastAPI and server dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy[asyncio]>=2.0.0
aiosqlite>=0.19.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-multipart>=0.0.6
websockets>=12.0
```

## 🎯 前端集成建议

### API 客户端（TypeScript）

```typescript
// api/client.ts
const API_BASE = 'http://localhost:8080';

export const api = {
  // Reports
  getLatestReport: () =>
    fetch(`${API_BASE}/api/v1/reports/latest`).then(r => r.json()),

  getReportByDate: (date: string) =>
    fetch(`${API_BASE}/api/v1/reports/${date}`).then(r => r.json()),

  // Pipeline
  runPipeline: (layers: string[], date?: string) =>
    fetch(`${API_BASE}/api/v1/pipeline/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ layers, date }),
    }).then(r => r.json()),

  getPipelineStatus: () =>
    fetch(`${API_BASE}/api/v1/pipeline/status`).then(r => r.json()),
};
```

### WebSocket Hook（React）

```typescript
// hooks/usePipelineProgress.ts
import { useEffect, useState } from 'react';

export function usePipelineProgress() {
  const [progress, setProgress] = useState(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8080/ws');

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'progress') {
        setProgress(msg.data);
      }
    };

    const heartbeat = setInterval(() => ws.send('ping'), 30000);

    return () => {
      ws.close();
      clearInterval(heartbeat);
    };
  }, []);

  return progress;
}
```

## 🧪 测试

### 健康检查

```bash
curl http://localhost:8080/health
# 响应: {"status": "healthy"}
```

### API 文档

访问 http://localhost:8080/docs 可以：
- 查看所有 API 端点
- 在线测试 API
- 查看 schema 定义

## 📊 数据流

```
前端 Dashboard
    ↓ HTTP POST /api/v1/pipeline/run
FastAPI Server
    ↓ 创建 PipelineRun 记录（status=running）
    ↓ 后台 ThreadPool 执行
PipelineV2 (src/pipeline_v2.py)
    ↓ Fetch → Rank → Analyze → Generate
    ↓ 生成文件到 reports/2026-02-15/
FastAPI Server
    ↓ 更新 PipelineRun（status=success）
    ↓ 调用 sync-report API
    ↓ 读取 analyzed JSON + 报告文件
    ↓ 写入 reports 和 articles 表
前端 Dashboard
    ↓ GET /api/v1/reports/latest
    ↓ 展示报告 + 文章列表
```

## 🐛 故障排除

### 端口占用

```bash
# 修改端口
export PORT=8081
python -m server.main
```

### 数据库锁定

```bash
# 确保没有其他进程访问
rm data/newsloom.db  # 删除并重新初始化
python -m server.main
```

### Pipeline 导入失败

确保在项目根目录运行：
```bash
cd /Users/peterzhang/project/Newsloom
python -m server.main
```

## 📚 更多文档

详细文档请参考：
- [server/README.md](server/README.md) - 完整 API 文档
- http://localhost:8080/docs - 在线 API 文档
- [src/pipeline_v2.py](src/pipeline_v2.py) - Pipeline 实现

## ✅ 验证清单

- [x] FastAPI app 可以成功导入
- [x] 数据库表自动创建（5 张表）
- [x] 22 个路由已注册
- [x] WebSocket 端点已配置
- [x] CORS 已启用
- [x] Pipeline 后台执行服务已实现
- [x] Report 同步服务已实现
- [x] 依赖已更新到 requirements.txt
- [x] 启动脚本已创建
- [x] README 文档已完成

## 🎉 总结

Newsloom FastAPI 后端已完成搭建，包含：
- ✅ 完整的 RESTful API
- ✅ WebSocket 实时推送
- ✅ SQLite 异步数据库
- ✅ Pipeline 后台执行
- ✅ 自动 API 文档
- ✅ CORS 支持

**下一步：** 开发前端 Dashboard，使用这些 API 展示报告和控制 Pipeline。
