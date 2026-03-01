"""Layer 4 v2: 报告生成器 - 支持分级阅读 + Executive Summary + 新模板

改进点：
1. Executive Summary 由 AI 生成（从 analyzer_v2 传入）
2. 分级标注：🔴必读 / 🟡推荐 / 🟢了解
3. 支持 priority 排序（🔴 在前）
4. 新 HTML 模板（magazine 风格）
5. Discord 精简版输出
"""

import json
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup


def _md_inline(text: str) -> Markup:
    """Convert inline markdown (**bold**, *italic*, `code`) to HTML"""
    if not text:
        return Markup("")
    s = str(text)
    # **bold**
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    # *italic*
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', s)
    # `code`
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    # • bullet → remove (already in <p>)
    s = re.sub(r'^[•·]\s*', '', s)
    return Markup(s)

try:
    # macOS: weasyprint 需要 pango/gobject，确保 homebrew 库路径可用
    import os
    import platform
    if platform.system() == "Darwin":
        _lib_path = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        if "/opt/homebrew/lib" not in _lib_path:
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = f"/opt/homebrew/lib:{_lib_path}"
    from weasyprint import HTML as WeasyHTML
    HAS_WEASYPRINT = True
except (ImportError, OSError):
    HAS_WEASYPRINT = False


PRIORITY_ORDER = {"🔴": 0, "🟡": 1, "🟢": 2}


