# Newsloom Template System

完全解耦的可插拔模板系统，支持自定义 HTML 和 Markdown 主题。

## 目录结构

```
templates/
  dark-pro/          # 专业暗色主题（默认）
    meta.yaml        # 模板元信息
    report.html.j2   # HTML Jinja2 模板
    report.md.j2     # Markdown Jinja2 模板
  minimal/           # 极简主题
    meta.yaml
    report.html.j2
    report.md.j2
```

## 使用方法

### 1. 选择模板

在 `config/config.yaml` 中设置模板名称：

```yaml
pipeline:
  generate:
    template: "dark-pro"  # 或 "minimal"
```

### 2. Section 配置

Section 的元信息（emoji、标题、颜色等）在 `config/sections.yaml` 中定义：

```yaml
sections:
  ai:
    title: 'AI & 科技'
    emoji: '🤖'
    order: 1
    color: '#6366f1'
    description: 'AI 和机器学习相关新闻'
```

### 3. 模板变量

模板中可使用以下变量：

**通用变量:**
- `date_str`: 日期字符串 (如 "2024-02-12")
- `generated_time`: 生成时间戳
- `total_items`: 总条目数
- `section_configs`: Section 元信息字典
- `section_order`: Section 排序列表

**内容变量 (briefs 字典):**
- `briefs`: 按 section 分组的内容
  - `briefs[section_key]`: 某个 section 的条目列表
  - 每个条目包含：
    - `title` / `headline`: 标题
    - `url`: 链接
    - `source`: 来源
    - `text` / `detail`: 详细内容

### 4. 创建自定义模板

1. 在 `templates/` 下新建目录，如 `my-theme/`
2. 创建 `meta.yaml`:

```yaml
name: "My Theme"
author: "Your Name"
version: "1.0.0"
description: "自定义主题描述"
default_theme: "light"  # 或 "dark"
supports:
  - html
  - markdown
```

3. 创建 `report.html.j2` 和 `report.md.j2`（参考 `dark-pro` 模板）

4. 在 `config.yaml` 中设置 `template: "my-theme"`

## 内置模板

### dark-pro
- 专业暗色主题
- 侧边栏导航
- Section 颜色区分
- 响应式设计
- 主题切换（深色/浅色）

### minimal
- 极简设计
- 衬线字体
- 适合打印
- 无 JavaScript
- 专注内容

## 模板开发提示

### HTML 模板
- 使用 Jinja2 语法
- 循环渲染 sections: `{% for section_key in section_order %}`
- 访问 section 元信息: `{{ section_configs[section_key].emoji }}`
- 过滤空 section: `{% if section_key in briefs and briefs[section_key]|length > 0 %}`

### Markdown 模板
- 生成目录时使用 section emoji 和 title
- 保持格式简洁
- 支持 GitHub Flavored Markdown

### CSS 内联
- 推荐将 CSS 直接内联到 `<style>` 标签
- 或单独创建 `styles.css` 并在模板中引用

## 向后兼容

如果模板目录不存在或加载失败，系统会自动降级到内置的 fallback 模板，确保报告始终可以生成。

## 示例

查看现有模板代码以了解最佳实践：
- `dark-pro/report.html.j2` - 复杂的专业主题
- `minimal/report.html.j2` - 简洁的极简主题
