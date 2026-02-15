#!/usr/bin/env python3
"""对比新旧 PDF 生成效果"""

import json
import yaml
from pathlib import Path
from src.processors.generator_v2 import ReportGeneratorV2

def generate_comparison():
    # 加载配置
    config_path = Path("config/config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 加载最新的分析数据
    analyzed_dir = Path("data/analyzed")
    latest_file = sorted(analyzed_dir.glob("*.json"), reverse=True)[0]
    date_str = latest_file.stem

    with open(latest_file, "r", encoding="utf-8") as f:
        analyzed_data = json.load(f)

    # 生成新版本（使用打印模板）
    print("\n🎨 生成新版 PDF（杂志风格 + 亮色）...")
    output_new = Path("test_output/comparison/new")
    output_new.mkdir(parents=True, exist_ok=True)

    generator_new = ReportGeneratorV2(config)
    generator_new.formats = ["html", "pdf"]
    generator_new.generate(analyzed_data, date_str, output_new)

    # 生成旧版本（直接转换暗色 HTML）
    print("\n🌑 生成旧版 PDF（暗色 HTML 直接转换）...")
    output_old = Path("test_output/comparison/old")
    output_old.mkdir(parents=True, exist_ok=True)

    generator_old = ReportGeneratorV2(config)
    generator_old.formats = ["html"]
    generator_old.generate(analyzed_data, date_str, output_old)

    # 使用 fallback 方法生成旧版 PDF
    from weasyprint import HTML as WeasyHTML
    html_path = output_old / "report.html"
    pdf_path = output_old / "report.pdf"

    # 读取暗色 HTML 并添加简单的打印 CSS
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    old_print_css = """
<style>
@page {
    size: A4;
    margin: 2cm 1.5cm;
}
body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
}
.sidebar { display: none !important; }
.main { margin-left: 0 !important; max-width: 100% !important; }
</style>
"""
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", old_print_css + "</head>")

    WeasyHTML(string=html_content, base_url=str(output_old)).write_pdf(str(pdf_path))
    print(f"📕 旧版 PDF: {pdf_path}")

    print("\n" + "="*60)
    print("📊 对比总结")
    print("="*60)

    # 文件大小对比
    new_pdf = output_new / "report.pdf"
    old_pdf = output_old / "report.pdf"

    new_size = new_pdf.stat().st_size / 1024
    old_size = old_pdf.stat().st_size / 1024

    print(f"\n📄 文件大小:")
    print(f"   新版: {new_size:>8.1f} KB  ← 专用打印模板（亮色 + 杂志风）")
    print(f"   旧版: {old_size:>8.1f} KB  ← 暗色 HTML 直接转换")

    print(f"\n✨ 新版改进:")
    print(f"   ✓ 白色背景，更适合打印")
    print(f"   ✓ 专业杂志排版（首页、目录、分页）")
    print(f"   ✓ 品牌色（#6366f1 indigo）点缀")
    print(f"   ✓ 优先级色条（🔴红/🟡黄/🟢绿）")
    print(f"   ✓ 页脚带页码")
    print(f"   ✓ Executive Summary 高亮")
    print(f"   ✓ A4 纸张优化排版")

    print(f"\n🔍 对比查看:")
    print(f"   open {new_pdf}")
    print(f"   open {old_pdf}")

if __name__ == "__main__":
    generate_comparison()
