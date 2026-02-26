"""Layer 2.5: 推荐系统式排序 — 粗排 + 精排 + 去重聚合

设计思想：
- 候选池：所有源 fetch 后的全量数据
- 粗排（规则）：关键词 × 来源权威度 × 时效性 × 互动量 → 快速打分，取 Top N
- 精排（AI）：Claude 评估 relevance × impact × urgency → 精确排序
- 去重聚合：同一事件多源报道合并
- 个性化：根据用户画像调整权重
"""

import re
import hashlib
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from sources.base import Item


# ============================================================
# 用户画像 — 老板的兴趣权重
# ============================================================
USER_PROFILE = {
    # AI/ML 方向（核心兴趣）
    "ai_core": {
        "weight": 2.0,
        "keywords": [
            "llm", "large language model", "transformer", "gpt", "claude",
            "gemini", "reasoning", "agent", "rag", "fine-tuning", "rlhf",
            "multimodal", "diffusion", "openai", "anthropic", "deepseek",
            "mistral", "scaling law", "inference", "quantization", "moe",
            "大模型", "推理", "智能体", "微调",
        ]
    },
    # AI 应用/工程（工作相关）
    "ai_engineering": {
        "weight": 1.8,
        "keywords": [
            "deployment", "serving", "mlops", "vector database", "embedding",
            "prompt engineering", "function calling", "tool use", "ai agent",
            "coding assistant", "copilot", "cursor", "vscode", "ide",
            "api", "sdk", "framework", "benchmark", "evaluation",
        ]
    },
    # Crypto/量化（第二赛道）
    "crypto_quant": {
        "weight": 1.8,
        "keywords": [
            "bitcoin", "ethereum", "btc", "eth", "solana", "defi",
            "trading", "quantitative", "algorithmic", "arbitrage",
            "market making", "liquidity", "on-chain", "whale",
            "polymarket", "prediction market", "perpetual", "futures",
            "stablecoin", "usdc", "usdt", "layer 2", "rollup",
            "比特币", "以太坊", "量化", "套利", "链上",
        ]
    },
    # 开源/工具链
    "tools": {
        "weight": 1.3,
        "keywords": [
            "open source", "github", "rust", "python", "typescript",
            "cli", "terminal", "developer tool", "productivity",
            "automation", "self-hosted", "homelab",
        ]
    },
    # 创业/商业
    "business": {
        "weight": 1.0,
        "keywords": [
            "startup", "funding", "acquisition", "ipo", "revenue",
            "valuation", "series a", "series b", "unicorn",
        ]
    },
}

# 来源权威度分数（满分 10）
SOURCE_AUTHORITY = {
    # Tier 1: 官方/顶级
    "OpenAI Blog": 10, "Google AI Blog": 10, "Google DeepMind": 10,
    "Anthropic": 10, "Meta Engineering": 9, "Microsoft Research": 9,
    "HuggingFace Blog": 9, "NVIDIA AI": 9,
    # Tier 2: 顶级媒体
    "MIT Tech Review": 9, "arXiv": 9, "The Gradient": 8,
    "Lil'Log (Lilian Weng)": 9, "Simon Willison": 8,
    "Import AI (Jack Clark)": 8,
    # Tier 3: 主流科技媒体
    "TechCrunch": 7, "The Verge": 7, "Ars Technica": 7,
    "Wired": 7, "VentureBeat AI": 7, "The Decoder": 7,
    "InfoQ": 7, "Lobsters": 7,
    # Tier 4: 行业媒体
    "CoinDesk": 7, "Cointelegraph": 6, "CryptoSlate": 6,
    "Decrypt": 6, "Bankless": 7, "The Defiant": 6,
    "WSJ Markets": 8, "Financial Times": 8, "CNBC": 7,
    # Tier 5: 社区/综合
    "Hacker News": 7, "GitHub Trending": 7,
    "AI News": 6, "36kr": 6, "机器之心": 7, "量子位": 6,
    # Tier 6: 一般
    "Dev.to AI": 5, "Slashdot": 5,
    # 交易所上线 (高价值 alpha 信号)
    "exchange_listing": 10,
    "Binance": 10, "Upbit": 10, "Bithumb": 10,
    "Coinbase": 9, "OKX": 9, "Bybit": 8,
    # Anthropic 官方
    "anthropic_news": 10, "Anthropic News": 10,
    # Web Search
    "web_search": 6,
    # 默认
    "_default": 5,
}


