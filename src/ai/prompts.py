"""Prompt 模板库"""


class PromptTemplates:
    """
    Prompt 模板集合

    支持中英文双语
    """

    @staticmethod
    def filter_prompt(items: list, section: str, language: str = "zh-CN") -> str:
        """
        Pass 1: 过滤 prompt

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
        """中文过滤 prompt"""
        items_text = "\n\n".join([
            f"ID: {i}\n标题: {item.title}\n来源: {item.source} | 作者: {item.author}\n内容: {item.text[:500]}"
            for i, item in enumerate(items)
        ])

        return f"""你是一个专业的内容筛选助手。请从以下 {section} 领域的内容中，筛选出**真正有价值、高质量**的内容。

# 筛选标准
- ✅ 保留：技术深度高、信息量大、有启发性、来自权威来源
- ✅ 保留：重大新闻、突破性进展、深度分析
- ❌ 排除：营销软文、低质量内容、重复信息、纯新闻稿

# 待筛选内容
{items_text}

# 输出格式
请只返回通过筛选的内容的 ID 列表（用逗号分隔的数字），例如：0,3,7,12

如果所有内容都不合格，返回：NONE

ID列表:"""

    @staticmethod
    def _filter_prompt_en(items: list, section: str) -> str:
        """英文过滤 prompt"""
        items_text = "\n\n".join([
            f"ID: {i}\nTitle: {item.title}\nSource: {item.source} | Author: {item.author}\nContent: {item.text[:500]}"
            for i, item in enumerate(items)
        ])

        return f"""You are a professional content curator. Please filter high-quality, valuable content from the following {section} items.

# Filtering Criteria
- ✅ Keep: Deep technical content, high information density, insightful, authoritative sources
- ✅ Keep: Major news, breakthroughs, in-depth analysis
- ❌ Exclude: Marketing, low-quality, duplicates, press releases

# Content to Filter
{items_text}

# Output Format
Return only the IDs of selected items (comma-separated numbers), e.g.: 0,3,7,12

If nothing passes, return: NONE

IDs:"""

    @staticmethod
    def extract_prompt(items: list, section: str, language: str = "zh-CN") -> str:
        """
        Pass 2: 提取 prompt

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
    def _extract_prompt_zh(items: list, section: str) -> str:
        """中文提取 prompt"""
        items_text = "\n\n".join([
            f"【{i+1}】\n标题: {item.title}\n来源: {item.source} | 作者: {item.author}\n链接: {item.url}\n内容: {item.text[:800]}"
            for i, item in enumerate(items)
        ])

        return f"""你是一个专业的技术编辑。请将以下 {section} 领域的内容提炼成简洁的日报条目。

# 内容
{items_text}

# 输出要求
请为每条内容生成：
1. **headline**（一句话标题，20字内，突出核心价值）
2. **detail**（2-3句话详细说明，包含关键信息和要点）

# 输出格式（JSON）
```json
[
  {{
    "headline": "简洁有力的标题",
    "detail": "详细说明，包含关键技术点、数据、影响等。",
    "url": "原文链接",
    "source": "来源"
  }}
]
```

只返回 JSON，不要其他内容。

JSON:"""

    @staticmethod
    def _extract_prompt_en(items: list, section: str) -> str:
        """英文提取 prompt"""
        items_text = "\n\n".join([
            f"【{i+1}】\nTitle: {item.title}\nSource: {item.source} | Author: {item.author}\nURL: {item.url}\nContent: {item.text[:800]}"
            for i, item in enumerate(items)
        ])

        return f"""You are a professional tech editor. Please distill the following {section} content into concise daily brief entries.

# Content
{items_text}

# Requirements
For each item, generate:
1. **headline** (one-sentence title, under 20 words, highlighting core value)
2. **detail** (2-3 sentences with key information and insights)

# Output Format (JSON)
```json
[
  {{
    "headline": "Concise, impactful title",
    "detail": "Detailed explanation with key technical points, data, and impact.",
    "url": "original URL",
    "source": "source name"
  }}
]
```

Return ONLY JSON, nothing else.

JSON:"""
