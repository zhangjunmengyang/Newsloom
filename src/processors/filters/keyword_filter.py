"""关键词评分过滤策略"""

from .base import FilterStrategy
from sources.base import Item
from utils.text_utils import calculate_keyword_score


class KeywordScoreFilter(FilterStrategy):
    """
    基于关键词的评分策略

    配置示例:
    ```yaml
    strategy: keyword_score
    min_score: 3
    keywords:
      ai: 5
      machine learning: 4
    blacklist:
      - spam
    ```
    """

    def __init__(self, config):
        super().__init__(config)
        self.keywords = config.get('keywords', {})

    def calculate_score(self, item: Item) -> float:
        """基于关键词匹配计算得分"""
        full_text = f"{item.title} {item.text}"
        score = calculate_keyword_score(full_text, self.keywords)
        return score

    def __repr__(self):
        return f"KeywordScoreFilter(keywords={len(self.keywords)}, min_score={self.min_score})"
