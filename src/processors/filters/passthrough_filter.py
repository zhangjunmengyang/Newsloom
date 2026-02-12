"""直通过滤策略"""

from .base import FilterStrategy
from sources.base import Item


class PassThroughFilter(FilterStrategy):
    """
    直通策略 - 所有 item 都通过

    用于已经被源过滤过的数据（如 GitHub Trending）

    配置示例:
    ```yaml
    strategy: pass_through
    min_score: 0
    ```
    """

    def calculate_score(self, item: Item) -> float:
        """始终返回固定分数"""
        return 1.0

    def __repr__(self):
        return "PassThroughFilter(pass_all=True)"
