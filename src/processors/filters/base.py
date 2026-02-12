"""过滤策略抽象基类"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from sources.base import Item


class FilterStrategy(ABC):
    """
    过滤策略抽象基类

    所有自定义过滤策略都应该继承这个类
    并实现 filter() 方法
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化过滤策略

        Args:
            config: 该策略的配置字典
        """
        self.config = config
        self.min_score = config.get('min_score', 0)
        self.blacklist = config.get('blacklist', [])

    @abstractmethod
    def calculate_score(self, item: Item) -> float:
        """
        计算 item 的得分

        Args:
            item: 要评分的 Item

        Returns:
            float: 得分
        """
        pass

    def filter(self, item: Item) -> Optional[float]:
        """
        过滤单个 item

        Args:
            item: 要过滤的 Item

        Returns:
            Optional[float]: 如果通过过滤返回得分，否则返回 None
        """
        # 检查黑名单
        if self.blacklist:
            text = f"{item.title} {item.text}".lower()
            for blocked in self.blacklist:
                if blocked.lower() in text:
                    return None

        # 计算得分
        score = self.calculate_score(item)

        # 检查最低分
        if score >= self.min_score:
            return score

        return None

    def __repr__(self):
        return f"{self.__class__.__name__}(min_score={self.min_score})"
