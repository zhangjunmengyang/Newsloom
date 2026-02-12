"""Layer 2: 智能过滤 - 粗排精排 + 候选池 + 去重"""

import json
import math
import re
from typing import List, Dict, Tuple
from pathlib import Path
from collections import Counter

from sources.base import Item
from utils.time_utils import is_within_hours
from .filters import get_filter, FILTER_REGISTRY


# ============================================================
# 老板关注领域关键词（用于 BM25 相关性打分）
# ============================================================
OWNER_INTEREST_KEYWORDS = {
    # AI / LLM（核心）
    'llm': 8, 'large language model': 8, 'gpt': 7, 'claude': 7, 'gemini': 6,
    'transformer': 7, 'attention': 5, 'rag': 7, 'agent': 6, 'reasoning': 6,
    'fine-tuning': 6, 'finetuning': 6, 'prompt': 5, 'embedding': 5,
    'multimodal': 6, 'vision language': 6, 'code generation': 6,
    'openai': 6, 'anthropic': 6, 'deepmind': 5, 'meta ai': 5,
    'open source': 5, 'open-source': 5, 'hugging face': 5, 'huggingface': 5,
    'inference': 5, 'quantization': 6, 'gguf': 5, 'ggml': 5, 'ollama': 5,
    'local llm': 7, 'vllm': 5, 'lora': 6, 'qlora': 6,
    'deep learning': 5, 'machine learning': 4, 'neural network': 4,
    'ai': 3, 'artificial intelligence': 4,
    # 中文 AI 关键词
    '大模型': 8, '大语言模型': 8, '人工智能': 4, '机器学习': 4,
    '深度学习': 5, '微调': 6, '推理': 5, '智能体': 6,

    # Crypto / 量化
    'bitcoin': 6, 'btc': 5, 'ethereum': 6, 'eth': 5, 'solana': 5, 'sol': 4,
    'defi': 7, 'web3': 5, 'blockchain': 5, 'smart contract': 6,
    'trading': 6, 'quantitative': 7, 'quant': 7, 'algo trading': 8,
    'algorithmic trading': 8, 'backtest': 7, 'alpha': 6, 'strategy': 4,
    'market making': 7, 'mev': 6, 'dex': 5, 'cex': 4,
    'yield': 5, 'staking': 4, 'airdrop': 3,
    # 中文量化关键词
    '量化': 8, '量化交易': 8, '回测': 7, '策略': 5, '套利': 6,
    '比特币': 6, '以太坊': 6, '加密货币': 5, '区块链': 5,

    # 开发工具
    'rust': 4, 'python': 3, 'typescript': 3, 'developer tool': 5,
    'cli': 4, 'api': 3, 'framework': 3, 'library': 3,
    'gpu': 5, 'cuda': 5, 'mlx': 5, 'tpu': 4,
}


class RelevanceScorer:
    """
    BM25 风格的文本相关性打分器（纯 Python 实现）

    基于老板关注领域关键词，给每条新闻打相关性分
    """

    def __init__(self, interest_keywords: dict = None, k1: float = 1.5, b: float = 0.75):
        self.keywords = interest_keywords or OWNER_INTEREST_KEYWORDS
        self.k1 = k1
        self.b = b

    def score(self, item: Item) -> float:
        """
        计算单条 item 的相关性分数

        Returns:
            float: 相关性分数（0~100）
        """
        text = f"{item.title} {item.title} {item.text}".lower()  # 标题权重 x2
        text_len = len(text.split())
        avg_len = 200  # 假设平均文档长度

        total_score = 0.0

        for keyword, weight in self.keywords.items():
            keyword_lower = keyword.lower()

            # 统计词频
            if ' ' in keyword_lower:
                tf = text.count(keyword_lower)
            else:
                tf = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', text))

            if tf == 0:
                continue

            # BM25 公式（简化版，IDF 用 keyword weight 替代）
            idf = weight  # 用人工权重替代 IDF
            norm_tf = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * text_len / avg_len))
            total_score += idf * norm_tf

        return total_score


