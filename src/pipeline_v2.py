"""Pipeline v2 — 推荐系统式信息处理

改进架构：
  Fetch (并行) → 粗排 (规则) → 精排 (AI) → 洞察提取 (AI) → 生成报告

vs 旧版：
  Fetch → 关键词过滤 → AI 过滤 + 提取 → 生成
"""

import argparse
import yaml
import os
import json
import signal
import sys
from pathlib import Path
from datetime import datetime, timezone

from sources.registry import SourceRegistry
from processors.fetcher import ParallelFetcher
from processors.ranker import RankingPipeline
from processors.analyzer_v2 import AIAnalyzerV2
from processors.generator_v2 import ReportGeneratorV2
from utils.state import StateManager
from utils.time_utils import get_date_str


class PipelineTimeout(Exception):
    """Pipeline global timeout exceeded"""
    pass


def _timeout_handler(signum, frame):
    raise PipelineTimeout("Pipeline global timeout exceeded (600s)")


class PipelineV2:
    """v2 Pipeline — 推荐系统架构"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.reports_dir = Path(self.config["output"]["base_dir"])

        self.data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

    OBSIDIAN_VAULT = Path("/Users/peterzhang/project/morpheus-vault")
    OBSIDIAN_NEWSLOOM_DIR = OBSIDIAN_VAULT / "日报"

    def _archive_to_obsidian(self, output_dir: Path, date_str: str):
        """将日报 Markdown 归档到 Obsidian vault"""
        try:
            source_md = output_dir / "report.md"
            if not source_md.exists():
                print("⚠️ Obsidian 入库跳过: report.md 不存在")
                return

            self.OBSIDIAN_NEWSLOOM_DIR.mkdir(parents=True, exist_ok=True)

            with open(source_md, "r", encoding="utf-8") as f:
                content = f.read()

            # 添加 Obsidian frontmatter
            frontmatter = f"""---
title: "Newsloom 每日情报 {date_str}"
date: {date_str}
tags:
  - newsloom
  - daily-report
type: report
---

