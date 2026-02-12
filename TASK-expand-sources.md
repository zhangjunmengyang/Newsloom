# 任务：系统性扩展 Newsloom 信息源

## 背景
Newsloom 是一个多源智能日报系统。当前信息源太少，需要大幅扩展，确保覆盖 AI/Tech/Crypto/Finance 各个重要领域。

## 当前信息源清单
### RSS (config/sources.yaml)
- **rss_tech (3)**: TechCrunch, The Verge, HN RSS
- **rss_ai (6)**: AI News, Google AI Blog, VentureBeat AI, MIT Tech Review, The Decoder, Slashdot
- **rss_crypto (4)**: CoinDesk, Cointelegraph, CryptoSlate, Decrypt
- **rss_finance (5)**: Yahoo Finance, Reuters Business, CNBC, Fortune, TechCrunch Fintech
### 非 RSS
- **arxiv**: cs.AI, cs.CL, cs.LG
- **github**: Python daily trending
- **hackernews**: min_score 100

## 需要扩展的方向

### P0: 官方博客/公告（最重要！这些是第一手信息）
必须加入这些 AI 公司官方博客的 RSS/Atom feed：
- **Anthropic** (anthropic.com/blog 或 research) — 我们的"老家"
- **OpenAI** (openai.com/blog)
- **Google DeepMind** (deepmind.google/blog)
- **Meta AI / FAIR** (ai.meta.com/blog)
- **Microsoft Research** (microsoft.com/en-us/research/blog)
- **Cursor** (cursor.com/blog) — 老板常用的 AI 编码工具
- **Vercel** (vercel.com/blog) — 前端/全栈重要动态
- **Hugging Face** (huggingface.co/blog)
- **Stability AI** (stability.ai/news)
- **Mistral AI** (mistral.ai/news)
- **Cohere** (cohere.com/blog)
- **xAI** (如果有 RSS)
- **NVIDIA AI** (blogs.nvidia.com)

### P1: 高质量科技媒体补充
- **Ars Technica** (arstechnica.com)
- **Wired** (wired.com)
- **The Information** (如果有免费 RSS)
- **Hacker News 精选** (lobste.rs 也是好源)
- **Dev.to** (AI/ML tag)
- **InfoQ** (中英文都有)
- **36kr** (中文科技媒体)
- **机器之心 (jiqizhixin.com)** — 中文 AI 顶级媒体
- **量子位 (qbitai.com)** — 中文 AI 媒体

### P2: Crypto/DeFi 补充
- **The Block** (theblock.co)
- **Messari** (messari.io/newsletter)
- **Delphi Digital** (如果有 RSS)
- **Bankless** (bankless.com)
- **DeFi Llama** 的 news feed
- **Rekt News** (rekt.news)

### P3: Finance/Macro
- **Bloomberg** (如果有免费 RSS)
- **FT** (如果有免费 RSS)
- **Wall Street Journal** (如果有免费 RSS)
- **Seeking Alpha** (seekingalpha.com)
- **ZeroHedge** (zerohedge.com)

### P4: GitHub Trending 扩展
- 当前只跟踪 python daily
- 加入: 全语言(overall), TypeScript, Rust
- 考虑 weekly trending 也拉一份

## 实施要求

1. **验证每个 feed URL 能正常获取**。用 `curl -sL <url> | head -20` 测试，确认返回 XML/Atom/RSS。不能用的就跳过，备注原因。

2. **归类到正确的 channel**：
   - 官方 AI 公司博客 → `ai` channel
   - 中文 AI 媒体 → 新建 `ai_cn` channel（或合并到 `ai`）
   - 通用科技 → `tech` channel
   - Crypto → `crypto` channel
   - Finance/Macro → `finance` channel

3. **更新 config/sources.yaml** — 新增 feeds 到对应源，或新建源

4. **更新 config/filters.yaml** — 如果新建了 channel，加对应过滤策略

5. **GitHub trending 扩展** — 修改 sources.yaml 的 github 配置，或在 `src/sources/` 里看代码是否支持多语言/多 period

6. **测试** — 改完后跑 `cd src && python3 pipeline.py --layers fetch` 验证 fetch 阶段正常

7. **提交并推送** — `git add -A && git commit -m "feat: 大规模扩展信息源" && git push`

8. **完成后运行**: `openclaw system event --text "Done: 信息源大规模扩展完成 - [简要统计]" --mode now`

## 注意事项
- RSS feed URL 要准确，很多网站的 feed 路径不标准，需要实测
- 有些网站可能 403/需要 User-Agent，记录下来
- max_per_feed 官方博客设 10-15（更新不频繁），大媒体设 20-30
- 不要删除现有可用的源，只新增
- 中文源如果拿不到 RSS，先跳过备注
