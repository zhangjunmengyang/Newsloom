"""Layer 4 v2: 报告生成器 — 支持分级阅读 + Executive Summary + 新模板

改进点：
1. Executive Summary 由 AI 生成（从 analyzer_v2 传入）
2. 分级标注：🔴必读 / 🟡推荐 / 🟢了解
3. 支持 priority 排序（🔴 在前）
4. 新 HTML 模板（magazine 风格）
5. Discord 精简版输出
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader

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

    def __init__(self, config: dict):
        self.config = config
        self.formats = config.get("generate", {}).get("formats", ["markdown", "html"])
        self.template_name = config.get("generate", {}).get("template", "magazine")

        self.project_root = Path(__file__).parent.parent.parent
        self.template_dir = self.project_root / "templates" / self.template_name

        self.section_configs = self._load_sections_config()

        if self.template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self.jinja_env = None

    def _load_sections_config(self) -> Dict:
        sections_file = self.project_root / "config" / "sections.yaml"
        if sections_file.exists():
            with open(sections_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("sections", {})
        return {}

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
            "stats": {...}
        }
        """
        print(f"\n📝 生成 v2 报告...")
        output_dir.mkdir(parents=True, exist_ok=True)

        briefs = analyzed_data.get("briefs", analyzed_data)  # 兼容旧格式
        exec_summary = analyzed_data.get("executive_summary", "")
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
            self._generate_markdown(briefs, exec_summary, date_str, md_path)

        if "html" in self.formats:
            html_path = output_dir / "report.html"
            self._generate_html(briefs, exec_summary, stats, date_str, html_path)

        # PDF 版（从 HTML 转换，适配 A4 打印）
        if "pdf" in self.formats or True:  # 默认总是生成 PDF
            pdf_path = output_dir / "report.pdf"
            html_path = output_dir / "report.html"
            if html_path.exists():
                self._generate_pdf(html_path, pdf_path, date_str)

        # Discord 精简版
        discord_path = output_dir / "discord.md"
        self._generate_discord(briefs, exec_summary, date_str, discord_path)

        print(f"✅ 报告已生成: {output_dir}")

    def _generate_markdown(self, briefs: Dict, exec_summary: str, date_str: str, output_path: Path):
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
            f"# 📰 Newsloom 每日情报 — {date_str}",
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
                lines.append(f"- [{emoji} {title}](#{section}) — {count} 条{must_tag}")
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
                lines.append("---")
                lines.append("")

        # Footer
        lines.append("")
        lines.append("*Generated by Newsloom v2 📰*")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"📄 Markdown: {output_path}")

    def _generate_html(self, briefs: Dict, exec_summary: str, stats: Dict, date_str: str, output_path: Path):
        """生成 HTML 报告（优先用模板）"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        total = sum(len(v) for v in briefs.values() if isinstance(v, list))

        if self.jinja_env:
            try:
                template = self.jinja_env.get_template("report.html.j2")
                html = template.render(
                    date_str=date_str,
                    generated_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    total_items=total,
                    executive_summary=exec_summary,
                    briefs=briefs,
                    section_configs=self.section_configs,
                    section_order=self._get_section_order(),
                    stats=stats,
                )
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"🌐 HTML (template {self.template_name}): {output_path}")
                return
            except Exception as e:
                print(f"⚠️ Template failed: {e}, fallback")

        # Fallback
        self._generate_html_fallback(briefs, exec_summary, date_str, output_path)

    def _generate_html_fallback(self, briefs: Dict, exec_summary: str, date_str: str, output_path: Path):
        """Fallback HTML"""
        total = sum(len(v) for v in briefs.values() if isinstance(v, list))
        # 生成内联 HTML
        sections_html = ""
        for section in self._get_section_order():
            if section not in briefs or not briefs[section]:
                continue
            meta = self.section_configs.get(section, {})
            emoji = meta.get("emoji", "")
            title = meta.get("title", section)
            color = meta.get("color", "#6366f1")

            sections_html += f'<section id="section-{section}" class="section">'
            sections_html += f'<div class="section-header" style="border-color:{color}"><h2>{emoji} {title}</h2><span class="count">{len(briefs[section])}</span></div>'

            for brief in briefs[section]:
                priority = brief.get("priority", "🟢")
                headline = brief.get("headline", "")
                detail = brief.get("detail", "")
                url = brief.get("url", "#")
                source = brief.get("source", "")
                tags = brief.get("tags", [])
                tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)

                sections_html += f'''
                <div class="card" style="border-left-color:{color}">
                    <div class="card-priority">{priority}</div>
                    <div class="card-body">
                        <h3><a href="{url}" target="_blank">{headline}</a></h3>
                        <div class="card-meta"><span class="source">{source}</span>{tags_html}</div>
                        <p>{detail}</p>
                    </div>
                </div>'''

            sections_html += "</section>"

        exec_html = ""
        if exec_summary:
            lines = exec_summary.strip().split("\n")
            exec_html = '<div class="executive-summary"><h2>📌 今日核心</h2>'
            for line in lines:
                if line.strip():
                    exec_html += f"<p>{line}</p>"
            exec_html += "</div>"

        html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Newsloom — {date_str}</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--text:#e6edf3;--muted:#8b949e;--border:#30363d;--link:#58a6ff}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
.container{{max-width:900px;margin:0 auto;padding:24px}}
header{{padding:40px 0;border-bottom:1px solid var(--border);margin-bottom:32px}}
h1{{font-size:2em;margin-bottom:8px}}
.subtitle{{color:var(--muted);font-size:.9em}}
.executive-summary{{background:var(--card);border-radius:12px;padding:24px;margin-bottom:32px;border-left:4px solid #f59e0b}}
.executive-summary h2{{margin-bottom:12px;font-size:1.2em}}
.executive-summary p{{margin-bottom:8px;color:var(--text)}}
.section{{margin-bottom:40px}}
.section-header{{display:flex;align-items:center;gap:12px;padding-bottom:12px;border-bottom:3px solid;margin-bottom:20px}}
.section-header h2{{font-size:1.5em}}
.count{{background:var(--card);color:var(--muted);padding:2px 10px;border-radius:10px;font-size:.85em}}
.card{{display:flex;background:var(--card);border-radius:10px;margin-bottom:16px;border-left:4px solid;overflow:hidden;transition:transform .2s}}
.card:hover{{transform:translateX(4px)}}
.card-priority{{display:flex;align-items:center;padding:0 16px;font-size:1.3em;min-width:56px;justify-content:center}}
.card-body{{padding:16px;flex:1}}
.card-body h3{{font-size:1.1em;margin-bottom:6px}}
.card-body h3 a{{color:var(--text);text-decoration:none}}
.card-body h3 a:hover{{color:var(--link)}}
.card-meta{{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}}
.source{{color:var(--muted);font-size:.85em}}
.tag{{background:var(--bg);color:var(--link);padding:2px 8px;border-radius:4px;font-size:.8em}}
.card-body p{{color:var(--muted);font-size:.95em;line-height:1.5}}
footer{{text-align:center;padding:40px 0;color:var(--muted);border-top:1px solid var(--border);margin-top:40px}}
</style></head>
<body><div class="container">
<header><h1>📰 Newsloom 每日情报</h1><p class="subtitle">{date_str} | {total} 条精选 | Powered by Claude AI</p></header>
{exec_html}
{sections_html}
<footer>Generated by Newsloom v2 📰</footer>
</div></body></html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"🌐 HTML (fallback): {output_path}")

    def _generate_pdf(self, html_path: Path, pdf_path: Path, date_str: str):
        """从 HTML 生成图文并茂的 A4 PDF"""
        if not HAS_WEASYPRINT:
            print("⚠️ weasyprint 未安装，跳过 PDF 生成。安装: pip install weasyprint")
            return

        try:
            # 读取 HTML 并注入打印优化 CSS
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            print_css = """
<style>
@page {
    size: A4;
    margin: 2cm 1.5cm;
    @bottom-center {
        content: "Newsloom """ + date_str + """ — Page " counter(page) " / " counter(pages);
        font-size: 9px;
        color: #8b949e;
    }
}

/* 覆盖暗色背景为打印友好色 */
body {
    background: #0d1117 !important;
    color: #e6edf3 !important;
    font-size: 11pt !important;
    line-height: 1.6 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
}

/* 每个 section 前分页 */
.section {
    page-break-before: auto;
    page-break-inside: avoid;
}

.section:nth-child(n+2) {
    page-break-before: always;
}

/* 卡片不跨页 */
.card {
    page-break-inside: avoid;
    margin-bottom: 12px !important;
}

/* Executive summary 不跨页 */
.executive-summary {
    page-break-inside: avoid;
    page-break-after: always;
}

/* 标题页样式 */
header {
    page-break-after: avoid;
    padding: 60px 0 30px !important;
    text-align: center !important;
}

header h1 {
    font-size: 2.2em !important;
    margin-bottom: 16px !important;
}

/* 链接显示 URL */
a[href] {
    color: #58a6ff !important;
    text-decoration: none !important;
}

/* 隐藏页脚 */
footer {
    page-break-before: always;
    text-align: center;
    padding-top: 40px;
}

/* 确保暗色背景在 PDF 中渲染 */
.container {
    max-width: 100% !important;
    padding: 0 !important;
}
</style>
"""
            # 在 </head> 前注入打印 CSS
            if "</head>" in html_content:
                html_content = html_content.replace("</head>", print_css + "</head>")
            else:
                html_content = print_css + html_content

            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            WeasyHTML(string=html_content, base_url=str(html_path.parent)).write_pdf(str(pdf_path))
            
            file_size = pdf_path.stat().st_size / 1024
            print(f"📕 PDF: {pdf_path} ({file_size:.0f} KB)")

        except Exception as e:
            print(f"⚠️ PDF 生成失败: {e}")

    def _generate_discord(self, briefs: Dict, exec_summary: str, date_str: str, output_path: Path):
        """生成 Discord 友好的精简版"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [f"**📰 Newsloom 每日情报 — {date_str}**", ""]

        # Executive Summary
        if exec_summary:
            lines.append("**📌 今日核心**")
            for line in exec_summary.strip().split("\n"):
                if line.strip():
                    lines.append(line)
            lines.append("")

        # 只展示 🔴必读 和 🟡推荐
        for section in self._get_section_order():
            if section not in briefs or not briefs[section]:
                continue

            meta = self.section_configs.get(section, {})
            emoji = meta.get("emoji", "")
            title = meta.get("title", section)

            important = [b for b in briefs[section] if b.get("priority") in ("🔴", "🟡")]
            if not important:
                continue

            lines.append(f"**{emoji} {title}**")
            for b in important[:5]:  # 每个 section 最多 5 条
                priority = b.get("priority", "🟢")
                headline = b.get("headline", "")
                url = b.get("url", "")
                lines.append(f"{priority} [{headline}](<{url}>)")
            lines.append("")

        lines.append("*完整报告见 HTML 版*")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"💬 Discord 版: {output_path}")
