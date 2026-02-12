# Changelog

All notable changes to Newsloom will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (Phase 6 - Deep Optimization - 2026-02-12)

#### P0: 核心功能完善
- **Crypto/Finance 数据源**: 新增 8 个高质量 RSS feeds
  - Crypto 频道: CoinDesk, Cointelegraph, CryptoSlate, Decrypt
  - Finance 频道: Bloomberg Tech, Reuters Tech, TechCrunch Fintech, WSJ Tech
- **过滤规则扩展**: 为 crypto 和 finance 频道添加完整的关键词评分策略
  - Crypto: bitcoin, ethereum, blockchain, defi, smart contract 等 25+ 关键词
  - Finance: fintech, payment, banking, venture capital, regulation 等 20+ 关键词
  - 黑名单：scam, airdrop, ponzi 等垃圾内容过滤
- **专业 HTML 报告主题**:
  - 侧边栏导航（固定、可滚动、section 跳转）
  - Section 颜色区分（AI 紫色、Tech 蓝色、Crypto 橙色、Finance 绿色等）
  - 优化的暗色主题（默认）+ 亮色主题切换
  - 响应式布局，移动端友好
  - 平滑滚动 + active section 高亮
  - 渐变背景 + 悬停动画

#### P1: 健壮性改进
- **Generator 空 section 处理**: 自动跳过空的 section，避免报错
  - 如果所有 section 为空，生成 "No Content" 报告而不是崩溃
- **HackerNews 并发优化**: 使用 ThreadPoolExecutor 并发获取 story detail
  - 默认 10 个并发 worker，可配置
  - 性能提升约 5-10 倍
- **State 自动清理**: 在 save() 时自动清理超过 dedup_window_days 的旧记录
  - 新增 `item_timestamps` 追踪每个 item 的首次见到时间
  - 减少 state 文件膨胀

#### P2: 文档完善
- **README.md 更新**:
  - 反映当前实际配置（API 代理、新数据源、环境变量）
  - 更新特性列表（并发优化、多频道支持）
  - 更新路线图（Phase 6 完成）
- **CHANGELOG.md**: 记录所有变更历史
- **config.example.yaml**: 提供示例配置（不含敏感信息）

### Changed
- HTML 报告默认主题改为暗色
- HackerNews 抓取逻辑从串行改为并发

### Fixed
- Generator 在 section 为空时不再报错
- State 文件不再无限增长

---

## [0.5.0] - Phase 5 - 2026-02-11

### Added
- GitHub Actions 自动化部署
- 完整文档（EXTENDING.md, DEPLOYMENT.md, PROJECT_SUMMARY.md）

## [0.4.0] - Phase 3 - 2026-02-10

### Added
- Claude AI 双 pass 分析（Extract + Summarize）
- AI briefs 生成（headline + detail）
- Analyzer 处理器

## [0.3.0] - Phase 2 - 2026-02-09

### Added
- arXiv 数据源（论文搜索）
- GitHub Trending 数据源
- HackerNews 数据源
- 多数据源支持

## [0.2.0] - Phase 1.5 - 2026-02-08

### Added
- 可插拔过滤系统（FilterStrategy）
- KeywordFilter（关键词评分）
- UpvoteFilter（投票加权）
- PassThroughFilter（直通）
- Filter 注册机制

## [0.1.0] - Phase 1 - 2026-02-07

### Added
- 核心 Pipeline 架构（Fetch → Filter → Analyze → Generate）
- RSS 数据源支持
- ParallelFetcher（并行抓取）
- StateManager（去重管理）
- Markdown 和 HTML 报告生成
- 基础配置系统（YAML + 环境变量）

---

## Legend

- **Added**: 新功能
- **Changed**: 现有功能的更改
- **Deprecated**: 即将移除的功能
- **Removed**: 已移除的功能
- **Fixed**: Bug 修复
- **Security**: 安全相关修复