class CoarseRanker:
    """
    粗排器 — 规则打分，快速筛选候选池
    
    评分维度：
    1. 关键词匹配（与用户画像对齐）
    2. 来源权威度
    3. 时效性衰减
    4. 互动量加成（HN score、GitHub stars 等）
    """

    def __init__(self, user_profile: dict = None, source_authority: dict = None):
        self.profile = user_profile or USER_PROFILE
        self.authority = source_authority or SOURCE_AUTHORITY
        # 预编译关键词正则
        self._keyword_patterns = {}
        for category, info in self.profile.items():
            patterns = []
            for kw in info["keywords"]:
                patterns.append(re.compile(re.escape(kw), re.IGNORECASE))
            self._keyword_patterns[category] = (patterns, info["weight"])

    def rank(self, items: List[Item], top_n: int = 200) -> List[Item]:
        """
        粗排：对所有候选打分，返回 Top N
        
        Args:
            items: 全量候选
            top_n: 返回前 N 条
        Returns:
            按分数降序排列的 Top N items
        """
        scored = []
        for item in items:
            score = self._score_item(item)
            item.score = score
            scored.append((score, item))

        # 按分数降序
        scored.sort(key=lambda x: x[0], reverse=True)

        result = [item for _, item in scored[:top_n]]
        return result

    def _score_item(self, item: Item) -> float:
        """
        综合打分
        
        score = keyword_score × authority × freshness × engagement_bonus
        """
        text = f"{item.title} {item.text}".lower()

        # 1. 关键词得分（用户画像匹配）
        kw_score = 0.0
        for category, (patterns, weight) in self._keyword_patterns.items():
            match_count = 0
            for pat in patterns:
                if pat.search(text):
                    match_count += 1
            if match_count > 0:
                # 每个 category 的贡献 = min(matches, 3) × weight
                kw_score += min(match_count, 3) * weight

        # 基础分：即使没匹配关键词也有基础分（防止好内容被埋）
        base_score = max(kw_score, 1.0)

        # 2. 来源权威度 (0.5 ~ 1.0)
        meta = item.metadata or {}
        source_name = meta.get("feed_name") or meta.get("feed_title") or item.source
        authority = self.authority.get(source_name, self.authority["_default"])
        authority_factor = 0.5 + (authority / 20.0)  # 5 → 0.75, 10 → 1.0

        # 3. 时效性衰减 (1.0 → 0.3 over 48h) + breaking news 升权
        now = datetime.now(timezone.utc)
        age_hours = (now - item.published_at).total_seconds() / 3600
        freshness = max(0.3, 1.0 - (age_hours / 72.0))
        # Breaking news (<2h) 额外 +30%
        if age_hours < 2:
            freshness = min(freshness * 1.3, 1.5)

        # 4. 互动量加成
        engagement = 1.0
        if meta.get("score"):  # HN score
            hn_score = meta["score"]
            engagement += min(hn_score / 500, 1.0)  # 500+ score → +1.0
        if meta.get("stars"):  # GitHub stars
            stars = meta["stars"]
            engagement += min(stars / 10000, 0.8)
        if meta.get("daily_stars"):
            daily = meta["daily_stars"]
            engagement += min(daily / 500, 0.5)
        if meta.get("comments"):
            comments = meta["comments"]
            engagement += min(comments / 200, 0.3)

        # 5. 特殊信号加成
        # 交易所上线 → 强制高分（这是 alpha 信号，不能被埋）
        if item.source == 'exchange_listing':
            title_lower = item.title.lower()
            # 真实上线公告（排除 CoinGecko Trending 这类）
            if any(k in title_lower for k in ['上线', 'listing', 'new pair', 'new trading', '新增']):
                base_score = max(base_score, 20.0)
            # 韩国交易所额外加分（溢价效应）
            if '🇰🇷' in item.title or any(k in title_lower for k in ['upbit', 'bithumb']):
                base_score *= 1.5

        # Anthropic 官方公告 → 固定高分
        if item.source in ('anthropic_news', 'anthropic'):
            base_score = max(base_score, 12.0)

        final_score = base_score * authority_factor * freshness * engagement
        return round(final_score, 3)


