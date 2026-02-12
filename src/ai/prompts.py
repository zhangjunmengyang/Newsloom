"""Prompt 模板库 - v0.2.0 增强版"""


# 老板 Profile Context（注入到所有 prompt 中）
OWNER_PROFILE = """你的读者是一位 AI 算法工程师 + Crypto 量化研究者，他关注：
- AI/LLM 前沿：新模型发布、架构创新、推理优化、开源工具、Agent 框架
- Crypto/DeFi：市场动态、协议升级、链上数据、MEV/套利机会
- 量化交易：算法策略、回测框架、市场微观结构、Alpha 信号
- 开发工具：高效开发工具、Rust/Python 生态、GPU 计算、MLOps
- 科技商业：融资动态、产品创新、科技公司战略"""


class PromptTemplates:
    """
    Prompt 模板集合

    支持中英文双语，v0.2.0 增加：
    - 老板 profile context 注入
    - 精排打分 (1-10)
    - importance / category_tags / insight 字段
    - Executive Summary prompt
    """

    @staticmethod
    def filter_prompt(items: list, section: str, language: str = "zh-CN") -> str:
        """
        Pass 1: 过滤+精排 prompt

        Args:
            items: Item 列表
            section: 频道/分类名称
            language: 语言（zh-CN 或 en-US）
        """
        if language == "zh-CN":
            return PromptTemplates._filter_prompt_zh(items, section)
        else:
            return PromptTemplates._filter_prompt_en(items, section)

    @staticmethod
    def _filter_prompt_zh(items: list, section: str) -> str:
        """中文过滤+精排 prompt"""
        items_text = "\n\n".join([
            f"ID: {i}\n标题: {item.title}\n来源: {PromptTemplates._get_display_source(item)} | 作者: {item.author}\n内容: {item.text[:500]}"
            for i, item in enumerate(items)
        ])

        return f"""你是一个专业的内容筛选助手。

{OWNER_PROFILE}

请从以下 {section} 领域的内容中，筛选出**对这位读者真正有价值**的内容。

# 筛选标准
- ✅ 保留：与 AI/LLM/Crypto/量化/开源工具 直接相关的高质量内容
- ✅ 保留：重大新闻、技术突破、深度分析、实用工具
- ✅ 保留：有数据支撑的市场分析、链上洞察
- ❌ 排除：营销软文、低质量内容、纯新闻稿、重复信息
- ❌ 排除：与读者领域无关的一般科技新闻

# 待筛选内容
{items_text}

# 输出格式
请只返回通过筛选的内容的 ID 列表（用逗号分隔的数字），例如：0,3,7,12

如果所有内容都不合格，返回：NONE

ID列表:"""

    @staticmethod
    def _filter_prompt_en(items: list, section: str) -> str:
        """英文过滤+精排 prompt"""
        items_text = "\n\n".join([
            f"ID: {i}\nTitle: {item.title}\nSource: {PromptTemplates._get_display_source(item)} | Author: {item.author}\nContent: {item.text[:500]}"
            for i, item in enumerate(items)
        ])

        return f"""You are a professional content curator.

{OWNER_PROFILE}

Please filter high-quality, valuable content from the following {section} items, focusing on what matters to this reader.

# Filtering Criteria
- ✅ Keep: Directly relevant to AI/LLM/Crypto/Quantitative/Open-source tools
- ✅ Keep: Major news, technical breakthroughs, deep analysis, useful tools
- ❌ Exclude: Marketing, low-quality, duplicates, press releases
- ❌ Exclude: General tech news unrelated to the reader's focus areas

# Content to Filter
{items_text}

# Output Format
Return only the IDs of selected items (comma-separated numbers), e.g.: 0,3,7,12

If nothing passes, return: NONE

IDs:"""

    @staticmethod
    def extract_prompt(items: list, section: str, language: str = "zh-CN") -> str:
        """
        Pass 2: 结构化提取 prompt（增强版）

        Args:
            items: 筛选后的 Item 列表
            section: 频道/分类名称
            language: 语言
        """
        if language == "zh-CN":
            return PromptTemplates._extract_prompt_zh(items, section)
        else:
            return PromptTemplates._extract_prompt_en(items, section)

    @staticmethod
    def _get_display_source(item) -> str:
        """获取人类可读的来源名（优先 metadata 中的 feed_title/feed_name）"""
        meta = getattr(item, 'metadata', {}) or {}
        return meta.get('feed_name') or meta.get('feed_title') or getattr(item, 'source', 'unknown')

    @staticmethod
    def _extract_prompt_zh(items: list, section: str) -> str:
        """中文提取 prompt（v0.2.0 增强版）"""
        items_text = "\n\n".join([
            f"【{i+1}】\n标题: {item.title}\n来源: {PromptTemplates._get_display_source(item)} | 作者: {item.author}\n链接: {item.url}\n内容: {item.text[:800]}"
            for i, item in enumerate(items)
        ])

        return f"""你是一个专业的技术编辑，服务于一位 AI 算法工程师 + Crypto 量化研究者。

{OWNER_PROFILE}

请将以下 {section} 领域的内容提炼成结构化的日报条目。

# 内容
{items_text}

# 输出要求
请为每条内容生成：
1. **headline**（一句话标题，20字内，突出核心价值）
2. **detail**（3-4句话详细说明，要有 "so what" 的分析视角——不只是复述事实，要说明这对读者意味着什么、有什么影响或机会）
3. **importance**（1-5 重要性评级：1=一般了解，2=值得关注，3=重要，4=非常重要，5=必读/突破性）
4. **category_tags**（1-3 个分类标签，如 "LLM", "DeFi", "开源工具", "量化策略", "融资", "GPU", "Agent" 等）
5. **insight**（一句话洞察：为什么这条对读者有价值，用"→"开头，如 "→ 可用于优化现有量化回测框架"）

**注意**：
- 如果内容字段只包含简单元数据（如 "Score: X | Comments: Y"），请基于标题提炼出有价值的信息
- 对于社区热门内容，可以将热度信息融入 detail 中
- importance 评分要有区分度，不要全给 3 分
- category_tags 要具体，不要用太泛的标签
- 每条内容都必须生成完整的字段，不要跳过任何条目

# 输出格式（JSON）
```json
[
  {{
    "headline": "简洁有力的标题",
    "detail": "详细分析，包含关键技术点、数据、影响。这意味着...对于量化/AI 从业者来说...",
    "url": "原文链接",
    "source": "来源",
    "importance": 4,
    "category_tags": ["LLM", "开源工具"],
    "insight": "→ 一句话洞察，说明为什么对读者有价值"
  }}
]
```

只返回 JSON，不要其他内容。

JSON:"""

    @staticmethod
    def _extract_prompt_en(items: list, section: str) -> str:
        """英文提取 prompt（v0.2.0 增强版）"""
        items_text = "\n\n".join([
            f"【{i+1}】\nTitle: {item.title}\nSource: {PromptTemplates._get_display_source(item)} | Author: {item.author}\nURL: {item.url}\nContent: {item.text[:800]}"
            for i, item in enumerate(items)
        ])

        return f"""You are a professional tech editor serving an AI engineer + Crypto quant researcher.

{OWNER_PROFILE}

Please distill the following {section} content into structured daily brief entries.

# Content
{items_text}

# Requirements
For each item, generate:
1. **headline** (one-sentence title, under 20 words, highlighting core value)
2. **detail** (3-4 sentences with "so what" analysis — don't just restate facts, explain implications and opportunities for the reader)
3. **importance** (1-5 rating: 1=nice to know, 2=worth noting, 3=important, 4=very important, 5=must-read/breakthrough)
4. **category_tags** (1-3 specific tags like "LLM", "DeFi", "Open Source", "Quant Strategy", "GPU", "Agent")
5. **insight** (one-sentence insight starting with "→", e.g., "→ Could optimize existing quant backtesting framework")

**Important**:
- If content field only contains simple metadata (like "Score: X | Comments: Y"), extract value from the title instead
- importance scoring should be differentiated, not all 3s
- category_tags should be specific, not overly broad
- You MUST generate complete fields for EVERY item - do not skip any entries

# Output Format (JSON)
```json
[
  {{
    "headline": "Concise, impactful title",
    "detail": "Detailed analysis with key points, data, and impact. This means... For AI/quant practitioners...",
    "url": "original URL",
    "source": "source name",
    "importance": 4,
    "category_tags": ["LLM", "Open Source"],
    "insight": "→ One-sentence insight on value to the reader"
  }}
]
```

Return ONLY JSON, nothing else.

JSON:"""

    @staticmethod
    def executive_summary_prompt(briefs: dict, section_configs: dict, language: str = "zh-CN") -> str:
        """
        Executive Summary prompt - 基于所有 section 的 top 内容生成今日要闻概述

        Args:
            briefs: {section: [brief_dicts]} 所有已分析的 briefs
            section_configs: section 配置（包含 emoji, title 等）
            language: 语言
        """
        if language == "zh-CN":
            return PromptTemplates._executive_summary_zh(briefs, section_configs)
        else:
            return PromptTemplates._executive_summary_en(briefs, section_configs)

    @staticmethod
    def _executive_summary_zh(briefs: dict, section_configs: dict) -> str:
        """中文 Executive Summary prompt"""
        # 收集每个 section 的 top 3 内容
        top_items_text = ""
        for section, items in briefs.items():
            if not items:
                continue
            meta = section_configs.get(section, {})
            emoji = meta.get('emoji', '•')
            title = meta.get('title', section)
            top_items_text += f"\n### {emoji} {title}\n"
            for item in items[:3]:
                headline = item.get('headline', '')
                detail = item.get('detail', '')
                importance = item.get('importance', 3)
                top_items_text += f"- [重要性:{importance}] {headline}: {detail[:100]}\n"

        return f"""你是一位资深技术编辑，每天为一位 AI 算法工程师 + Crypto 量化研究者撰写早间简报。

{OWNER_PROFILE}

以下是今日各板块的精选内容摘要：

{top_items_text}

请按以下结构生成 Executive Summary：

**格式要求（严格按此结构输出）：**

1. 第一行：**今日关键词**（3-5 个 tag，用 `#` 前缀，空格分隔）
   例如：`#Claude4发布 #ETH突破4000 #Cursor融资 #Rust2.0 #链上AI`

2. 空一行后，**三大主线**（每条一行，emoji 前缀 + 一句话概括，不超过 30 字）
   例如：
   🔬 OpenAI 发布 o3-mini，推理能力大幅提升，开源社区迅速跟进
   💰 Crypto 市场回暖，ETH DeFi TVL 创新高，MEV 套利机会增多
   🛠️ Cursor 完成 B 轮融资，AI 编码工具进入军备竞赛阶段

3. 空一行后，**🎯 重点关注**（1-2 条对老板最有价值的，每条 1-2 句话，说明为什么值得关注和可能的行动点）

**注意**：
- 关键词要具体，不要太泛（"AI进展" ❌ → "GPT-5泄露" ✅）
- 三大主线要覆盖不同领域，不要都是 AI
- 重点关注要有 actionable insight

直接输出内容，不要加 "Executive Summary" 标题。

输出:"""

    @staticmethod
    def _executive_summary_en(briefs: dict, section_configs: dict) -> str:
        """英文 Executive Summary prompt"""
        top_items_text = ""
        for section, items in briefs.items():
            if not items:
                continue
            meta = section_configs.get(section, {})
            title = meta.get('title', section)
            top_items_text += f"\n### {title}\n"
            for item in items[:3]:
                headline = item.get('headline', '')
                importance = item.get('importance', 3)
                top_items_text += f"- [importance:{importance}] {headline}\n"

        return f"""You are a senior tech editor.

{OWNER_PROFILE}

Here are today's top items across all sections:

{top_items_text}

Please generate a ~200 word Executive Summary that:
1. Highlights the 3-5 most important developments today
2. Focuses on what matters most to an AI engineer + quant researcher
3. Notes any cross-domain connections (e.g., AI+Crypto)
4. Professional but engaging tone, like a morning briefing to a colleague

Return only the summary text, no titles or formatting marks.

Summary:"""
