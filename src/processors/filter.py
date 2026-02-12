"""Layer 2: 智能过滤 - 完全可扩展的过滤系统"""

import json
from typing import List, Dict
from pathlib import Path

from sources.base import Item
from utils.time_utils import is_within_hours
from .filters import get_filter, FILTER_REGISTRY


class SmartFilter:
    """
    智能过滤器 - 支持多种可插拔的过滤策略

    特性:
    - 按频道应用不同策略
    - 完全可扩展（添加新策略只需继承 FilterStrategy）
    - 时效性过滤
    - 支持关键词继承
    """

    def __init__(self, config: dict):
        self.config = config
        self.channels = config.get('channels', {})
        self.defaults = config.get('defaults', {})

    def filter_items(self, items: List[Item], max_age_hours: int = 48) -> List[Item]:
        """
        应用过滤策略

        Args:
            items: 要过滤的 Item 列表
            max_age_hours: 最大时效（小时）

        Returns:
            通过过滤的 Item 列表（带得分）
        """
        print(f"\n🔍 过滤 {len(items)} 条数据...")
        print(f"   已注册策略: {list(FILTER_REGISTRY.keys())}")

        # 按频道分组
        by_channel = {}
        for item in items:
            by_channel.setdefault(item.channel, []).append(item)

        filtered = []

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

            # 应用过滤策略
            try:
                filter_class = get_filter(strategy_name)
                filter_instance = filter_class(ch_config)

                for item in time_filtered:
                    score = filter_instance.filter(item)

                    if score is not None:
                        item.score = score
                        item.filtered = True
                        filtered.append(item)

                passed = sum(1 for item in time_filtered if item.filtered)
                print(f"     ✓ 通过: {passed}/{len(time_filtered)}")

            except Exception as e:
                print(f"     ✗ 策略 '{strategy_name}' 失败: {e}")

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