class Deduplicator:
    """
    去重聚合器 — 同一事件多源报道合并
    
    策略：
    1. URL 去重（精确匹配）
    2. 标题相似度（编辑距离 / Jaccard）
    3. 保留最高分的版本，其余合并为 related_sources
    """

    def __init__(self, similarity_threshold: float = 0.6):
        self.threshold = similarity_threshold

    def deduplicate(self, items: List[Item]) -> List[Item]:
        """
        去重并聚合
        
        Returns:
            去重后的 items（已排序）
        """
        if not items:
            return []

        # Phase 1: URL 去重
        seen_urls = {}
        url_deduped = []
        for item in items:
            normalized_url = self._normalize_url(item.url)
            if normalized_url in seen_urls:
                # 保留分数更高的
                existing = seen_urls[normalized_url]
                if item.score > existing.score:
                    url_deduped.remove(existing)
                    url_deduped.append(item)
                    seen_urls[normalized_url] = item
            else:
                seen_urls[normalized_url] = item
                url_deduped.append(item)

        # Phase 2: 标题相似度去重
        clusters = self._cluster_by_title(url_deduped)

        # 每个 cluster 取最高分
        result = []
        for cluster in clusters:
            best = max(cluster, key=lambda x: x.score)
            if len(cluster) > 1:
                # 记录其他来源
                other_sources = [
                    (item.metadata or {}).get("feed_name", item.source)
                    for item in cluster if item != best
                ]
                best.metadata = best.metadata or {}
                best.metadata["related_sources"] = other_sources
                best.metadata["coverage_count"] = len(cluster)
            result.append(best)

        return result

    def _normalize_url(self, url: str) -> str:
        """URL 标准化"""
        url = url.strip().rstrip("/")
        # 去掉常见追踪参数
        for param in ["utm_source", "utm_medium", "utm_campaign", "ref"]:
            url = re.sub(rf'[?&]{param}=[^&]*', '', url)
        return url

    def _cluster_by_title(self, items: List[Item]) -> List[List[Item]]:
        """按标题相似度聚类"""
        clusters = []
        used = set()

        for i, item_a in enumerate(items):
            if i in used:
                continue
            cluster = [item_a]
            used.add(i)

            tokens_a = self._tokenize(item_a.title)

            for j, item_b in enumerate(items):
                if j in used or j <= i:
                    continue
                tokens_b = self._tokenize(item_b.title)
                sim = self._jaccard(tokens_a, tokens_b)
                if sim >= self.threshold:
                    cluster.append(item_b)
                    used.add(j)

            clusters.append(cluster)

        return clusters

    def _tokenize(self, text: str) -> set:
        """分词（简单按空格 + 特殊字符）"""
        words = re.findall(r'\w+', text.lower())
        # 去停用词
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on",
                       "at", "to", "for", "of", "and", "or", "with", "from", "by",
                       "that", "this", "it", "its", "how", "what", "why", "when"}
        return {w for w in words if w not in stop_words and len(w) > 1}

    def _jaccard(self, set_a: set, set_b: set) -> float:
        """Jaccard 相似度"""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0


class RankingPipeline:
    """
    完整排序 pipeline
    
    候选池 → 粗排 → 去重 → [精排由 analyzer 负责]
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.coarse_ranker = CoarseRanker()
        self.deduplicator = Deduplicator(
            similarity_threshold=self.config.get("dedup_threshold", 0.55)
        )

    def process(self, items: List[Item], top_n: int = 200) -> List[Item]:
        """
        执行粗排 + 去重
        
        Args:
            items: 全量候选
            top_n: 粗排后保留条数
        Returns:
            排序+去重后的 items
        """
        print(f"\n📊 排序管线启动...")
        print(f"   候选池: {len(items)} 条")

        # Step 1: 粗排
        ranked = self.coarse_ranker.rank(items, top_n=top_n)
        print(f"   粗排 Top {top_n}: {len(ranked)} 条")
        if ranked:
            print(f"   分数范围: {ranked[0].score:.2f} ~ {ranked[-1].score:.2f}")

        # Step 2: 去重
        deduped = self.deduplicator.deduplicate(ranked)
        removed = len(ranked) - len(deduped)
        if removed > 0:
            print(f"   去重: 移除 {removed} 条重复")

        print(f"   ✅ 最终: {len(deduped)} 条")
        return deduped
