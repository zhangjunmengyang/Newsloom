# Template Deep Upgrade Guide — Commercial Quality Standard

> 本文档是模板深度优化的唯一标准。每个模板升级必须参照此文档。

## 目标
将每个模板从"能用"提升到"能卖 $29"的商业级品质。

## 质量标杆
- **premium** 模板是当前最高质量的参考 — 605 行，完整 design tokens、渐变、glass morphism、多层阴影
- 目标：每个模板 ≥ 600 行，具备完整的设计系统

---

## 必须达标的 6 个维度

### 1. Design Tokens（CSS 变量系统）
每个模板必须在 `:root` 中定义完整的设计变量：
- **背景色**: 至少 4 级（primary → secondary → card → surface → hover）
- **文字色**: 至少 4 级（primary → secondary → muted → inverse/light）
- **品牌色**: 主色 + 亮色变体 + 暗色变体 + dim 半透明 + glow 半透明
- **Priority 色**: must(红) + recommended(橙/黄) + fyi(绿) + 各自的 bg 半透明
- **边框色**: default(微妙) + strong + accent
- **间距**: 8pt grid — sp-1(4) 到 sp-12(48) 或更大
- **字体**: 主字体 + 辅助字体 + 等宽字体（含中文 fallback）
- **圆角**: sm(6) + md(10) + lg(14)
- **阴影**: card(subtle) + elevated(stronger) + glow(brand-color)

### 2. 排版层次（Typography Hierarchy）
- **H1/品牌标题**: 最大，letter-spacing 紧凑 (-0.02em)，font-weight 700-800
- **H2/Section 标题**: 次大，有颜色或图标辅助
- **Body/正文**: 舒适阅读，line-height 1.65+
- **Small/Meta**: 最小，颜色最淡，font-size 0.72-0.75em
- **大写文字**: 必须加 letter-spacing 0.08-0.12em
- **font-weight 对比**: 标题与正文至少差 2 级（如 700 vs 400）

### 3. 留白与呼吸感
- **Section 间距**: ≥ 48px（var(--sp-10) 或更大）
- **卡片内 padding**: ≥ 24px
- **元素间 gap**: ≥ 16px
- **页面容器 max-width**: 700-760px（除非特殊排版如报纸双栏）
- **line-height**: 正文 ≥ 1.65，摘要 ≥ 1.75

### 4. 视觉细节（让人多看一眼的设计）
每个模板至少具备以下 5 项中的 4 项：
- [ ] **渐变背景/装饰**: linear-gradient 或 radial-gradient（用于 header、卡片、分隔）
- [ ] **::before/::after 伪元素**: 装饰线条、发光效果、角标
- [ ] **多层阴影**: 至少定义 card 和 elevated 两级阴影
- [ ] **Border 精致化**: border-image gradient / 低透明度 border / 渐变分隔线
- [ ] **Hover 状态**: 带 transition 的颜色/背景/位移变化

### 5. Priority 视觉区分（🔴/🟡/🟢）
不能只靠颜色区分，必须有：
- **左侧指示条**: 不同颜色的 border-left 或独立色条元素
- **背景渐变**: must-read 卡片有微妙的红色/品牌色背景渐变
- **Must-read 特殊处理**: 更大的字重、更亮的文字颜色、可选 glow 效果

### 6. 代码质量
- **注释**: 每个大区块有 `/* --- Section Name --- */` 分隔
- **命名一致**: 用 BEM-like 或语义命名（.brief-headline, .section-header）
- **@page 规则**: 完整的 PDF 输出设置
- **@media print**: 单独的打印优化
- **@media (max-width: 640px)**: 移动端基础适配
- **CJK 字体 fallback**: PingFang SC, Noto Sans SC/Noto Serif SC, Microsoft YaHei

---

## 每种风格的设计要点

### 深色科技（deep-space, linear-elegant, premium, crypto-neon, neon-cyberpunk）
- 背景色近黑但不纯黑
- 发光效果(glow)要克制
- 代码/数据用等宽字体
- 可以用 radial-gradient 制造"光源感"

### 金融/商务（wsj-classic, ft-salmon, bloomberg-orange, goldman-sachs, economist-red）
- 衬线字体为主
- 配色要沉稳（desaturated）
- 留白要充足 — 像纸质出版物
- 分隔线是关键装饰元素
- Header 要有权威感

### 学术（arxiv-paper, nature-journal, ieee-technical, harvard-crimson, oxford-navy）
- 严谨的衬线排版
- 小标签标注（如 Fig. 1, Ref. [1]）
- 双栏布局可选
- 脚注风格的 meta 信息

### 咨询/企业（mckinsey-blue, bcg-green, bain-red, deloitte-green, strategy-plus）
- 极度克制，"无聊的高级"
- 大量留白
- 品牌色用于点睛而非铺底
- 数据/图表感

### 文化/艺术（ink-wash, ukiyo-e, art-deco, bauhaus, nordic-minimal）
- 风格必须鲜明 — 一眼就知道是什么主题
- 用 CSS 模拟材质感（纹理、纸张、木刻效果）
- 装饰性可以强一些，但不能影响可读性

### 品牌致敬（notion-clean, stripe-gradient, figma-playful, vercel-stark, spotify-green）
- 高度还原品牌的设计语言
- 间距、颜色、字体选择要"像"
- 不是 1:1 复制，是"如果 Notion 做了一个 newsletter"

### 行业垂直（healthcare-blue, legal-serif, realestate-luxury, education-warm, government-official）
- 行业色彩心理要对（医疗=蓝、法律=深色衬线、教育=暖色）
- 行业惯用设计模式（政府=严肃保守、地产=奢华大图）

### 社交媒体（instagram-gradient, twitter-card, newsletter-modern, wechat-article, reddit-thread）
- 模拟平台原生感
- 卡片/信息流布局
- 互动感（hover、点赞图标）

### 创意/实验（glassmorphism, retro-terminal, vintage-newspaper, neon-cyberpunk, swiss-grid）
- 风格极端但可读
- CSS 特效可以大胆（CRT扫描线、毛玻璃、霓虹发光）
- 一定要有趣

---

## Jinja2 模板结构标准

```jinja2
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsloom · {{ date_str }}</title>
    <style>
        /* 完整的 CSS — 所有样式都在这里 */
    </style>
</head>
<body>
    <!-- Header -->
    <!-- Executive Summary -->
    {% if executive_summary %}...{% endif %}
    <!-- Sections Loop -->
    {% for section in section_order %}
        {% if section in briefs and briefs[section] %}
            {% set meta = section_configs.get(section, {}) %}
            {% set section_briefs = briefs[section] %}
            <!-- Section with header + briefs -->
        {% endif %}
    {% endfor %}
    <!-- Footer -->
</body>
</html>
```

---

## 升级流程

1. 读取现有模板
2. 对照本文档逐项检查
3. 补齐缺失的 design tokens
4. 增强排版层次
5. 增加留白
6. 添加视觉细节（渐变、阴影、伪元素）
7. 强化 priority 区分
8. 优化代码质量和注释
9. 确保 ≥ 600 行
10. 风格特色要鲜明 — 不要变成"又一个深色模板"

**核心原则: 每个模板都要有自己的个性，但都要达到同样的品质标准。**
