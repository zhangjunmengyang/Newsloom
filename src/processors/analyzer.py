"""Layer 3: AI 分析器 - Claude 双pass处理 + Executive Summary"""

import json
from typing import List, Dict
from pathlib import Path
from collections import defaultdict

from sources.base import Item
from ai.claude import ClaudeClient
from ai.prompts import PromptTemplates


class AIAnalyzer:
    """
    AI 分析器 - Claude 双pass处理 (v0.2.0 增强版)

    整合 morning-brief 和 twitter-watchdog 的最佳实践:
    - Pass 1: 智能过滤（识别高质量内容）
    - Pass 2: 结构化提取（生成 headline + detail + importance + tags + insight）
    - Executive Summary: AI 生成今日要闻概述
    - Token-aware 批处理
    """

    def __init__(self, claude_client: ClaudeClient, language: str = "zh-CN", config: dict = None):
        """
        初始化分析器

        Args:
            claude_client: Claude 客户端实例
            language: 语言（zh-CN 或 en-US）
            config: 可选配置 (max_items_per_section 等)
        """
        self.claude = claude_client
        self.language = language
        self.config = config or {}

    def analyze(self, items: List[Item], two_pass: bool = True,
                section_configs: dict = None) -> Dict[str, List[Dict]]:
        """
        分析 items 并生成结构化输出

        Args:
            items: 要分析的 Item 列表
            two_pass: 是否使用双pass处理
            section_configs: section 配置（用于生成 Executive Summary）

        Returns:
            Dict[section, List[brief]]: 按 section 分组的 briefs
            特殊 key "__executive_summary__" 存放 AI 生成的概述
        """
        print(f"\n🧠 AI 分析中...")
        print(f"   模型: {self.claude.model}")
        print(f"   双pass: {two_pass}")

        # 按 section 分组
        by_section = self._group_by_section(items)

        results = {}

        for section, section_items in by_section.items():
            print(f"\n  📁 分析 section '{section}': {len(section_items)} 条")

            # 限流：按 score 降序取 top N（默认 30，可通过 config 配置）
            max_per_section = self.config.get('max_items_per_section', 30)
            if len(section_items) > max_per_section:
                section_items = sorted(section_items, key=lambda x: x.score, reverse=True)[:max_per_section]
                print(f"     📊 限流: 取 top {max_per_section} 条（按 score 排序）")

            if two_pass:
                # Pass 1: 过滤
                filtered_items = self._pass1_filter(section_items, section)
                print(f"     ✓ Pass 1 过滤: {len(filtered_items)}/{len(section_items)}")

                # Pass 2: 提取
                if filtered_items:
                    briefs = self._pass2_extract(filtered_items, section)
                    results[section] = briefs
                    print(f"     ✓ Pass 2 提取: {len(briefs)} 条 briefs")
            else:
                # 单pass：直接提取
                briefs = self._pass2_extract(section_items, section)
                results[section] = briefs
                print(f"     ✓ 提取: {len(briefs)} 条 briefs")

        # 按 importance 排序每个 section
        for section in results:
            results[section] = sorted(
                results[section],
                key=lambda x: x.get('importance', 3),
                reverse=True
            )

        # 生成"个人关注"板块 — 从其他 section 高分内容中二次筛选
        if section_configs and 'personal' in section_configs:
            try:
                personal_briefs = self._build_personal_section(results)
                if personal_briefs:
                    results['personal'] = personal_briefs
                    print(f"\n  🎯 个人关注: {len(personal_briefs)} 条")
            except Exception as e:
                print(f"\n  ⚠️  个人关注生成失败: {e}")

        # 生成 Executive Summary
        if section_configs and self.claude:
            try:
                executive_summary = self._generate_executive_summary(results, section_configs)
                if executive_summary:
                    results['__executive_summary__'] = executive_summary
                    print(f"\n  📝 Executive Summary 已生成 ({len(executive_summary)} 字)")
            except Exception as e:
                print(f"\n  ⚠️  Executive Summary 生成失败: {e}")

        total_briefs = sum(len(b) for k, b in results.items() if k != '__executive_summary__')
        print(f"\n✅ AI 分析完成: {total_briefs} 条 briefs")
        return results

    def _group_by_section(self, items: List[Item]) -> Dict[str, List[Item]]:
        """按 section/channel 分组"""
        by_section = defaultdict(list)

        for item in items:
            section = item.channel
            by_section[section].append(item)

        return dict(by_section)

    def _pass1_filter(self, items: List[Item], section: str) -> List[Item]:
        """
        Pass 1: AI 过滤

        使用 Claude 识别高质量内容
        """
        # Token-aware 分批
        batches = self.claude.batch_items_by_tokens(items, max_tokens=80000)

        filtered_items = []

        for batch_idx, batch in enumerate(batches):
            if len(batches) > 1:
                print(f"     📦 批次 {batch_idx + 1}/{len(batches)}: {len(batch)} 条")

            # 生成 prompt
            prompt = PromptTemplates.filter_prompt(batch, section, self.language)

            # 调用 Claude
            try:
                response = self.claude.call(
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.2
                )

                # 解析 IDs
                selected_ids = self._parse_ids(response)

                # 提取对应的 items
                for item_id in selected_ids:
                    if 0 <= item_id < len(batch):
                        filtered_items.append(batch[item_id])

            except Exception as e:
                print(f"     ⚠️  Pass 1 失败: {e}")
                # 失败时保留所有items
                filtered_items.extend(batch)

        return filtered_items

    def _pass2_extract(self, items: List[Item], section: str) -> List[Dict]:
        """
        Pass 2: 结构化提取（v0.2.0 增强版）

        使用 Claude 生成 headline + detail + importance + category_tags + insight
        papers section 使用专用 prompt，额外提取 authors/arxiv_id/research_tags/practicality_score
        """
        is_papers = section == 'papers'

        # 如果内容太多，分批处理
        batches = self.claude.batch_items_by_tokens(items, max_tokens=80000)

        all_briefs = []

        for batch_idx, batch in enumerate(batches):
            if len(batches) > 1:
                print(f"     📦 批次 {batch_idx + 1}/{len(batches)}: {len(batch)} 条")

            # 生成 prompt — papers section 使用专用 prompt
            if is_papers:
                prompt = PromptTemplates.extract_prompt_papers(batch, section, self.language)
            else:
                prompt = PromptTemplates.extract_prompt(batch, section, self.language)

            # 调用 Claude（JSON 输出）
            try:
                briefs = self.claude.call_with_json(
                    prompt=prompt,
                    max_tokens=8192,
                    temperature=0.3
                )

                # 验证格式
                brief_list = []
                if isinstance(briefs, list):
                    brief_list = briefs
                elif isinstance(briefs, dict) and 'items' in briefs:
                    brief_list = briefs['items']

                for brief in brief_list:
                    # 通用字段默认值
                    brief.setdefault('importance', 3)
                    brief.setdefault('category_tags', [])
                    brief.setdefault('insight', '')
                    # papers 专用字段默认值
                    if is_papers:
                        brief.setdefault('authors', '')
                        brief.setdefault('arxiv_id', '')
                        brief.setdefault('research_tags', [])
                        brief.setdefault('practicality_score', 3)

                all_briefs.extend(brief_list)

            except Exception as e:
                print(f"     ⚠️  Pass 2 失败: {e}")
                # 失败时使用简单格式，papers 额外从 metadata 回填字段
                for item in batch:
                    meta = getattr(item, 'metadata', {}) or {}
                    display_source = meta.get('feed_name') or meta.get('feed_title') or item.source
                    fallback = {
                        'headline': item.title,
                        'detail': item.text[:200],
                        'url': item.url,
                        'source': display_source,
                        'importance': 3,
                        'category_tags': [],
                        'insight': ''
                    }
                    if is_papers:
                        # 从 Item metadata 回填论文专用字段
                        authors = meta.get('authors', [])
                        author_str = ', '.join(authors[:3])
                        if len(authors) > 3:
                            author_str += ' et al.'
                        fallback['authors'] = author_str
                        fallback['arxiv_id'] = meta.get('arxiv_id', '')
                        fallback['research_tags'] = meta.get('categories', [])[:4]
                        fallback['practicality_score'] = 3
                    all_briefs.append(fallback)

        return all_briefs

    # ============================================================
    # 个人关注板块 — 从全局高分内容中二次筛选
    # ============================================================

    # 关键词集合：匹配到任意一个即入选候选
    PERSONAL_KEYWORDS = [
        # 量化交易
        "quant", "quantitative", "algorithmic trading", "algo trading",
        "backtesting", "backtest", "alpha", "market making", "arbitrage",
        "trading strategy", "order book", "高频", "量化", "套利", "回测",
        "策略", "algotrading",
        # Crypto DeFi
        "defi", "dex", "amm", "liquidity pool", "yield", "staking",
        "mev", "flashbots", "uniswap", "aave", "compound", "lido",
        "restaking", "eigenlayer", "pendle", "ethena",
        "layer 2", "rollup", "zk-proof", "zk-snark",
        "on-chain", "链上", "去中心化金融",
        # AI Agent / 工具链
        "ai agent", "agent framework", "langchain", "langgraph",
        "autogpt", "crewai", "tool use", "function calling",
        "mcp", "model context protocol",
        "cursor", "copilot", "aider", "coding assistant",
        "openai api", "claude api", "anthropic api",
    ]

    def _build_personal_section(self, results: Dict[str, List[Dict]]) -> List[Dict]:
        """
        从所有 section 的高分 briefs 中筛选出与老板个人兴趣最相关的内容。

        筛选逻辑：
        1. 收集所有 section 中 importance >= 3 的 briefs
        2. 关键词匹配（headline + detail + tags 中命中个人兴趣关键词）
        3. 按 importance 降序，取 top 8
        """
        import re

        candidates = []

        for section, briefs in results.items():
            if section.startswith('__') or not isinstance(briefs, list):
                continue
            for brief in briefs:
                importance = brief.get('importance', 3)
                if importance < 3:
                    continue

                # 拼接检索文本
                search_text = " ".join([
                    brief.get('headline', ''),
                    brief.get('detail', ''),
                    " ".join(brief.get('category_tags', [])),
                    brief.get('insight', ''),
                ]).lower()

                # 关键词匹配
                match_count = 0
                for kw in self.PERSONAL_KEYWORDS:
                    if kw.lower() in search_text:
                        match_count += 1

                if match_count > 0:
                    candidates.append({
                        **brief,
                        '_match_count': match_count,
                        '_source_section': section,
                    })

        # 按匹配数 × importance 排序
        candidates.sort(
            key=lambda x: x['_match_count'] * x.get('importance', 3),
            reverse=True
        )

        # 取 top 8，去掉内部字段
        personal = []
        seen_urls = set()
        for c in candidates:
            url = c.get('url', '')
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # 去除内部字段
            item = {k: v for k, v in c.items() if not k.startswith('_')}
            personal.append(item)
            if len(personal) >= 8:
                break

        return personal

    def _generate_executive_summary(self, briefs: Dict[str, List[Dict]],
                                     section_configs: dict) -> str:
        """
        生成 AI Executive Summary

        Args:
            briefs: 所有已分析的 briefs
            section_configs: section 配置

        Returns:
            str: AI 生成的概述文字
        """
        # 过滤掉特殊 key
        content_briefs = {k: v for k, v in briefs.items() if not k.startswith('__')}

        if not content_briefs:
            return ""

        prompt = PromptTemplates.executive_summary_prompt(
            content_briefs, section_configs, self.language
        )

        response = self.claude.call(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.4
        )

        return response.strip()

    def _parse_ids(self, response: str) -> List[int]:
        """
        解析 filter prompt 的响应

        支持格式: "0,3,7,12" 或 "NONE"
        """
        response = response.strip()

        # 空响应或 NONE
        if not response or response.upper() == "NONE":
            return []

        # 提取数字
        import re
        numbers = re.findall(r'\d+', response)

        try:
            return [int(n) for n in numbers]
        except ValueError:
            return []

    def save_analyzed_data(self, briefs: Dict[str, List[Dict]], output_path: Path):
        """保存分析结果到 JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(briefs, f, indent=2, ensure_ascii=False)

        print(f"💾 已保存分析数据: {output_path}")

    def load_analyzed_data(self, input_path: Path) -> Dict[str, List[Dict]]:
        """从 JSON 加载分析结果"""
        with open(input_path, encoding='utf-8') as f:
            return json.load(f)
