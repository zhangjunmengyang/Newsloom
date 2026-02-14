# Newsloom 深度迭代路线图

> **创建时间**: 2026-02-15 01:45 CST
> **目标**: 24h 极限挑战，将 Newsloom 从 MVP 打磨为真正有竞争力的产品

---

## 现状分析

### 我们有什么
- ✅ 4层 Pipeline 架构 (Fetch → Filter → Analyze → Generate)
- ✅ 5个数据源 (RSS/arXiv/GitHub/HN/ProductHunt)
- ✅ Claude 双Pass AI 分析
- ✅ MD + HTML + PDF 输出
- ✅ Cron 自动运行 + Discord 推送
- ✅ 完整 PRD (含前端 8页详细设计)

### 差距在哪
| 维度 | 当前状态 | twitter-watchdog | 我们的目标 |
|------|----------|------------------|-----------|
| 数据源 | 5个(无Twitter) | Twitter 专精 | 7+ 源(含Twitter) |
| 前端 | ❌ 无 | ✅ HTML报告+导航 | ✅ Next.js Dashboard |
| 三层分离 | ❌ 耦合 | ✅ scrape/analyze/report | ✅ 独立可组合 |
| 周报/月报 | ❌ | ✅ 自动聚合 | ✅ 智能聚合 |
| 报告质量 | 中等 | 中等 | 高(洞察+评分+趋势) |
| CLI 工具 | ❌ | ✅ 子命令 | ✅ news CLI |
| 部署体验 | 手动 | 简单 | 一键部署 |
| 实时性 | 每天1次 | 每天4次 | 按需+定时 |

### 竞品亮点借鉴
1. **twitter-watchdog**: 三层独立架构(scrape/analyze/report)、周报月报自动聚合、HTML暗色报告、图片下载
2. **rauchg/next-ai-news**: Next.js 14 + RSC + Drizzle ORM + shadcn/ui, Vercel 部署
3. **kaiban-agents-aggregator**: 多 Agent 协作、React UI、实时可视化工作流
4. **News-Aggregator-with-Chatbot**: RAG 聊天机器人、内容聚类、Docker 部署

---

## 24h 迭代优先级

### 🔴 Sprint 1: 后端 API 层 (4-6h)
> Pipeline 已有，包一层 FastAPI 让前端能调用

**任务清单:**
1. FastAPI 骨架 + 路由设计
2. 报告 CRUD API (`/api/v1/reports`)
3. 数据源管理 API (`/api/v1/sources`)
4. Pipeline 触发 API (`/api/v1/pipeline/run`)
5. WebSocket 实时状态推送
6. SQLite 数据层 (报告元数据 + 文章表 + 运行记录)
7. JWT 基础认证

**产出:** 能跑的 FastAPI server，`news serve` 启动

### 🔴 Sprint 2: 前端 MVP (6-8h)
> 参考 PRD，做 Dashboard + 报告阅读器 + 数据源管理

**任务清单:**
1. Next.js 15 项目初始化 + Tailwind + shadcn/ui
2. Layout: Sidebar + Header + 暗色主题
3. Dashboard 页面 (统计卡片 + 今日精选 + 数据源状态 + 趋势图)
4. 报告阅读器 (沉浸式阅读 + Section 切换 + 搜索)
5. 数据源管理页 (列表 + 添加/编辑/禁用)
6. Pipeline 运行页 (触发 + 实时进度)

**产出:** 可以在浏览器里看报告、管理数据源

### 🟡 Sprint 3: Pipeline 质量提升 (3-4h)
> 信息质量是核心竞争力

**任务清单:**
1. Executive Summary 升级 — 30秒速览今日核心
2. 重要性评分 (🔴必读/🟡推荐/🟢了解)
3. "So What" 洞察 — 每条新闻加一句"对你意味着什么"
4. 趋势检测 — 跨天对比，发现热度上升的话题
5. 同源去重 — 同一事件多源报道聚合
6. Discord 推送优化 — embed 格式、分 section 发送

### 🟡 Sprint 4: CLI 工具 (2-3h)
> `news` 命令行，开发者友好

**任务清单:**
1. Click CLI 骨架
2. `news` — 今日摘要
3. `news run` — 运行 pipeline
4. `news status` — 系统状态
5. `news serve` — 启动 Dashboard
6. `news history` — 历史报告
7. `news sources` — 数据源管理

### 🟢 Sprint 5: 数据源扩展 (2-3h)
1. Twitter 数据源对接 (参考 twitter-watchdog 的 twitterapi.io)
2. 周报/月报自动聚合
3. RSS feed 输出 (让别人能订阅)

---

## 技术决策

### 前端
- **Next.js 15** (App Router + RSC) — 与 PRD 一致
- **shadcn/ui + Tailwind** — 快速出活、暗色优先
- **Zustand** 状态管理
- **Recharts** 图表
- **pnpm** 包管理

### 后端
- **FastAPI** — 异步、OpenAPI 自动生成
- **SQLite** — 零配置，够用
- **SQLAlchemy 2.0** — 异步 ORM
- **APScheduler** — 定时任务

### 部署
- 前端: `next build` + 静态导出 or Vercel
- 后端: `uvicorn` + systemd/launchd
- Docker: `docker-compose.yml` 一键启动

---

## 执行策略

1. **所有编码通过 Claude Code 完成** — 我做架构设计和任务拆分，CC 写代码
2. **每个 Sprint 是一个独立的 CC 任务** — 清晰的 prompt + 上下文
3. **Sprint 间做 code review** — 确保质量和一致性
4. **心跳驱动** — 每次心跳推进一个子任务
5. **优先可见成果** — 先让东西跑起来，再打磨细节

---

## 产品愿景延伸

### 超越简报的方向
1. **RAG 问答** — "上周 AI 领域最重要的 3 件事是什么？"
2. **趋势仪表盘** — 关键词热度曲线、情感指数
3. **个性化推荐** — 根据阅读行为学习偏好
4. **协作空间** — 团队共享 + 标注 + 讨论
5. **API 开放** — 让其他工具能消费 Newsloom 的数据
6. **移动端** — PWA or React Native

### 商业化路径
- 开源免费版 (个人使用)
- Pro 版 (团队 + 高级分析 + 自定义源)
- SaaS (全托管零部署)

---

_This is a living document. Updated as we execute._