"""
            dest_file = self.OBSIDIAN_NEWSLOOM_DIR / f"{date_str} 每日情报.md"
            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(frontmatter + content)

            print(f"📚 Obsidian 入库: {dest_file}")

        except Exception as e:
            print(f"⚠️ Obsidian 入库失败: {e}")

    def _load_config(self) -> dict:
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
        return self._replace_env_vars(config)

    def _replace_env_vars(self, obj):
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            return os.environ.get(obj[2:-1], "")
        return obj

    def run(self, layers: list = None, date_str: str = None):
        """
        运行 v2 pipeline
        
        Layers:
        - fetch: 并行抓取
        - rank: 粗排 + 去重
        - analyze: AI 精排 + 洞察提取
        - generate: 报告生成
        """
        if layers is None:
            layers = ["fetch", "rank", "analyze", "generate"]

        if date_str is None:
            date_str = get_date_str()

        # Global timeout: default 10 minutes (signal-based, Unix only)
        # Override via env NEWSLOOM_GLOBAL_TIMEOUT (seconds)
        global_timeout = int(os.environ.get("NEWSLOOM_GLOBAL_TIMEOUT", "600"))
        try:
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(global_timeout)
        except (AttributeError, OSError):
            pass  # SIGALRM not available on Windows

        print(f"\n🚀 Newsloom v2 — Intelligence Pipeline")
        print(f"📅 Date: {date_str}")
        print(f"🔧 Layers: {', '.join(layers)}")
        print(f"⏱️  Global timeout: {global_timeout}s")
        print("=" * 60)

        state_file = self.base_dir / self.config["state"]["file"]
        dedup_window = self.config["state"]["dedup_window_days"]
        state_manager = StateManager(state_file, dedup_window)

        items = []

        # ============================================================
        # Layer 1: FETCH
        # ============================================================
        if "fetch" in layers:
            print("\n" + "=" * 60)
            print("LAYER 1: FETCH")
            print("=" * 60)

            sources_config_path = self.config_path.parent / "sources.yaml"
            registry = SourceRegistry(str(sources_config_path))
            sources = registry.get_enabled_sources()

            if not sources:
                print("⚠️  No enabled sources found!")
                return

            fetcher = ParallelFetcher(sources, state_manager)
            hours_ago = self.config["pipeline"]["fetch"]["hours_ago"]
            items = fetcher.fetch_all(hours_ago=hours_ago)

            raw_path = self.data_dir / "raw" / f"{date_str}.jsonl"
            fetcher.save_raw_data(items, raw_path)
            # NOTE: state_manager.save() 延迟到 pipeline 全部成功后执行
            # 避免 fetch 成功但后续步骤失败时，新条目被标记为 seen 导致重跑时被 dedup 跳过

        # ============================================================
        # Layer 2: RANK (粗排 + 去重)
        # ============================================================
        if "rank" in layers:
            print("\n" + "=" * 60)
            print("LAYER 2: COARSE RANK + DEDUP")
            print("=" * 60)

            if not items:
                raw_path = self.data_dir / "raw" / f"{date_str}.jsonl"
                if raw_path.exists():
                    fetcher = ParallelFetcher([], state_manager)
                    items = fetcher.load_raw_data(raw_path)
                    print(f"📥 从文件加载: {len(items)} 条")
                else:
                    print(f"⚠️  No raw data for {date_str}")
                    return

            ranker = RankingPipeline(self.config.get("ranking", {}))
            top_n = self.config.get("ranking", {}).get("coarse_top_n", 200)
            items = ranker.process(items, top_n=top_n)

            # 保存粗排结果
            ranked_path = self.data_dir / "ranked" / f"{date_str}.jsonl"
            ranked_path.parent.mkdir(parents=True, exist_ok=True)
            with open(ranked_path, "w", encoding="utf-8") as f:
                for item in items:
                    f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
            print(f"💾 粗排结果: {ranked_path}")

        # ============================================================
        # Layer 3: ANALYZE (AI 精排 + 洞察)
        # ============================================================
        if "analyze" in layers:
            print("\n" + "=" * 60)
            print("LAYER 3: AI FINE RANK + INSIGHTS")
            print("=" * 60)

            if not items:
                # 优先加载粗排结果
                ranked_path = self.data_dir / "ranked" / f"{date_str}.jsonl"
                if ranked_path.exists():
                    from sources.base import Item
                    items = []
                    with open(ranked_path, encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                items.append(Item.from_dict(json.loads(line)))
                    print(f"📥 从粗排文件加载: {len(items)} 条")
                else:
                    print(f"⚠️  No ranked data for {date_str}")
                    return

            api_key = self.config["ai"]["claude"].get("api_key", "")
            if not api_key:
                print("⚠️  未配置 ANTHROPIC_API_KEY，跳过 AI 分析")
                return

            from ai.claude import ClaudeClient
            claude = ClaudeClient(
                api_key=api_key,
                base_url=self.config["ai"]["claude"].get("base_url") or None,
                model=self.config["ai"]["claude"].get("model"),
                protocol=self.config["ai"]["claude"].get("protocol") or "anthropic",
            )

            analyzer = AIAnalyzerV2(
                claude_client=claude,
                config=self.config.get("analyze", {}),
            )

            result = analyzer.analyze(items, top_per_section=12)

            # 保存
            analyzed_path = self.data_dir / "analyzed" / f"{date_str}.json"
            analyzer.save_analyzed_data(result, analyzed_path)

            # 传给下一层
            items = result
            
            # ============================================================
            # POST-ANALYZE: DEDUP + TREND DETECTION
            # ============================================================
            print("\n" + "-" * 40)
            print("POST-ANALYZE: DEDUP + TREND DETECTION")
            print("-" * 40)
            
            # --- 去重 ---
            from processors.deduplicator import Deduplicator
            deduplicator = Deduplicator()
            
            # Get briefs from analyzed data (handle both old and new format)
            analyzed_briefs = items.get("briefs", items) if isinstance(items, dict) else items
            
            for section in analyzed_briefs:
                if section.startswith('__'):
                    continue
                if isinstance(analyzed_briefs[section], list):
                    before = len(analyzed_briefs[section])
                    analyzed_briefs[section] = deduplicator.deduplicate(analyzed_briefs[section])
                    after = len(analyzed_briefs[section])
                    if before != after:
                        print(f"  🔄 [{section}] 去重: {before} → {after}")

            # --- 趋势检测 ---
            from processors.trend_detector import TrendDetector
            trend_detector = TrendDetector(data_dir=str(self.data_dir))
            trends = trend_detector.detect(analyzed_briefs, date_str)
            trend_detector.save_today_keywords(analyzed_briefs, date_str)
            
            if trends:
                # 注入到 briefs 供 generator 渲染
                analyzed_briefs['__trends__'] = trends
                rising = [t for t in trends if '🔥' in t['trend'] or '🆕' in t['trend']]
                print(f"  📊 趋势检测: {len(trends)} 个关键词, {len(rising)} 个上升")
            
            # Update items with processed data
            if isinstance(items, dict):
                items["briefs"] = analyzed_briefs
            else:
                items = analyzed_briefs

        # ============================================================
        # Layer 4: GENERATE
        # ============================================================
        if "generate" in layers:
            print("\n" + "=" * 60)
            print("LAYER 4: GENERATE REPORTS")
            print("=" * 60)

            if not items or not isinstance(items, dict):
                analyzed_path = self.data_dir / "analyzed" / f"{date_str}.json"
                if analyzed_path.exists():
                    with open(analyzed_path, encoding="utf-8") as f:
                        items = json.load(f)
                    print(f"📥 从分析文件加载")
                else:
                    print(f"⚠️  No analyzed data for {date_str}")
                    return

            output_dir = self.reports_dir / date_str
            generator = ReportGeneratorV2(self.config)
            generator.generate(items, date_str, output_dir)

            # latest 软链
            for fmt in ["md", "html", "pdf"]:
                latest = self.reports_dir / f"latest.{fmt}"
                report = output_dir / f"report.{fmt}"
                if report.exists():
                    if latest.exists() or latest.is_symlink():
                        latest.unlink()
                    latest.symlink_to(report)

            # Obsidian 入库
            self._archive_to_obsidian(output_dir, date_str)

            # ============================================================
            # RSS Feed 自动生成
            # ============================================================
            try:
                from processors.rss_generator import RSSGenerator
                rss_gen = RSSGenerator()
                
                # 从 analyzed briefs 生成 RSS
                if isinstance(items, dict) and 'briefs' in items:
                    briefs = items['briefs']
                elif isinstance(items, dict):
                    briefs = items
                else:
                    briefs = {}
                    
                if briefs:
                    rss_xml = rss_gen.generate_from_briefs(briefs, date=date_str)
                    rss_gen.save_feed(rss_xml, str(self.reports_dir / "feed.xml"))
                    print("📡 RSS feed updated")
            except Exception as e:
                print(f"⚠️ RSS generation failed: {e}")

        # Cancel global timeout
        try:
            signal.alarm(0)
        except (AttributeError, OSError):
            pass

        # Pipeline 全部成功，现在才保存 state（标记 seen items）
        # 这样如果中间步骤失败，重跑时这些条目不会被 dedup 跳过
        if "fetch" in layers:
            state_manager.save()
            print("💾 State saved (seen items updated)")

        print("\n" + "=" * 60)
        print("✅ Pipeline v2 completed!")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Newsloom v2 — Intelligence Pipeline")
    parser.add_argument("--config", type=str, help="Path to config.yaml")
    parser.add_argument("--layers", type=str, help="Comma-separated layers: fetch,rank,analyze,generate")
    parser.add_argument("--date", type=str, help="Date YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    layers = None
    if args.layers:
        layers = [l.strip() for l in args.layers.split(",")]

    pipeline = PipelineV2(config_path=args.config)
    pipeline.run(layers=layers, date_str=args.date)


if __name__ == "__main__":
    main()
