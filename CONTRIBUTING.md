# 贡献指南

感谢您对 Newsloom 的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告 Bug

如果您发现了 Bug，请：

1. 在 [Issues](https://github.com/zhangjunmengyang/Newsloom/issues) 中搜索是否已有相关报告
2. 如果没有，创建新 Issue，包含：
   - 清晰的标题和描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（Python 版本、操作系统等）
   - 相关日志或截图

### 提出新功能

如果您有新功能建议：

1. 在 [Discussions](https://github.com/zhangjunmengyang/Newsloom/discussions) 中发起讨论
2. 描述功能的使用场景和价值
3. 如果可能，提供实现思路

### 贡献代码

#### 1. Fork 仓库

点击右上角的 "Fork" 按钮。

#### 2. 克隆到本地

```bash
git clone https://github.com/你的用户名/Newsloom.git
cd Newsloom
```

#### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
```

分支命名规范：
- `feature/xxx` - 新功能
- `fix/xxx` - Bug 修复
- `docs/xxx` - 文档改进
- `refactor/xxx` - 代码重构

#### 4. 进行开发

- 遵循现有代码风格
- 添加必要的注释和文档
- 确保代码通过测试

#### 5. 提交更改

```bash
git add .
git commit -m "feat: 添加新功能描述"
```

提交信息规范（遵循 [Conventional Commits](https://www.conventionalcommits.org/)）：

- `feat:` - 新功能
- `fix:` - Bug 修复
- `docs:` - 文档更新
- `style:` - 代码格式调整（不影响功能）
- `refactor:` - 代码重构
- `test:` - 测试相关
- `chore:` - 构建/工具相关

#### 6. 推送到 GitHub

```bash
git push origin feature/your-feature-name
```

#### 7. 创建 Pull Request

1. 访问您的 Fork 仓库
2. 点击 "Compare & pull request"
3. 填写 PR 描述：
   - 更改的内容
   - 相关 Issue（如有）
   - 测试情况
   - 截图（如适用）

## 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://pep8.org/)
- 使用 `black` 格式化代码
- 最大行长度：100 字符

```bash
# 格式化代码
black src/
```

### 文档字符串

使用 Google 风格的 docstring：

```python
def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
    """
    抓取数据并返回统一格式的列表

    Args:
        hours_ago: 只抓取最近 N 小时的数据（None = 全部）

    Returns:
        List[Item]: 统一格式的 Item 列表

    Raises:
        ValueError: 当参数无效时
    """
    pass
```

### 类型注解

尽可能添加类型注解：

```python
from typing import List, Optional, Dict, Any

def process_items(items: List[Item], config: Dict[str, Any]) -> Optional[List[Item]]:
    pass
```

## 测试

### 运行测试

```bash
pytest tests/
```

### 编写测试

为新功能添加测试：

```python
# tests/test_my_feature.py
import pytest
from src.sources.my_source import MySource

def test_my_source_fetch():
    config = {'enabled': True, 'channel': 'test'}
    source = MySource(config)
    items = source.fetch()

    assert len(items) > 0
    assert items[0].source == 'my_source'
```

## 贡献新数据源

如果您要贡献新数据源：

1. 在 `src/sources/` 创建新文件
2. 继承 `DataSource` 基类
3. 实现 `fetch()` 方法
4. 在 `registry.py` 中注册
5. 添加配置示例到 `config/sources.yaml`
6. 更新 `docs/EXTENDING.md`
7. 添加测试到 `tests/test_sources.py`

示例 PR：[添加 Twitter 数据源](https://github.com/zhangjunmengyang/Newsloom/pull/XXX)

## 贡献新过滤策略

如果您要贡献新过滤策略：

1. 在 `src/processors/filters/` 创建新文件
2. 继承 `FilterStrategy` 基类
3. 实现 `calculate_score()` 方法
4. 在 `__init__.py` 中注册
5. 添加配置示例到 `config/filters.yaml`
6. 更新文档
7. 添加测试

## 文档贡献

文档同样重要！您可以：

- 修正错别字
- 改进现有文档
- 添加示例
- 翻译文档

## Code Review

所有 PR 都会经过 Code Review：

- 至少一位维护者 approve
- 通过 CI 测试
- 符合代码规范

## 行为准则

请保持友善和尊重。我们致力于营造一个开放、包容的社区环境。

## 问题？

如果您有任何问题，欢迎：

- 在 [Discussions](https://github.com/zhangjunmengyang/Newsloom/discussions) 中提问
- 加入我们的社区频道（待建立）

---

再次感谢您的贡献！ 🎉
