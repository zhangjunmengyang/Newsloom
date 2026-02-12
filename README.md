<div align="center">

# Newsloom 📰

### 多信息源智能日报系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/zhangjunmengyang/Newsloom?style=social)](https://github.com/zhangjunmengyang/Newsloom/stargazers)

[English](README_EN.md) | 简体中文

</div>

---

## 📖 简介

**Newsloom** 是一个生产级、AI 驱动的智能新闻聚合系统，能够从多个信息源（RSS、arXiv、GitHub、Twitter、HackerNews 等）自动抓取、过滤、分析内容，并生成精美的每日报告。

### ✨ 核心特性

- 🔌 **完全可插拔** - 模块化架构，轻松添加新数据源和过滤策略
- 🚀 **高性能并行** - ThreadPool 并发抓取，HackerNews 故事并发获取
- 🧠 **AI 智能分析** - Claude 双pass处理，提取高质量内容
- 🎨 **精美报告** - Markdown、专业暗色主题 HTML（侧边导航 + section 颜色区分）
- 💾 **智能状态管理** - 自动清理旧记录，跨运行去重
- ⚙️ **灵活配置** - YAML 驱动，支持环境变量和多配置文件
- 📊 **可视化输出** - 交互式 HTML 报告，响应式布局，支持主题切换
- 🔧 **易于扩展** - 清晰的插件系统，几行代码添加新功能
- 🌐 **多频道支持** - AI、Tech、Crypto、Finance、Papers、GitHub、Community

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                   DATA SOURCES (可插拔)                      │
│  Twitter │ RSS │ arXiv │ GitHub │ HN │ Reddit │ 自定义... │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: FETCH (并行多源抓取)                               │
│  - ThreadPoolExecutor 并行                                   │
│  - 统一 Item 格式                                            │
│  - 状态去重                                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: FILTER (智能过滤 - 可扩展)                         │
│  - 关键词评分                                                │
│  - 投票加权                                                  │
│  - 自定义策略                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: ANALYZE (AI 分析 - 即将推出)                       │
│  - Claude 双pass处理                                         │
│  - 结构化提取                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: GENERATE (多格式报告)                              │
│  - Markdown                                                  │
│  - HTML (亮/暗主题)                                          │
│  - PNG 卡片 (可选)                                           │
│  - RSS Feed                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/zhangjunmengyang/Newsloom.git
cd Newsloom

# 安装依赖
pip install -r requirements.txt

# (可选) 安装 Playwright 用于卡片渲染
playwright install chromium
```

### 基础使用

```bash
# 运行完整流程（4层 pipeline: fetch → filter → analyze → generate）
python3 run.py

# 只运行特定层
python3 run.py --layers fetch,filter,generate

# 指定日期
python3 run.py --date 2026-02-12

# 使用自定义配置
python3 run.py --config config/my_config.yaml
```

**环境变量配置** (在 `.env` 或 `/etc/environment`):

```bash
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 可选：使用代理
```

### 配置数据源

编辑 `config/sources.yaml`:

```yaml
sources:
  rss_tech:
    enabled: true           # 启用此数据源
    channel: "tech"         # 分类频道
    type: "rss"            # 数据源类型
    feeds:
      - url: "https://techcrunch.com/feed/"
        name: "TechCrunch"

  rss_crypto:
    enabled: true
    channel: "crypto"
    type: "rss"
    feeds:
      - url: "https://www.coindesk.com/arc/outboundfeeds/rss/"
        name: "CoinDesk"

  arxiv:
    enabled: true
    channel: "papers"
    type: "arxiv"
    categories: "cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG"

  github:
    enabled: true
    channel: "github"
    type: "github"
    language: "python"
    period: "daily"

  hackernews:
    enabled: true
    channel: "community"
    type: "hackernews"
    min_score: 100
    count: 20
```

### 配置过滤规则

编辑 `config/filters.yaml`:

```yaml
channels:
  ai:
    strategy: keyword_score  # 过滤策略
    min_score: 4            # 最低分数
    keywords:
      llm: 5                # 关键词权重
      gpt: 4
      claude: 4
      transformer: 5
    blacklist:
      - spam                # 黑名单

  crypto:
    strategy: keyword_score
    min_score: 4
    keywords:
      bitcoin: 5
      ethereum: 5
      blockchain: 5
      defi: 5

  finance:
    strategy: keyword_score
    min_score: 3
    keywords:
      fintech: 5
      payment: 4
      banking: 4
```

### 查看报告

```bash
# 查看最新报告
cat reports/latest.md

# 在浏览器中打开 HTML
open reports/latest.html
```

---

## 📂 项目结构

```
newsloom/
├── config/                     # 配置文件
│   ├── config.yaml            # 主配置
│   ├── sources.yaml           # 数据源配置
│   └── filters.yaml           # 过滤策略配置
├── src/
│   ├── sources/               # 数据源插件
│   │   ├── base.py           # 抽象基类
│   │   ├── rss.py            # RSS 实现
│   │   └── registry.py       # 注册中心
│   ├── processors/            # 处理器
│   │   ├── fetcher.py        # 并行抓取
│   │   ├── filter.py         # 智能过滤
│   │   ├── generator.py      # 报告生成
│   │   └── filters/          # 过滤策略
│   │       ├── base.py       # 策略基类
│   │       ├── keyword_filter.py
│   │       ├── upvote_filter.py
│   │       └── passthrough_filter.py
│   ├── utils/                 # 工具函数
│   └── pipeline.py            # 主流程
├── data/                      # 数据存储
│   ├── raw/                  # Layer 1 输出
│   ├── filtered/             # Layer 2 输出
│   └── state/                # 状态文件
├── reports/                   # 生成的报告
├── docs/                      # 文档
│   └── EXTENDING.md          # 扩展指南
└── run.py                     # 入口脚本
```

---

## 🔧 扩展系统

### 添加新数据源

1. **创建数据源类**（`src/sources/my_source.py`）:

```python
from .base import DataSource, Item