class DedupEngine:
    """
    去重引擎 - 基于标题 Jaccard 相似度合并重复新闻
    """

    def __init__(self, threshold: float = 0.5):
        """
        Args:
            threshold: Jaccard 相似度阈值，超过则视为重复
        """
        self.threshold = threshold

    def _tokenize(self, text: str) -> set:
        """将标题分词为 token 集合"""
        text = text.lower()
        # 英文按空格/标点分词
        tokens = set(re.findall(r'[a-z0-9\u4e00-\u9fff]+', text))
        # 中文按字分词（简单但有效）
        chinese_chars = set(re.findall(r'[\u4e00-\u9fff]', text))
        tokens.update(chinese_chars)
        return tokens

    def _jaccard(self, set_a: set, set_b: set) -> float:
        """计算 Jaccard 相似度"""
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    def deduplicate(self, items: List[Item]) -> List[Item]:
        """
        去重：保留每组重复中得分最高的

        Returns:
            去重后的 Item 列表
        """
        if not items:
            return items

        # 预计算所有标题的 token 集合
        token_sets = [(item, self._tokenize(item.title)) for item in items]

        kept = []
        removed_count = 0

        for i, (item, tokens) in enumerate(token_sets):
            is_duplicate = False
            for j, kept_item in enumerate(kept):
                kept_tokens = self._tokenize(kept_item.title)
                sim = self._jaccard(tokens, kept_tokens)
                if sim >= self.threshold:
                    # 重复了，保留得分高的
                    if item.score > kept_item.score:
                        kept[j] = item
                    is_duplicate = True
                    removed_count += 1
                    break

            if not is_duplicate:
                kept.append(item)

        if removed_count > 0:
            print(f"     🔄 去重: 合并了 {removed_count} 条重复内容")

        return kept