class ReportGeneratorV2:
    """v2 报告生成器"""

    def __init__(self, config: dict, template_name: str = None):
        self.config = config
        self.formats = config.get("generate", {}).get("formats", ["markdown", "html"])
        self.template_name = template_name or config.get("generate", {}).get("template", "magazine")

        self.project_root = Path(__file__).parent.parent.parent
        self.template_dir = self.project_root / "templates" / self.template_name

        self.section_configs = self._load_sections_config()

        if self.template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            self.jinja_env.filters['md_inline'] = _md_inline
        else:
            self.jinja_env = None

    def _load_sections_config(self) -> Dict:
        sections_file = self.project_root / "config" / "sections.yaml"
        if sections_file.exists():
            with open(sections_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("sections", {})
        return {}

    @classmethod
    def list_templates(cls, config: dict = None) -> List[Dict]:
        """扫描 templates 目录，返回所有可用模板列表"""
        if config is None:
            config = {}
        project_root = Path(__file__).parent.parent.parent
        templates_dir = project_root / "templates"

        if not templates_dir.exists():
            return []

        templates = []
        for template_path in templates_dir.iterdir():
            if not template_path.is_dir():
                continue

            meta_file = template_path / "meta.yaml"
            template_info = {
                "name": template_path.name,
                "description": "No description available",
                "theme": "default",
                "features": []
            }

            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = yaml.safe_load(f)
                        if meta:
                            template_info.update({
                                "description": meta.get("description", template_info["description"]),
                                "theme": meta.get("theme", template_info["theme"]),
                                "features": meta.get("features", template_info["features"])
                            })
                except Exception as e:
                    print(f"⚠️ 读取 {meta_file} 失败: {e}")

            # 检查是否有必要的模板文件
            if (template_path / "report.html.j2").exists():
                templates.append(template_info)

        return sorted(templates, key=lambda x: x["name"])

    def preview_template(self, template_name: str) -> str:
        """生成模板预览 HTML（使用 mock 数据）"""
        project_root = Path(__file__).parent.parent.parent
        template_dir = project_root / "templates" / template_name

        if not template_dir.exists() or not (template_dir / "report.html.j2").exists():
            return f"<p>Template '{template_name}' not found or invalid.</p>"

        # Mock 数据用于预览
        mock_data = {
            "date_str": "2024-01-15",
            "generated_time": "2024-01-15 09:30",
            "total_items": 12,
            "executive_summary": "今日重点关注：人工智能领域新突破，加密货币市场波动，科技股集体上涨。重要政策发布影响多个行业。",
            "briefs": {
                "tech": [
                    {
                        "headline": "OpenAI 发布 GPT-4 Turbo 新版本",
                        "detail": "新版本在推理能力和多模态处理方面有显著提升，API 成本降低 50%",
                        "url": "#",
                        "source": "TechCrunch",
                        "priority": "🔴",
                        "tags": ["AI", "OpenAI", "GPT-4"]
                    },
                    {
                        "headline": "苹果公司将在下月发布 Vision Pro 2",
                        "detail": "据内部消息，新版本将支持更高分辨率显示和改进的手势识别",
                        "url": "#",
                        "source": "Bloomberg",
                        "priority": "🟡",
                        "tags": ["Apple", "VR", "Vision Pro"]
                    }
                ],
                "crypto": [
                    {
                        "headline": "比特币突破 45000 美元大关",
                        "detail": "受机构投资者入场影响，比特币价格创近期新高",
                        "url": "#",
                        "source": "CoinDesk",
                        "priority": "🟡",
                        "tags": ["BTC", "价格", "突破"]
                    }
                ]
            },
            "section_configs": {
                "tech": {
                    "title": "科技前沿",
                    "emoji": "💻",
                    "order": 1
                },
                "crypto": {
                    "title": "加密货币",
                    "emoji": "₿",
                    "order": 2
                }
            },
            "section_order": ["tech", "crypto"],
            "stats": {
                "sources_count": 25,
                "keywords_count": 156,
                "sentiment_score": 0.65
            }
        }

        try:
            jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            jinja_env.filters['md_inline'] = _md_inline

            template = jinja_env.get_template("report.html.j2")
            html = template.render(**mock_data)

            # 只返回前 5000 字符（预览用）
            if len(html) > 5000:
                html = html[:5000] + "...</div></body></html>"

            return html

        except Exception as e:
            return f"<p>Template preview error: {str(e)}</p>"

    def _get_section_order(self) -> List[str]:
        return sorted(
            self.section_configs.keys(),
            key=lambda k: self.section_configs[k].get("order", 999),
        )

    def generate(self, analyzed_data: Dict, date_str: str, output_dir: Path):
        """
        生成所有格式的报告

        analyzed_data 结构：
        {
            "briefs": {section: [brief, ...]},
            "executive_summary": "...",
            "cross_analysis": {...},
            "stats": {...}
        }
        """
        print(f"\n📝 生成 v2 报告...")
        output_dir.mkdir(parents=True, exist_ok=True)

        briefs = analyzed_data.get("briefs", analyzed_data)  # 兼容旧格式
        exec_summary = analyzed_data.get("executive_summary", "")
        cross_analysis = analyzed_data.get("cross_analysis", {})
        stats = analyzed_data.get("stats", {})

        # 按 priority 排序每个 section
        for section in briefs:
            if isinstance(briefs[section], list):
                briefs[section] = sorted(
                    briefs[section],
                    key=lambda x: PRIORITY_ORDER.get(x.get("priority", "🟢"), 2),
                )

        if "markdown" in self.formats:
            md_path = output_dir / "report.md"
            self._generate_markdown(briefs, exec_summary, cross_analysis, date_str, md_path)

        if "html" in self.formats:
            html_path = output_dir / "report.html"
            self._generate_html(briefs, exec_summary, stats, cross_analysis, date_str, html_path)

        # PDF 版（从 HTML 转换，适配 A4 打印）
        if "pdf" in self.formats or True:  # 默认总是生成 PDF
            pdf_path = output_dir / "report.pdf"
            html_path = output_dir / "report.html"
            if html_path.exists():
                self._generate_pdf(html_path, pdf_path, date_str)

        # Discord 精简版
        discord_path = output_dir / "discord.md"
        self._generate_discord(briefs, exec_summary, cross_analysis, date_str, discord_path)

        print(f"✅ 报告已生成: {output_dir}")

    def _generate_markdown(self, briefs: Dict, exec_summary: str, cross_analysis: Dict, date_str: str, output_path: Path):
        """生成 Markdown 报告"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        total = sum(len(v) for v in briefs.values() if isinstance(v, list))
        must_read = sum(
            1 for section_briefs in briefs.values()
            if isinstance(section_briefs, list)
            for b in section_briefs
            if b.get("priority") == "🔴"
        )

        lines = [
            f"# 📰 Newsloom 每日情报 - {date_str}",
            "",
            f"*{datetime.now().strftime('%H:%M')} 生成 | {total} 条精选 | {must_read} 条必读*",
            "",
            "---",
            "",
        ]

        # Executive Summary
        if exec_summary:
            lines.append("## 📌 今日核心")
            lines.append("")
            for line in exec_summary.strip().split("\n"):
                lines.append(line)
            lines.append("")
            lines.append("---")
            lines.append("")

        # Trends Radar
        if "__trends__" in briefs and briefs["__trends__"]:
            trends = briefs["__trends__"]
            # 只显示 rising 和 new 的，最多 10 条
            display_trends = [t for t in trends if '🔥' in t['trend'] or '🆕' in t['trend']][:10]

            if display_trends:
                lines.append("## 📊 趋势雷达")
                lines.append("")
                lines.append("| 关键词 | 趋势 | 今日 | 近7日均值 | 变化 |")
                lines.append("|--------|------|------|-----------|------|")

                for trend in display_trends:
                    keyword = trend.get('keyword', '')
                    trend_emoji = trend.get('trend', '')
                    today_count = trend.get('today_count', 0)
                    avg_count = trend.get('avg_count', 0)
                    change_pct = trend.get('change_pct', 0)
                    change_sign = "+" if change_pct >= 0 else ""

                    lines.append(f"| {keyword} | {trend_emoji} | {today_count} | {avg_count} | {change_sign}{change_pct}% |")

                lines.append("")
                lines.append("---")
                lines.append("")

        # TOC
        lines.append("## 目录")
        lines.append("")
        for section in self._get_section_order():
            if section in briefs and briefs[section]:
                meta = self.section_configs.get(section, {})
                emoji = meta.get("emoji", "")
                title = meta.get("title", section)
                count = len(briefs[section])
                must = sum(1 for b in briefs[section] if b.get("priority") == "🔴")
                must_tag = f" ({must}🔴)" if must else ""
                lines.append(f"- [{emoji} {title}](#{section}) - {count} 条{must_tag}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Sections
        for section in self._get_section_order():
            if section not in briefs or not briefs[section]:
                continue

            meta = self.section_configs.get(section, {})
            emoji = meta.get("emoji", "")
            title = meta.get("title", section)

            lines.append(f"## {emoji} {title}")
            lines.append("")

            for i, brief in enumerate(briefs[section], 1):
                headline = brief.get("headline", "No headline")
                detail = brief.get("detail", "")
                so_what = brief.get("so_what", "")
                url = brief.get("url", "#")
                source = brief.get("source", "")
                priority = brief.get("priority", "🟢")
                tags = brief.get("tags", [])

                tags_str = " ".join(tags) if tags else ""

                lines.append(f"### {priority} {i}. [{headline}]({url})")
                lines.append("")
                if source:
                    lines.append(f"**{source}** {tags_str}")
                    lines.append("")
                if detail:
                    lines.append(detail)
                    lines.append("")
                if so_what:
                    lines.append(f"> 💡 **行动建议：** {so_what}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        # 跨板块关联
        if cross_analysis:
            connections = cross_analysis.get("cross_connections", [])
            main_narrative = cross_analysis.get("main_narrative", "")
            risk_opp = cross_analysis.get("risk_opportunity", "")

            if connections or main_narrative or risk_opp:
                lines.append("## 🔗 跨板块关联")
                lines.append("")
                if main_narrative:
                    lines.append(f"**今日主叙事：** {main_narrative}")
                    lines.append("")
                for conn in connections:
                    sections_str = " + ".join(conn.get("sections", []))
                    insight = conn.get("insight", "")
                    implication = conn.get("implication", "")
                    lines.append(f"🔗 **[{sections_str}]** {insight}")
                    if implication:
                        lines.append(f"   → {implication}")
                    lines.append("")
                if risk_opp:
                    lines.append(f"⚠️ **关注点：** {risk_opp}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        # Footer
        lines.append("")
        lines.append("*Generated by Newsloom v2 📰*")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"📄 Markdown: {output_path}")

    def _generate_html(self, briefs: Dict, exec_summary: str, stats: Dict, cross_analysis: Dict, date_str: str, output_path: Path):
        """生成 HTML 报告（优先用模板）"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        total = sum(len(v) for v in briefs.values() if isinstance(v, list))

        # 缓存渲染数据，供 PDF 生成复用
        self._last_render_data = {
            "date_str": date_str,
            "generated_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_items": total,
            "executive_summary": exec_summary,
            "cross_analysis": cross_analysis,
            "briefs": briefs,
            "section_configs": self.section_configs,
            "section_order": self._get_section_order(),
            "stats": stats,
        }

        if self.jinja_env:
            try:
                template = self.jinja_env.get_template("report.html.j2")
                html = template.render(**self._last_render_data)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"🌐 HTML (template {self.template_name}): {output_path}")
                return
            except Exception as e:
                print(f"⚠️ Template failed: {e}, fallback")

        # Fallback
        self._generate_html_fallback(briefs, exec_summary, date_str, output_path)

    def _generate_html_fallback(self, briefs: Dict, exec_summary: str, date_str: str, output_path: Path):
        """简化的 Fallback HTML（如果模板加载失败）"""
        total = sum(len(v) for v in briefs.values() if isinstance(v, list))
        generated_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        sections_html = ""
        for section in self._get_section_order():
            if section not in briefs or not briefs[section]:
                continue
            meta = self.section_configs.get(section, {})
            emoji = meta.get("emoji", "")
            title = meta.get("title", section)

            sections_html += f'<section class="section"><div class="section-header"><span class="section-emoji">{emoji}</span><h2 class="section-title">{title}</h2><span class="section-count">{len(briefs[section])}</span></div>'

            for brief in briefs[section]:
                priority = brief.get("priority", "🟢")
                priority_class = 'must-read' if priority == '🔴' else ('recommended' if priority == '🟡' else 'fyi')
                headline = brief.get("headline", "")
                detail = brief.get("detail", "")
                url = brief.get("url", "#")
                source = brief.get("source", "")
                tags = brief.get("tags", [])
                tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)

                sections_html += f'''<div class="brief"><div class="brief-priority {priority_class}"></div><div class="brief-body"><div class="brief-headline"><a href="{url}" target="_blank">{headline}</a></div><div class="brief-meta">{f'<span class="source-badge">{source}</span>' if source else ''}{tags_html}</div>{f'<div class="brief-detail">{detail}</div>' if detail else ''}</div></div>'''

            sections_html += "</section>"

        exec_html = ""
        if exec_summary:
            lines = exec_summary.strip().split("\n")
            exec_html = '<div class="exec-summary"><h2>⚡ Executive Summary</h2>'
            for line in lines:
                if line.strip():
                    exec_html += f"<p>{line}</p>"
            exec_html += "</div>"

        html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Newsloom Daily Brief · {date_str}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",sans-serif;background:#fafafa;color:#1a1a2e;font-size:15px;line-height:1.6}}
