# Newsloom v2.0 升级计划

## 改造目标
为老板（AI算法工程师 + B圈量化研究者）打造真正有用的每日情报系统

## 阶段一：信息源扩展 ✅ → 进行中
1. **Web Search 数据源** — 用 Brave Search API 抓取实时热点
2. **Reddit 数据源** — JSON endpoint 抓取（绕过 403）
3. **Product Hunt 数据源** — 新产品/工具发现
4. **Crypto 市场数据源** — CoinGecko API 实时行情 + Fear & Greed

## 阶段二：处理流程重构（推荐系统思想）
1. **候选池扩大** — 所有源 fetch 后合并为统一候选池
2. **粗排（Coarse Ranking）** — 规则 + 关键词 + 时效性 + 来源权威度快速打分，取 Top N
3. **精排（Fine Ranking）** — Claude AI 评估：相关性 × 信息密度 × 时效性 × 影响力
4. **去重 & 聚合** — 同一事件多源报道合并为一条（cluster dedup）
5. **个性化加权** — 根据老板的兴趣 profile 调整权重

## 阶段三：AI 分析升级
1. **System Prompt 重构** — 让 Claude 理解老板的身份和兴趣
2. **结构化评分** — 每条新闻输出 relevance/impact/urgency 分数
3. **洞察生成** — 不只是摘要，要有"所以呢？对你意味着什么？"
4. **趋势检测** — 跨条目关联，发现隐含趋势

## 阶段四：输出优化
1. **Executive Summary 升级** — 30秒读完今日核心
2. **分级阅读** — 🔴 必读 / 🟡 推荐 / 🟢 了解即可
3. **新 HTML 模板** — 更现代、更好看、支持折叠展开
4. **Discord 推送格式** — 适配 Discord embed 的精简版

## 阶段五：自动化
1. Cron 每天 09:00 GMT+8 自动运行 pipeline
2. 结果通过 Discord DM 推送给老板