class MySource(DataSource):
    def get_source_name(self) -> str:
        return "my_source"

    def fetch(self, hours_ago=None) -> List[Item]:
        # 实现抓取逻辑
        items = []
        # ...
        return items
```

2. **注册**（`src/sources/registry.py`）:

```python
SOURCE_MAP = {
    'my_source': MySource,
    # ...
}
```

3. **配置**（`config/sources.yaml`）:

```yaml
my_source:
  enabled: true
  channel: "custom"
  type: "my_source"
```

### 添加自定义过滤策略

1. **创建过滤器**（`src/processors/filters/my_filter.py`）:

```python
from .base import FilterStrategy

class MyFilter(FilterStrategy):
    def calculate_score(self, item) -> float:
        # 自定义评分逻辑
        return score
```

2. **注册**（`src/processors/filters/__init__.py`）:

```python
FILTER_REGISTRY = {
    'my_filter': MyFilter,
    # ...
}
```

3. **使用**（`config/filters.yaml`）:

```yaml
channels:
  my_channel:
    strategy: my_filter
    min_score: 5
```

更多详情请查看 [扩展指南](docs/EXTENDING.md)。

---

## 📊 示例输出

### Markdown 报告

```markdown
# Daily Report - 2024-02-12

## AI

### 1. [State-sponsored hackers exploit AI for advanced cyberattacks](...)
**Source:** rss_ai | **Author:** John Doe | **Score:** 139.0

> State-sponsored hackers are exploiting AI to accelerate cyberattacks...
```

### HTML 报告

<img src="docs/images/html-report-light.png" width="400" alt="HTML Light Theme">
<img src="docs/images/html-report-dark.png" width="400" alt="HTML Dark Theme">

---

## ⚙️ 配置选项

### 主配置 (`config/config.yaml`)

```yaml
project:
  name: "Newsloom"
  timezone: "Asia/Shanghai"

pipeline:
  enabled_layers: ["fetch", "filter", "analyze", "generate"]

  fetch:
    parallel_workers: 10    # 并行线程数
    hours_ago: 24          # 抓取24小时内的

  filter:
    max_age_hours: 48      # 只保留48小时内的
    min_score: 3           # 默认最低分

ai:
  claude:
    api_key: ${ANTHROPIC_API_KEY}
    base_url: ${ANTHROPIC_BASE_URL}  # 可选：API代理地址
    model: "claude-sonnet-4-20250514"
    max_tokens: 4096
    temperature: 0.2
```

### 环境变量

在配置中使用环境变量:

```yaml
api_key: ${MY_API_KEY}              # 必需
timeout: ${TIMEOUT:30}              # 带默认值
```

---

## 🛠️ 高级用法

### 自定义 Pipeline

创建自定义脚本:

```python
from sources.registry import SourceRegistry
from processors.fetcher import ParallelFetcher
from processors.filter import SmartFilter

# 初始化
registry = SourceRegistry('config/sources.yaml')
sources = registry.get_enabled_sources()

# 自定义流程
fetcher = ParallelFetcher(sources, state_manager)
items = fetcher.fetch_all(hours_ago=6)  # 只要6小时的

# 自定义过滤
filtered = [item for item in items if item.score > 10]

# 输出
for item in filtered:
    print(f"{item.title}")
```

### 多配置文件

```bash
# 生产环境
python3 run.py --config config/production.yaml

# 测试环境
python3 run.py --config config/testing.yaml
```

### 定时运行

使用 cron:

```bash
# 每天凌晨 2 点运行
0 2 * * * cd /path/to/Newsloom && python3 run.py
```

或使用 GitHub Actions（见 [部署指南](docs/DEPLOYMENT.md)）。

---

## 📈 路线图

- [x] **Phase 1**: 核心框架 + RSS 数据源 ✅
- [x] **Phase 1.5**: 可插拔过滤系统 ✅
- [x] **Phase 2**: 更多数据源 (arXiv, GitHub, HN) ✅
- [x] **Phase 3**: Claude AI 双pass分析 ✅
- [x] **Phase 5**: GitHub Actions 自动化 ✅
- [x] **Phase 6**: 深度优化（Crypto/Finance 频道、专业 HTML 主题、并发优化、健壮性）✅
- [ ] **Phase 4**: PNG 卡片渲染 (可选)

---

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)。

### 贡献方式

- 🐛 报告 Bug
- 💡 提出新功能
- 📝 改进文档
- 🔌 贡献新的数据源或过滤器
- ⭐ Star 本项目

### 开发设置

```bash
# 克隆仓库
git clone https://github.com/zhangjunmengyang/Newsloom.git
cd Newsloom

# 安装开发依赖
pip install -r requirements.txt
pip install pytest black

# 运行测试
pytest tests/

# 代码格式化
black src/
```

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

## 🙏 致谢

本项目受以下项目启发:

- [CloudFlare-AI-Insight-Daily](https://github.com/example/cloudflare-ai) - 无服务器架构
- [morning-brief-pro](https://github.com/example/morning-brief) - RAG 流水线
- [twitter-watchdog](https://github.com/example/twitter-watchdog) - Claude 最佳实践

---

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/zhangjunmengyang/Newsloom/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zhangjunmengyang/Newsloom/discussions)

---

<div align="center">

**[⬆ 回到顶部](#newsloom-)**

Made with ❤️ by Newsloom Contributors

</div>