.container{{max-width:700px;margin:0 auto;padding:32px 20px;background:#ffffff}}
.header{{padding:20px 0 24px;border-bottom:2px solid #e2e8f0;margin-bottom:28px}}
.header-title{{font-size:1.3em;font-weight:700;margin-bottom:6px}}
.header-meta{{font-size:.85em;color:#64748b}}
.exec-summary{{background:#fffbeb;border-left:4px solid #f59e0b;border-radius:6px;padding:20px 24px;margin-bottom:32px}}
.exec-summary h2{{font-size:1.05em;font-weight:700;color:#d97706;margin-bottom:12px;text-transform:uppercase}}
.exec-summary p{{color:#451a03;font-size:.95em;margin-bottom:6px}}
.section{{margin-bottom:36px}}
.section-header{{display:flex;align-items:center;gap:8px;padding-bottom:10px;margin-bottom:16px;border-bottom:1px solid #e2e8f0}}
.section-emoji{{font-size:1.3em}}
.section-title{{font-size:1.25em;font-weight:700}}
.section-count{{margin-left:auto;font-size:.75em;color:#94a3b8;background:#f1f5f9;padding:2px 8px;border-radius:4px}}
.brief{{display:flex;margin-bottom:16px}}
.brief-priority{{width:3px;flex-shrink:0;border-radius:2px 0 0 2px;margin-right:14px}}
.brief-priority.must-read{{background:#ef4444}}
.brief-priority.recommended{{background:#f59e0b}}
.brief-priority.fyi{{background:#22c55e}}
.brief-body{{flex:1}}
.brief-headline{{font-size:1em;font-weight:600;margin-bottom:4px}}
.brief-headline a{{color:#1a1a2e;text-decoration:none}}
.brief-headline a:hover{{color:#6366f1}}
.brief-meta{{display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap}}
.source-badge{{font-size:.78em;color:#64748b;background:#f1f5f9;padding:2px 8px;border-radius:3px}}
.tag{{font-size:.72em;color:#6366f1;background:#eef2ff;padding:2px 6px;border-radius:3px}}
.brief-detail{{color:#64748b;font-size:.92em}}
footer{{text-align:center;padding:24px 0;color:#94a3b8;border-top:1px solid #e2e8f0;margin-top:32px;font-size:.8em}}
</style></head>
<body><div class="container">
<header class="header"><div class="header-title">📰 Newsloom Daily Brief · {date_str}</div><div class="header-meta">{generated_time} · {total} items</div></header>
{exec_html}
{sections_html}
<footer>Generated by Newsloom · {date_str}</footer>
</div></body></html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"🌐 HTML (fallback): {output_path}")

    def _generate_pdf(self, html_path: Path, pdf_path: Path, date_str: str):
        """从统一模板生成 PDF（模板已内置 @page 样式）"""
        if not HAS_WEASYPRINT:
            print("⚠️ weasyprint 未安装，跳过 PDF 生成。安装: pip install weasyprint")
            return

        try:
            # 直接使用统一模板的 HTML（它已经包含了 @page 和 print 样式）
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            WeasyHTML(string=html_content, base_url=str(html_path.parent)).write_pdf(str(pdf_path))

            file_size = pdf_path.stat().st_size / 1024
            print(f"📕 PDF: {pdf_path} ({file_size:.0f} KB)")

        except Exception as e:
            print(f"⚠️ PDF 生成失败: {e}")


    def _generate_discord(self, briefs: Dict, exec_summary: str, cross_analysis: Dict, date_str: str, output_path: Path):
        """生成 Discord 友好的精简版（含 so_what + 跨板块关联）"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [f"**📰 Newsloom 每日情报 — {date_str}**", ""]

        # Executive Summary
        if exec_summary:
            lines.append("**📌 今日核心**")
            for line in exec_summary.strip().split("\n"):
                if line.strip():
                    lines.append(line)
            lines.append("")

        # 只展示 🔴必读 和 🟡推荐，带 so_what
        for section in self._get_section_order():
            if section not in briefs or not briefs[section]:
                continue

            meta = self.section_configs.get(section, {})
            emoji = meta.get("emoji", "")
            title = meta.get("title", section)

            important = [b for b in briefs[section] if b.get("priority") in ("🔴", "🟡")]
            selected = important[:5]

            # 兜底：若本次精排/分级失败导致全是 🟢，也要保证 Discord 版不是空报告
            if not selected:
                selected = (briefs[section] or [])[:3]

            if not selected:
                continue

            lines.append(f"**{emoji} {title}**")
            for b in selected:  # 每个 section 最多 5 条（兜底时最多 3 条）
                priority = b.get("priority") or "🟢"
                headline = b.get("headline", "")
                url = b.get("url", "")
                so_what = b.get("so_what", "")
                line = f"{priority} [{headline}](<{url}>)"
                if so_what:
                    line += f"\n  └ 💡 {so_what}"
                lines.append(line)
            lines.append("")

        # 跨板块关联（精简版）
        if cross_analysis:
            connections = cross_analysis.get("cross_connections", [])
            risk_opp = cross_analysis.get("risk_opportunity", "")
            main_narrative = cross_analysis.get("main_narrative", "")

            if connections or risk_opp or main_narrative:
                lines.append("**🔗 跨板块关联**")
                if main_narrative:
                    lines.append(f"今日主线：{main_narrative}")
                for conn in connections[:3]:
                    insight = conn.get("insight", "")
                    implication = conn.get("implication", "")
                    if insight:
                        lines.append(f"🔗 {insight}")
                    if implication:
                        lines.append(f"  → {implication}")
                if risk_opp:
                    lines.append(f"⚠️ {risk_opp}")
                lines.append("")

        lines.append("*完整报告见 HTML 版*")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"💬 Discord 版: {output_path}")
