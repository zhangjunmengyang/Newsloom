#!/usr/bin/env python3
"""简单测试聚合器和RSS生成器"""

import sys
import os
from pathlib import Path

# 添加 src 目录到路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_aggregator():
    """测试聚合器"""
    try:
        # 直接导入不依赖其他模块的 aggregator
        import json
        from datetime import datetime, timedelta
        from collections import Counter, defaultdict
        
        # 简化版测试
        print("📊 Testing ReportAggregator...")
        
        # 检查基本类定义
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "aggregator", 
            project_root / "src" / "processors" / "aggregator.py"
        )
        aggregator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(aggregator_module)
        
        agg_class = aggregator_module.ReportAggregator
        agg = agg_class(
            data_dir=str(project_root / "data"),
            reports_dir=str(project_root / "reports")
        )
        print("✅ ReportAggregator class instantiated successfully")
        return True
    except Exception as e:
        print(f"❌ ReportAggregator test failed: {e}")
        return False

def test_rss_generator():
    """测试RSS生成器"""
    try:
        print("📡 Testing RSSGenerator...")
        
        # 直接导入
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "rss_generator", 
            project_root / "src" / "processors" / "rss_generator.py"
        )
        rss_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rss_module)
        
        rss_class = rss_module.RSSGenerator
        gen = rss_class()
        
        # 测试生成空 feed
        empty_feed = gen._empty_feed()
        assert "<?xml" in empty_feed
        assert "rss" in empty_feed
        print("✅ RSSGenerator class working correctly")
        return True
    except Exception as e:
        print(f"❌ RSSGenerator test failed: {e}")
        return False

def test_cli_commands():
    """测试CLI命令"""
    try:
        print("🖥️  Testing CLI commands...")
        
        # 测试 weekly 命令导入
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "weekly", 
            project_root / "cli" / "commands" / "weekly.py"
        )
        weekly_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(weekly_module)
        
        # 测试 feed 命令导入
        spec = importlib.util.spec_from_file_location(
            "feed", 
            project_root / "cli" / "commands" / "feed.py"
        )
        feed_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(feed_module)
        
        print("✅ CLI commands imported successfully")
        return True
    except Exception as e:
        print(f"❌ CLI commands test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Sprint 5 features...")
    print("=" * 50)
    
    results = []
    results.append(test_aggregator())
    results.append(test_rss_generator())
    results.append(test_cli_commands())
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)