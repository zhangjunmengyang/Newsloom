"""过滤策略模块 - 完全可扩展"""

from .base import FilterStrategy
from .keyword_filter import KeywordScoreFilter
from .upvote_filter import UpvoteWeightedFilter
from .passthrough_filter import PassThroughFilter

# 过滤策略注册表
FILTER_REGISTRY = {
    'keyword_score': KeywordScoreFilter,
    'upvote_weighted': UpvoteWeightedFilter,
    'pass_through': PassThroughFilter,
}

def register_filter(name: str, filter_class):
    """注册自定义过滤策略"""
    FILTER_REGISTRY[name] = filter_class

def get_filter(name: str) -> FilterStrategy:
    """获取过滤策略实例"""
    if name not in FILTER_REGISTRY:
        raise ValueError(f"Unknown filter strategy: {name}")
    return FILTER_REGISTRY[name]

__all__ = [
    'FilterStrategy',
    'KeywordScoreFilter',
    'UpvoteWeightedFilter',
    'PassThroughFilter',
    'FILTER_REGISTRY',
    'register_filter',
    'get_filter',
]
