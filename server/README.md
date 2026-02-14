# Newsloom FastAPI Server

FastAPI 后端 API 服务，为 Newsloom 前端 Dashboard 提供数据接口。

## 功能特性

- ✅ RESTful API（报告查询、数据源管理、Pipeline 控制）
- ✅ WebSocket 实时推送（Pipeline 进度）
- ✅ SQLite + SQLAlchemy 异步 ORM
- ✅ 自动 API 文档（Swagger UI）
- ✅ CORS 支持（localhost:3000）
- ✅ Pipeline 后台执行

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `fastapi` - Web 框架
- `uvicorn[standard]` - ASGI 服务器
- `sqlalchemy[asyncio]` - 异步 ORM
- `aiosqlite` - 异步 SQLite 驱动
- `pydantic-settings` - 配置管理
- `websockets` - WebSocket 支持

### 2. 启动服务器

```bash
python -m server.main
```

服务器将在 `http://localhost:8080` 启动。

### 3. 访问 API 文档

打开浏览器访问：
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## API 端点

### Reports（报告）

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reports/` | 获取所有报告（分页） |
| GET | `/api/v1/reports/latest` | 获取最新报告 |
| GET | `/api/v1/reports/{date}` | 获取指定日期的报告 |
| POST | `/api/v1/reports/{date}/sync` | 从文件同步报告到数据库 |

### Pipeline（Pipeline 控制）

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/pipeline/run` | 触发 Pipeline 执行 |
| GET | `/api/v1/pipeline/status` | 获取当前 Pipeline 状态 |
| GET | `/api/v1/pipeline/history` | 获取 Pipeline 执行历史 |
| GET | `/api/v1/pipeline/run/{run_id}` | 获取指定 run 的详情 |
| POST | `/api/v1/pipeline/run/{run_id}/sync-report` | Pipeline 完成后同步报告 |

### Sources（数据源管理）

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sources/` | 获取所有数据源 |
| GET | `/api/v1/sources/{id}` | 获取单个数据源 |
| POST | `/api/v1/sources/` | 创建新数据源 |
| PUT | `/api/v1/sources/{id}` | 更新数据源配置 |
| DELETE | `/api/v1/sources/{id}` | 删除数据源 |
| POST | `/api/v1/sources/{id}/toggle` | 开关数据源 |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8080/ws` | 实时 Pipeline 进度推送 |

WebSocket 消息格式：
```json
{
  "type": "status|progress|log|error",
  "data": {...},
  "timestamp": "2026-02-15T12:00:00"
}
```

## 数据库

### 表结构

- **reports** - 日报元数据
- **articles** - 文章详情（关联到报告）
- **pipeline_runs** - Pipeline 执行记录
- **source_configs** - 数据源配置
- **settings** - 应用设置

数据库文件：`./data/newsloom.db`

### 数据同步

Pipeline 执行后需要将生成的报告同步到数据库：

```bash
# 方法 1: API 调用
curl -X POST http://localhost:8080/api/v1/reports/2026-02-15/sync

# 方法 2: Pipeline 完成后自动调用
curl -X POST http://localhost:8080/api/v1/pipeline/run/1/sync-report
```

## 使用示例

### 1. 触发 Pipeline 执行

```bash
curl -X POST http://localhost:8080/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "layers": ["fetch", "rank", "analyze", "generate"],
    "date": null
  }'
```

返回：
```json
{
  "id": 1,
  "date": "2026-02-15",
  "status": "running",
  "progress_percent": 0,
  ...
}
```

### 2. 查询最新报告

```bash
curl http://localhost:8080/api/v1/reports/latest
```

### 3. WebSocket 监听进度

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(msg.type, msg.data);
};

// 心跳
setInterval(() => ws.send('ping'), 30000);
```

## 配置

配置文件：`server/config.py`

主要配置项：
- `host` - 服务器地址（默认 0.0.0.0）
- `port` - 端口（默认 8080）
- `cors_origins` - CORS 白名单
- `db_url` - 数据库连接
- `reports_dir` - 报告文件目录

可通过环境变量覆盖：
```bash
export PORT=8000
export DEBUG=false
python -m server.main
```

## 开发

### 项目结构

```
server/
├── __init__.py
├── main.py              # FastAPI app 入口
├── config.py            # 配置管理
├── database.py          # 数据库模型
├── schemas.py           # Pydantic schemas
├── routers/
│   ├── reports.py       # 报告路由
│   ├── sources.py       # 数据源路由
│   ├── pipeline.py      # Pipeline 路由
│   └── ws.py            # WebSocket 路由
└── services/
    ├── pipeline_service.py  # Pipeline 服务
    └── report_service.py   # 报告服务
```

### 运行测试

```bash
pytest server/tests/
```

### 热重载开发模式

服务器默认启用热重载（`reload=True`），代码修改后自动重启。

## 故障排除

### 端口被占用

修改 `server/config.py` 中的 `port` 或使用环境变量：
```bash
export PORT=8081
python -m server.main
```

### 数据库锁定

确保没有其他进程访问 `./data/newsloom.db`：
```bash
fuser data/newsloom.db  # Linux
lsof data/newsloom.db   # macOS
```

### Pipeline 无法导入

确保 `src/` 目录在 Python path 中。服务启动时会自动添加。

## 生产部署

### 使用 Gunicorn + Uvicorn workers

```bash
gunicorn server.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080
```

### 使用 Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "server.main"]
```

### Nginx 反向代理

```nginx
location /api {
    proxy_pass http://localhost:8080;
    proxy_set_header Host $host;
}

location /ws {
    proxy_pass http://localhost:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## License

MIT
