"""Layer 4: Report generation (Markdown, HTML, Cards, RSS) - v0.2.0 增强版"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader, Template


class ReportGenerator:
    """Multi-format report generator with pluggable template system (v0.2.0)"""

    def __init__(self, config: dict):
        self.config = config
        self.formats = config.get('generate', {}).get('formats', ['markdown', 'html'])
        self.generate_rss = config.get('generate', {}).get('generate_rss', False)

        # Template configuration
        self.template_name = config.get('generate', {}).get('template', 'dark-pro')
        self.project_root = Path(__file__).parent.parent.parent
        self.template_dir = self.project_root / 'templates' / self.template_name

        # Load section configurations
        self.section_configs = self._load_sections_config()

        # Initialize Jinja2 environment if templates exist
        if self.template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            self.jinja_env = None
            print(f"⚠️  Template directory not found: {self.template_dir}, using fallback")

    def _load_sections_config(self) -> Dict:
        """Load section metadata from sections.yaml"""
        sections_file = self.project_root / 'config' / 'sections.yaml'
        if sections_file.exists():
            with open(sections_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('sections', {})
        else:
            return {
                'ai': {'title': 'AI & 科技', 'emoji': '🤖', 'order': 1, 'color': '#6366f1'},
                'tech': {'title': '科技动态', 'emoji': '💻', 'order': 2, 'color': '#06b6d4'},
                'papers': {'title': '论文速递', 'emoji': '📄', 'order': 3, 'color': '#8b5cf6'},
                'github': {'title': 'GitHub 趋势', 'emoji': '⭐', 'order': 4, 'color': '#f59e0b'},
                'community': {'title': '社区热议', 'emoji': '🔥', 'order': 5, 'color': '#ef4444'},
                'finance': {'title': '金融市场', 'emoji': '📊', 'order': 6, 'color': '#10b981'},
                'crypto': {'title': 'Crypto 舆情', 'emoji': '💎', 'order': 7, 'color': '#f97316'},
            }

    def _get_section_order(self) -> List[str]:
        """Get sections sorted by order field"""
        return sorted(
            self.section_configs.keys(),
            key=lambda k: self.section_configs[k].get('order', 999)
        )

    def generate(self, items, date_str: str, output_dir: Path):
        """
        生成所有配置的报告格式

        Args:
            items: Item 列表 或 AI briefs 字典
            date_str: 日期字符串
            output_dir: 输出目录
        """
        print(f"\n📝 生成报告中...")

        # 判断是 Items 还是 AI briefs
        if isinstance(items, dict):
            # AI briefs 格式: {section: [briefs], __executive_summary__: str}
            if 'markdown' in self.formats:
                md_path = output_dir / 'report.md'
                self.generate_markdown_from_briefs(items, date_str, md_path)

            if 'html' in self.formats:
                html_path = output_dir / 'report.html'
                self.generate_html_from_briefs(items, date_str, html_path)
        else:
            # 原始 Items
            if 'markdown' in self.formats:
                md_path = output_dir / 'report.md'
                self.generate_markdown(items, date_str, md_path)

            if 'html' in self.formats:
                html_path = output_dir / 'report.html'
                self.generate_html(items, date_str, html_path)

        print(f"✅ 报告已生成: {output_dir}")

    def _sort_briefs_by_importance(self, briefs: List[Dict]) -> List[Dict]:
        """按 importance 降序排序 briefs"""
        return sorted(briefs, key=lambda x: x.get('importance', 3), reverse=True)

    def _prepare_briefs_for_template(self, raw_briefs: Dict) -> Dict:
        """
        准备模板数据：提取 executive_summary，排序 briefs，过滤空 section

        Returns:
            dict with keys: briefs, executive_summary, stats
        """
        executive_summary = raw_briefs.get('__executive_summary__', '')

        # 过滤掉特殊 key 和空 section
        content_briefs = {}
        for k, v in raw_briefs.items():
            if k.startswith('__') or not v or not isinstance(v, list):
                continue
            # 按 importance 排序
            content_briefs[k] = self._sort_briefs_by_importance(v)

        # 统计信息
        stats = {}
        for section, items in content_briefs.items():
            meta = self.section_configs.get(section, {})
            stats[section] = {
                'count': len(items),
                'emoji': meta.get('emoji', '•'),
                'title': meta.get('title', section),
                'color': meta.get('color', '#666'),
            }

        return {
            'briefs': content_briefs,
            'executive_summary': executive_summary,
            'stats': stats,
        }

    def generate_markdown_from_briefs(self, briefs: Dict, date_str: str, output_path: Path):
        """从 AI briefs 生成 Markdown (使用 Jinja2 模板)"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        prepared = self._prepare_briefs_for_template(briefs)
        non_empty_briefs = prepared['briefs']

        if not non_empty_briefs:
            print("⚠️ No content to generate (all sections are empty)")
            self._generate_empty_markdown(date_str, output_path)
            return

        # Use template if available
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template('report.md.j2')

                total_items = sum(len(items) for items in non_empty_briefs.values())
                markdown = template.render(
                    date_str=date_str,
                    generated_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    total_items=total_items,
                    briefs=non_empty_briefs,
                    executive_summary=prepared['executive_summary'],
                    stats=prepared['stats'],
                    section_configs=self.section_configs,
                    section_order=self._get_section_order()
                )

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)

                print(f"📄 Markdown 已生成 (使用模板 {self.template_name}): {output_path}")
                return
            except Exception as e:
                print(f"⚠️  Template rendering failed: {e}, falling back to default")

        # Fallback to hardcoded template
        self._generate_markdown_fallback(non_empty_briefs, date_str, output_path,
                                          prepared['executive_summary'])

    def generate_html_from_briefs(self, briefs: Dict, date_str: str, output_path: Path):
        """从 AI briefs 生成 HTML (使用 Jinja2 模板)"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        prepared = self._prepare_briefs_for_template(briefs)
        non_empty_briefs = prepared['briefs']

        if not non_empty_briefs:
            print("⚠️ No content to generate (all sections are empty)")
            self._generate_empty_html(date_str, output_path)
            return

        # Use template if available
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template('report.html.j2')

                total_items = sum(len(items) for items in non_empty_briefs.values())

                # 直接传递 briefs（已包含 importance/tags/insight）
                formatted_briefs = {}
                for section, section_briefs in non_empty_briefs.items():
                    formatted_briefs[section] = []
                    for brief in section_briefs:
                        entry = {
                            'title': brief.get('headline', 'No title'),
                            'url': brief.get('url', '#'),
                            'source': brief.get('source', 'unknown'),
                            'text': brief.get('detail', ''),
                            'importance': brief.get('importance', 3),
                            'category_tags': brief.get('category_tags', []),
                            'insight': brief.get('insight', ''),
                        }
                        # papers section 额外字段
                        if section == 'papers':
                            entry['authors'] = brief.get('authors', '')
                            entry['arxiv_id'] = brief.get('arxiv_id', '')
                            entry['research_tags'] = brief.get('research_tags', [])
                            entry['practicality_score'] = brief.get('practicality_score', 3)
                        formatted_briefs[section].append(entry)

                html = template.render(
                    date_str=date_str,
                    total_items=total_items,
                    briefs=formatted_briefs,
                    executive_summary=prepared['executive_summary'],
                    stats=prepared['stats'],
                    section_configs=self.section_configs,
                    section_order=self._get_section_order()
                )

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html)

                print(f"🌐 HTML 已生成 (使用模板 {self.template_name}): {output_path}")
                return
            except Exception as e:
                print(f"⚠️  Template rendering failed: {e}, falling back to default")

        # Fallback
        self._generate_html_fallback(non_empty_briefs, date_str, output_path)

    def _generate_empty_markdown(self, date_str: str, output_path: Path):
        """Generate empty markdown report"""
        lines = [
            f"# Daily Report - {date_str}",
            "",
            f"*Generated by Newsloom AI at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            "",
            "## No Content",
            "",
            "No items to report today.",
            "",
            "---",
            "",
            "*Generated by Newsloom 📰*"
        ]
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def _generate_empty_html(self, date_str: str, output_path: Path):
        """Generate empty HTML report"""
        simple_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Report - {date_str}</title>
</head>
<body style="font-family: sans-serif; padding: 40px; text-align: center;">
    <h1>📰 Daily Report</h1>
    <p>{date_str}</p>
    <p>No items to report today.</p>
</body>
</html>"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(simple_html)

    def _generate_markdown_fallback(self, briefs: Dict, date_str: str, output_path: Path,
                                     executive_summary: str = ""):
        """Fallback markdown generation without templates"""
        lines = [
            f"# Daily Report - {date_str}",
            "",
            f"*Generated by Newsloom AI at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            ""
        ]

        # Executive Summary
        if executive_summary:
            lines.append("## 📌 Executive Summary")
            lines.append("")
            lines.append(executive_summary)
            lines.append("")
            lines.append("---")
            lines.append("")
        else:
            lines.extend(self._build_executive_summary(briefs))

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        for section in self._get_section_order():
            if section in briefs:
                section_meta = self.section_configs.get(section, {})
                emoji = section_meta.get('emoji', '')
                title = section_meta.get('title', section.replace('_', ' ').title())
                lines.append(f"- [{emoji} {title}](#{section})")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Content sections
        for section in self._get_section_order():
            if section not in briefs:
                continue

            section_briefs = briefs[section]
            section_meta = self.section_configs.get(section, {})
            emoji = section_meta.get('emoji', '')
            title = section_meta.get('title', section.replace('_', ' ').title())

            lines.append(f"## {emoji} {title}")
            lines.append("")
            lines.append(f"*{len(section_briefs)} items*")
            lines.append("")

            for i, brief in enumerate(section_briefs, 1):
                headline = brief.get('headline', 'No headline')
                detail = brief.get('detail', '')
                url = brief.get('url', '#')
                source = brief.get('source', 'unknown')
                importance = brief.get('importance', 3)
                tags = brief.get('category_tags', [])
                insight = brief.get('insight', '')

                # 重要性 emoji
                stars = '⭐' * min(importance, 5)

                lines.append(f"### {i}. [{headline}]({url})")
                lines.append("")

                # papers section 显示额外学术信息
                if section == 'papers':
                    authors = brief.get('authors', '')
                    arxiv_id = brief.get('arxiv_id', '')
                    research_tags = brief.get('research_tags', [])
                    practicality = brief.get('practicality_score', 3)

                    meta_parts = [f"**来源:** {source}"]
                    if arxiv_id:
                        meta_parts.append(f"**arXiv:** `{arxiv_id}`")
                    meta_parts.append(stars)
                    lines.append(" | ".join(meta_parts))

                    if authors:
                        lines.append(f"**作者:** {authors}")
                    if research_tags:
                        lines.append(f"**研究方向:** {' '.join(f'`{t}`' for t in research_tags)}")
                    lines.append(f"**实用性:** {'🔧' * min(practicality, 5)} ({practicality}/5)")
                else:
                    lines.append(f"**来源:** {source} | {stars}")

                if tags:
                    lines.append(f"**标签:** {' '.join(f'`{t}`' for t in tags)}")
                lines.append("")
                if detail:
                    lines.append(f"{detail}")
                    lines.append("")
                if insight:
                    lines.append(f"*{insight}*")
                    lines.append("")
                lines.append("---")
                lines.append("")

        # Footer
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Generated by Newsloom 📰*")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"📄 Markdown 已生成 (fallback): {output_path}")

    def _build_executive_summary(self, briefs: Dict) -> List[str]:
        """从每个 section 的 top brief 生成 Executive Summary（简单版）"""
        lines = []
        lines.append("## 📌 Executive Summary")
        lines.append("")
        total = sum(len(v) for v in briefs.values())
        lines.append(f"> 今日共 **{total}** 条精选，覆盖 {len(briefs)} 个板块。以下是各领域最值得关注的动态：")
        lines.append(">")
        for section in self._get_section_order():
            if section not in briefs or not briefs[section]:
                continue
            section_meta = self.section_configs.get(section, {})
            emoji = section_meta.get('emoji', '•')
            top = briefs[section][0]
            headline = top.get('headline', '')
            if headline:
                lines.append(f"> {emoji} **{headline}**")
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _generate_html_fallback(self, briefs: Dict, date_str: str, output_path: Path):
        """Fallback HTML generation (simple version)"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Daily Report - {date_str}</title>
    <style>
        body {{ font-family: sans-serif; padding: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        header {{ background: #fff; padding: 30px; border-radius: 8px; margin-bottom: 30px; }}
        .section {{ margin-bottom: 40px; }}
        .card {{ background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <header><h1>📊 Daily Report</h1><p>{date_str}</p></header>
"""

        for section in self._get_section_order():
            if section not in briefs:
                continue
            section_meta = self.section_configs.get(section, {})
            title = section_meta.get('title', section)
            emoji = section_meta.get('emoji', '')

            html += f'<div class="section"><h2>{emoji} {title}</h2>'
            for brief in briefs[section]:
                headline = brief.get('headline', 'No title')
                url = brief.get('url', '#')
                detail = brief.get('detail', '')
                html += f'<div class="card"><h3><a href="{url}">{headline}</a></h3><p>{detail}</p></div>'
            html += '</div>'

        html += """
    </div>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"🌐 HTML 已生成 (fallback): {output_path}")

    # ============================================================
    # 以下是原始 Item 格式的生成方法（向后兼容）
    # ============================================================

    def generate_markdown(self, items: List, date_str: str, output_path: Path):
        """Generate Markdown report from raw Items (backward compatible)"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        by_channel = {}
        for item in items:
            channel = getattr(item, 'channel', 'general')
            by_channel.setdefault(channel, []).append(item)

        for channel in by_channel:
            by_channel[channel].sort(key=lambda x: getattr(x, 'score', 0), reverse=True)

        lines = [
            f"# Daily Report - {date_str}",
            "",
            f"*Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            ""
        ]

        for channel in sorted(by_channel.keys()):
            items_list = by_channel[channel]
            channel_name = channel.replace('_', ' ').title()

            lines.append(f"## {channel_name}")
            lines.append("")

            for i, item in enumerate(items_list, 1):
                title = getattr(item, 'title', 'No title')
                url = getattr(item, 'url', '#')
                meta = getattr(item, 'metadata', {}) or {}
                source = meta.get('feed_name') or meta.get('feed_title') or getattr(item, 'source', 'unknown')

                lines.append(f"### {i}. [{title}]({url})")
                lines.append(f"**Source:** {source}")
                lines.append("")

            lines.append("---")
            lines.append("")

        lines.append("*Generated by Newsloom 📰*")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"📄 Generated Markdown: {output_path}")

    def generate_html(self, items: List, date_str: str, output_path: Path):
        """Generate HTML report from raw Items (backward compatible)"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        by_channel = {}
        for item in items:
            channel = getattr(item, 'channel', 'general')
            by_channel.setdefault(channel, []).append(item)

        for channel in by_channel:
            by_channel[channel].sort(key=lambda x: getattr(x, 'score', 0), reverse=True)

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Report - {date_str}</title></head>
<body style="font-family:sans-serif;padding:40px;background:#f5f5f5;">
<div style="max-width:1000px;margin:0 auto;">
<h1>📊 Daily Report - {date_str}</h1>"""

        for channel in sorted(by_channel.keys()):
            html += f'<h2>{channel}</h2>'
            for item in by_channel[channel]:
                title = getattr(item, 'title', '')
                url = getattr(item, 'url', '#')
                html += f'<div style="background:#fff;padding:16px;margin:8px 0;border-radius:8px;"><a href="{url}">{title}</a></div>'

        html += '</div></body></html>'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"🌐 Generated HTML: {output_path}")
