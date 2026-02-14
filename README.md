# 🗞️ Newsloom
> AI-Powered Daily Intelligence Platform

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![License](https://img.shields.io/badge/license-MIT-green)

Newsloom 是一个 AI 驱动的每日情报平台，自动聚合、分析、生成多源新闻摘要，支持 Web Dashboard、CLI 工具和 RSS 订阅。

## ✨ Features

- 🤖 AI 双 Pass 分析（Claude 驱动）
- 📡 15+ 数据源（RSS、arXiv、GitHub Trending、HN、Product Hunt）
- 🎯 智能重要性评分 + "So What" 洞察
- 🔄 同源去重 + 跨天趋势检测
- 📊 趋势雷达（关键词热度追踪）
- 🖥️ Next.js Dashboard（暗色主题）
- 📄 多格式输出（Markdown / HTML / PDF）
- 📡 RSS Feed 输出
- 📅 周报/月报自动聚合
- 🔧 CLI 工具（`news` 命令）
- 🎯 个人关注板块（量化/Crypto/Agent 定制）
- ⚡ FastAPI 后端 + WebSocket 实时状态

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/zhangjunmengyang/Newsloom.git
cd Newsloom

# Install
pip install -r requirements.txt

# Configure
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your API keys

# Run pipeline
python3 news run

# Start Dashboard
python3 news serve --frontend

# Generate weekly report
python3 news weekly

# Generate RSS feed
python3 news feed
```

## 🏗️ Architecture

```
Data Sources → Fetch → Filter → Analyze (AI) → Dedup → Trend → Generate → Deliver
     │                                                              │
     │         ┌──────────────┐                    ┌────────────────┤
     └─── RSS  │  FastAPI     │◄───── API ────────►│  Next.js       │
          arXiv │  Server     │                    │  Dashboard     │
          HN    │  WebSocket  │                    │  (shadcn/ui)   │
          GitHub└──────────────┘                    └────────────────┘
```

## 📋 CLI Commands

| Command | Description |
|---------|-------------|
| `news run` | Run the pipeline |
| `news status` | Show system status |
| `news serve` | Start Dashboard server |
| `news history` | List historical reports |
| `news sources` | List data sources |
| `news weekly` | Generate weekly report |
| `news monthly` | Generate monthly report |
| `news feed` | Generate RSS feed |

## 📁 Project Structure

```
Newsloom/
├── config/                     # Configuration files
│   ├── config.yaml
│   ├── sources.yaml
│   └── filters.yaml
├── src/
│   ├── sources/               # Data source plugins
│   ├── processors/            # Processing layers
│   ├── generators/            # Report generators
│   ├── api/                   # FastAPI backend
│   ├── web/                   # Next.js frontend
│   └── cli/                   # CLI interface
├── data/
│   ├── raw/                   # Raw fetched data
│   ├── processed/             # Filtered data
│   └── reports/               # Generated reports
├── frontend/
│   ├── components/            # React components
│   ├── pages/                 # Next.js pages
│   └── styles/                # Tailwind CSS
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── docs/                      # Documentation
├── scripts/                   # Deployment scripts
├── requirements.txt           # Python dependencies
├── package.json              # Node.js dependencies
└── README.md
```

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLite
- **Frontend**: Next.js 16, shadcn/ui, Tailwind CSS
- **AI**: Claude API, Anthropic SDK
- **Visualization**: Plotly, Chart.js
- **Data**: Pandas, BeautifulSoup, Feedparser
- **Real-time**: WebSocket, Server-Sent Events

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone and install
git clone https://github.com/zhangjunmengyang/Newsloom.git
cd Newsloom
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install

# Run tests
pytest tests/
npm test
```

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=zhangjunmengyang/Newsloom&type=Date)](https://star-history.com/#zhangjunmengyang/Newsloom&Date)

---

<div align="center">

**Made with ❤️ by the Newsloom Community**

[Website](https://newsloom.ai) • [Documentation](https://docs.newsloom.ai) • [Discord](https://discord.gg/newsloom)

</div>