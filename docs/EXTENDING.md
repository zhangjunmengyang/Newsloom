# Newsloom 扩展指南

本文档介绍如何扩展 Newsloom 的功能。

## 目录

- [添加新数据源](#添加新数据源)
- [添加新过滤策略](#添加新过滤策略)
- [自定义 Pipeline](#自定义-pipeline)

---

## 添加新数据源

### 1. 创建数据源类

在 `src/sources/` 目录下创建新文件，例如 `my_source.py`:

```python
from typing import List, Optional
from .base import DataSource, Item

class MyCustomSource(DataSource):
    """我的自定义数据源"""

    def get_source_name(self) -> str:
        return "my_source"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """
        实现数据抓取逻辑

        Returns:
            List[Item]: 统一格式的 Item 列表
        """
        items = []

        # 你的抓取逻辑
        # ...

        # 使用 _make_item 创建标准 Item
        item = self._make_item(
            native_id="unique_id",
            title="标题",
            text="正文内容",
            url="https://example.com",
            author="作者",
            published_at=datetime.now(timezone.utc),
            metadata={
                # 可选的元数据
                'custom_field': 'value'
            }
        )
        items.append(item)

        return items
```

### 2. 注册数据源

在 `src/sources/registry.py` 中注册:

```python
from .my_source import MyCustomSource

SOURCE_MAP = {
    # ... 其他数据源
    'my_source': MyCustomSource,
}
```

### 3. 配置数据源

在 `config/sources.yaml` 中添加配置:

```yaml
sources:
  my_custom_source:
    enabled: true
    channel: "custom"      # 分类频道
    type: "my_source"      # 对应 SOURCE_MAP 的 key
    # 自定义配置参数
    api_key: ${MY_API_KEY}
    max_items: 50
```

### 4. 测试运行

```bash
python3 run.py --layers fetch
```

---

## 添加新过滤策略

### 方法 1: 继承 FilterStrategy (推荐)

在 `src/processors/filters/` 目录下创建新文件:

```python
from .base import FilterStrategy
from sources.base import Item

class MyCustomFilter(FilterStrategy):
    """我的自定义过滤策略"""

    def __init__(self, config):
        super().__init__(config)
        # 初始化自定义参数
        self.my_param = config.get('my_param', 0)

    def calculate_score(self, item: Item) -> float:
        """
        计算得分逻辑

        Returns:
            float: 得分（会自动与 min_score 比较）
        """
        score = 0.0

        # 你的评分逻辑
        if 'important' in item.title.lower():
            score += 10

        return score
```

注册策略（在 `src/processors/filters/__init__.py`）:

```python
from .my_filter import MyCustomFilter

FILTER_REGISTRY = {
    # ... 其他策略
    'my_filter': MyCustomFilter,
}
```

### 方法 2: 快速创建（简单场景）

```python
from processors.filter import create_custom_filter

def my_score_function(item):
    if len(item.title) > 50:
        return 5
    return 1

create_custom_filter('length_based', my_score_function)
```

### 3. 配置使用

在 `config/filters.yaml` 中:

```yaml
channels:
  my_channel:
    strategy: my_filter      # 使用你的策略
    min_score: 5
    my_param: 100            # 自定义参数
    blacklist:
      - spam
```

---

## 自定义 Pipeline

### 1. 灵活的层级控制

只运行特定层:

```bash
# 只抓取
python3 run.py --layers fetch

# 只过滤
python3 run.py --layers filter

# 自定义组合
python3 run.py --layers fetch,filter,generate
```

### 2. 配置驱动的 Pipeline

在 `config/config.yaml` 中配置启用的层:

```yaml
pipeline:
  enabled_layers: ["fetch", "filter", "analyze", "generate"]

  fetch:
    parallel_workers: 10    # 并行数
    timeout_per_source: 30  # 超时时间

  filter:
    max_age_hours: 48      # 只要48小时内的
    min_score: 3           # 最低分数
```

### 3. 完全自定义处理流程

创建自定义脚本:

```python
from pathlib import Path
from sources.registry import SourceRegistry
from processors.fetcher import ParallelFetcher
from processors.filter import SmartFilter
from utils.state import StateManager

# 初始化
state = StateManager(Path('data/state/state.json'))
registry = SourceRegistry('config/sources.yaml')

# 自定义流程
sources = registry.get_enabled_sources()
fetcher = ParallelFetcher(sources, state)

# 1. 抓取
items = fetcher.fetch_all(hours_ago=12)  # 只要12小时的

# 2. 自定义处理
items = [item for item in items if len(item.title) > 20]

# 3. 过滤
import yaml
with open('config/filters.yaml') as f:
    filter_config = yaml.safe_load(f)

smart_filter = SmartFilter(filter_config)
filtered = smart_filter.filter_items(items, max_age_hours=12)

# 4. 自定义输出
for item in filtered[:10]:  # 只要前10条
    print(f"{item.title}: {item.score}")
```

---

## 进阶技巧

### 动态加载插件

创建 `plugins/` 目录，在运行时加载:

```python
import importlib
import sys
from pathlib import Path

# 加载自定义数据源
plugin_dir = Path('plugins')
if plugin_dir.exists():
    sys.path.insert(0, str(plugin_dir))

    for plugin_file in plugin_dir.glob('*_source.py'):
        module_name = plugin_file.stem
        module = importlib.import_module(module_name)

        # 自动注册
        from sources.registry import SourceRegistry
        SourceRegistry.SOURCE_MAP[module_name] = module.CustomSource
```

### 环境变量配置

在配置文件中使用环境变量:

```yaml
sources:
  my_api:
    api_key: ${MY_API_KEY}           # 从环境变量读取
    api_url: ${MY_API_URL}
    enabled: ${ENABLE_MY_API:false}  # 带默认值
```

### 多配置文件支持

```bash
# 使用不同配置文件
python3 run.py --config config/production.yaml
python3 run.py --config config/testing.yaml
```

---

## 常见模式

### 组合多个过滤器

```python
class CombinedFilter(FilterStrategy):
    """组合多个过滤策略"""

    def __init__(self, config):
        super().__init__(config)
        from .keyword_filter import KeywordScoreFilter
        from .upvote_filter import UpvoteWeightedFilter

        self.filter1 = KeywordScoreFilter(config)
        self.filter2 = UpvoteWeightedFilter(config)

    def calculate_score(self, item):
        # 取两个策略的最大值
        return max(
            self.filter1.calculate_score(item),
            self.filter2.calculate_score(item)
        )
```

### 条件化数据源

```python
class ConditionalSource(DataSource):
    """根据时间条件决定抓取源"""

    def fetch(self, hours_ago=None):
        from datetime import datetime

        if datetime.now().hour < 12:
            # 上午用源A
            return self._fetch_source_a()
        else:
            # 下午用源B
            return self._fetch_source_b()
```

---

## 最佳实践

1. **命名规范**: 数据源以 `*Source` 结尾，过滤器以 `*Filter` 结尾
2. **错误处理**: 在 `fetch()` 和 `calculate_score()` 中添加 try-except
3. **日志输出**: 使用 `print()` 输出关键信息，方便调试
4. **配置验证**: 在 `__init__` 中验证必需的配置参数
5. **文档字符串**: 为自定义类添加清晰的 docstring

---

## 需要帮助？

- 查看 `src/sources/rss.py` - RSS 数据源示例
- 查看 `src/processors/filters/` - 过滤策略示例
- 提交 Issue: https://github.com/zhangjunmengyang/Newsloom/issues