class SmartFilter:
    """
    智能过滤器 - 支持多种可插拔的过滤策略 + BM25 粗排 + 候选池

    特性:
    - 按频道应用不同策略
    - BM25 相关性粗排（基于老板兴趣）
    - 候选池机制（低分内容备用）
    - 标题去重
    - 完全可扩展（添加新策略只需继承 FilterStrategy）
    """

    def __init__(self, config: dict):
        self.config = config
        self.channels = config.get('channels', {})
        self.defaults = config.get('defaults', {})
        self.relevance_scorer = RelevanceScorer()
        self.dedup_engine = DedupEngine(threshold=0.5)

    def filter_items(self, items: List[Item], max_age_hours: int = 48) -> List[Item]:
        """
        应用过滤策略 + 粗排 + 候选池 + 去重

        Args:
            items: 要过滤的 Item 列表
            max_age_hours: 最大时效（小时）

        Returns:
            通过过滤的 Item 列表（带得分）
        """
        print(f"\n🔍 过滤 {len(items)} 条数据...")
        print(f"   已注册策略: {list(FILTER_REGISTRY.keys())}")

        # Step 0: 全局去重
        items = self.dedup_engine.deduplicate(items)

        # 按频道分组
        by_channel = {}
        for item in items:
            by_channel.setdefault(item.channel, []).append(item)

        filtered = []
        candidate_pool = []  # 候选池

        # 对每个频道应用策略
        for channel in sorted(by_channel.keys()):
            channel_items = by_channel[channel]
            ch_config = self._get_channel_config(channel)
            strategy_name = ch_config.get('strategy', 'keyword_score')

            print(f"  📁 频道 '{channel}': {len(channel_items)} 条, 策略='{strategy_name}'")

            # 时效性过滤
            time_filtered = [
                item for item in channel_items
                if is_within_hours(item.published_at, max_age_hours)
            ]

            if len(time_filtered) < len(channel_items):
                print(f"     ⏰ 时效过滤: {len(time_filtered)}/{len(channel_items)} 在 {max_age_hours}h 内")

            # Step 1: BM25 相关性粗排打分
            for item in time_filtered:
                relevance = self.relevance_scorer.score(item)
                item.metadata['relevance_score'] = relevance

            # 应用原有过滤策略
            try:
                filter_class = get_filter(strategy_name)
                filter_instance = filter_class(ch_config)

                passed = []
                candidates = []

                for item in time_filtered:
                    score = filter_instance.filter(item)
                    relevance = item.metadata.get('relevance_score', 0)

                    if score is not None:
                        # 综合得分 = 原始策略得分 + 相关性加成
                        combined_score = score + relevance * 0.1
                        item.score = combined_score
                        item.filtered = True
                        passed.append(item)
                    elif relevance > 10:
                        # 原始策略没通过，但相关性高 → 进候选池
                        item.score = relevance * 0.1
                        item.filtered = True
                        candidates.append(item)

                filtered.extend(passed)
                candidate_pool.extend(candidates)

                print(f"     ✓ 通过: {len(passed)}/{len(time_filtered)}, 候选池: +{len(candidates)}")

            except Exception as e:
                print(f"     ✗ 策略 '{strategy_name}' 失败: {e}")

        # Step 2: 候选池补充（如果高分内容不够）
        min_total = 30  # 最少期望条数
        if len(filtered) < min_total and candidate_pool:
            # 按相关性排序候选池
            candidate_pool.sort(key=lambda x: x.metadata.get('relevance_score', 0), reverse=True)
            supplement_count = min(min_total - len(filtered), len(candidate_pool))
            supplement = candidate_pool[:supplement_count]
            filtered.extend(supplement)
            print(f"\n  📦 候选池补充: +{supplement_count} 条 (总计 {len(filtered)} 条)")

        # Step 3: 频道内去重
        filtered = self.dedup_engine.deduplicate(filtered)

        print(f"\n✅ 过滤完成: {len(filtered)} 条")
        return filtered

    def _get_channel_config(self, channel: str) -> dict:
        """
        获取频道配置，支持关键词继承

        配置示例:
        ```yaml
        channels:
          tech:
            keywords:
              _inherit: [ai]  # 继承 ai 频道的关键词
              programming: 3
        ```
        """
        if channel in self.channels:
            config = dict(self.channels[channel])

            # 处理关键词继承
            if 'keywords' in config and '_inherit' in config['keywords']:
                inherit_from = config['keywords']['_inherit']
                inherited_keywords = {}

                # 从其他频道继承关键词
                for parent_channel in inherit_from:
                    if parent_channel in self.channels:
                        parent_keywords = self.channels[parent_channel].get('keywords', {})
                        inherited_keywords.update(parent_keywords)

                # 移除 _inherit 标记
                del config['keywords']['_inherit']

                # 合并继承的和自己的关键词（自己的优先）
                merged_keywords = inherited_keywords.copy()
                merged_keywords.update(config['keywords'])
                config['keywords'] = merged_keywords

            return config

        return self.defaults.copy()

    def save_filtered_data(self, items: List[Item], output_path: Path):
        """保存过滤后的数据到 JSONL"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in items:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + '\n')

        print(f"💾 已保存过滤数据: {output_path}")

    def load_filtered_data(self, input_path: Path) -> List[Item]:
        """从 JSONL 加载过滤后的数据"""
        items = []

        with open(input_path, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    items.append(Item.from_dict(data))

        return items


def create_custom_filter(name: str, score_func):
    """
    快速创建自定义过滤策略的辅助函数

    示例:
    ```python
    # 创建一个只看标题的过滤器
    def title_only_score(item):
        if 'important' in item.title.lower():
            return 10
        return 0

    create_custom_filter('title_only', title_only_score)
    ```
    """
    from .filters.base import FilterStrategy
    from .filters import register_filter

    class CustomFilter(FilterStrategy):
        def calculate_score(self, item):
            return score_func(item)

    register_filter(name, CustomFilter)
    return CustomFilter
