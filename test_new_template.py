#!/usr/bin/env python3
"""测试新的统一模板 - 独立测试脚本"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加 src 到路径（和 run_v2.py 一样）
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_template():
    # 直接导入生成器
    from processors.generator_v2 import ReportGeneratorV2
    import yaml

    # 加载配置
    config_path = Path("config/config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 使用最新的分析数据
    analyzed_file = Path("data/analyzed/2026-02-15.json")
    if not analyzed_file.exists():
        # 尝试最新的
        analyzed_dir = Path("data/analyzed")
        analyzed_files = sorted(analyzed_dir.glob("*.json"), reverse=True)
        if analyzed_files:
            analyzed_file = analyzed_files[0]
        else:
            print("❌ 没有分析数据")
            return

    date_str = analyzed_file.stem
    print(f"📂 使用数据: {analyzed_file}")
    print(f"📅 日期: {date_str}")

    with open(analyzed_file, "r", encoding="utf-8") as f:
        analyzed_data = json.load(f)

    # 创建测试输出
    test_output = Path("test_output") / date_str
    test_output.mkdir(parents=True, exist_ok=True)

    print(f"📁 输出目录: {test_output}\n")

    # 初始化生成器
    generator = ReportGeneratorV2(config)
    generator.formats = ["html", "pdf"]

    print("🚀 生成报告...")

    try:
        generator.generate(analyzed_data, date_str, test_output)

        print("\n✅ 生成完成！")
        print("\n📄 输出文件:")
        for file in sorted(test_output.iterdir()):
            size = file.stat().st_size / 1024
            print(f"   {file.name:<25} {size:>8.1f} KB")

        # 显示文件路径
        html_path = test_output / "report.html"
        pdf_path = test_output / "report.pdf"

        if html_path.exists():
            print(f"\n🌐 HTML: {html_path}")
            print(f"   open {html_path}")

        if pdf_path.exists():
            print(f"\n📕 PDF: {pdf_path}")
            print(f"   open {pdf_path}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_template()
