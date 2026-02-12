"""投票加权过滤策略"""

from .base import FilterStrategy
from .keyword_filter import KeywordScoreFilter
from sources.base import Item


class UpvoteWeightedFilter(FilterStrategy):
    """
    基于投票数加权的评分策略

    结合关键词得分 + 社区投票数

    配置示例:
    ```yaml
    strategy: upvote_weighted
    min_score: 4
    upvote_multiplier: 2
    keywords:
      reinforcement learning: 5
    ```
    """

    def __init__(self, config):
        super().__init__(config)
        self.upvote_multiplier = config.get('upvote_multiplier', 1.0)
        # 使用关键词过滤器计算基础分
        self.keyword_filter = KeywordScoreFilter(config)

    def calculate_score(self, item: Item) -> float:
        """基础得分 + 投票加权"""
        # 基础关键词得分
        base_score = self.keyword_filter.calculate_score(item)

        # 查找投票数
        upvotes = 0
        metadata = item.metadata or {}

        # 尝试不同的字段名
        for field in ['upvotes', 'stars', 'score', 'points', 'likes']:
            if field in metadata:
                upvotes = metadata[field]
                break

        # 投票加权
        bonus = upvotes * self.upvote_multiplier

        return base_score + bonus

    def __repr__(self):
        return f"UpvoteWeightedFilter(multiplier={self.upvote_multiplier}, min_score={self.min_score})"
