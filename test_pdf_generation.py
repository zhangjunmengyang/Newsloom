#!/usr/bin/env python3
"""测试新的 PDF 生成功能"""

import json
import yaml
from pathlib import Path
from src.processors.generator_v2 import ReportGeneratorV2

def test_pdf_generation():
    # 加载配置
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ config.yaml 不存在")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 加载最新的分析数据
    analyzed_dir = Path("data/analyzed")
    if not analyzed_dir.exists():
        print("❌ data/analyzed 目录不存在")
        return

    # 找最新的分析文件
    analyzed_files = sorted(analyzed_dir.glob("*.json"), reverse=True)
    if not analyzed_files:
        print("❌ 没有找到分析数据")
        return

    latest_file = analyzed_files[0]
    date_str = latest_file.stem

    print(f"\n📂 使用数据文件: {latest_file}")
    print(f"📅 日期: {date_str}")

    with open(latest_file, "r", encoding="utf-8") as f:
        analyzed_data = json.load(f)

    # 创建测试输出目录
    test_output_dir = Path("test_output") / date_str
    test_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 测试输出目录: {test_output_dir}")

    # 初始化生成器
    generator = ReportGeneratorV2(config)

    # 设置格式为仅 PDF（用于快速测试）
    generator.formats = ["html", "pdf"]

    print("\n🚀 开始生成报告...")

    # 生成报告
    generator.generate(analyzed_data, date_str, test_output_dir)

    print("\n✅ 测试完成！")
    print(f"\n📄 输出文件:")
    for file in sorted(test_output_dir.iterdir()):
        size = file.stat().st_size / 1024
        print(f"   {file.name:<20} {size:>8.1f} KB")

    # 显示 PDF 路径
    pdf_path = test_output_dir / "report.pdf"
    if pdf_path.exists():
        print(f"\n📕 PDF 文件: {pdf_path}")
        print(f"   可以用以下命令打开:")
        print(f"   open {pdf_path}")
    else:
        print(f"\n⚠️ PDF 文件未生成")

if __name__ == "__main__":
    test_pdf_generation()
