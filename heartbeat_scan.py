#!/usr/bin/env python3
"""
Newsloom 增量心跳扫描器

每次心跳调用此脚本，快速扫描高优先级源，
返回新发现的🔴/🟡信号，供哨兵决定是否立即汇报。

用法：
    conda run -n newsloom python heartbeat_scan.py
    conda run -n newsloom python heartbeat_scan.py --hours 2
    conda run -n newsloom python heartbeat_scan.py --sources exchange,anthropic,hackernews
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / '.env')
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sources.registry import SourceRegistry
from processors.fetcher import ParallelFetcher
from processors.ranker import RankingPipeline
from utils.state import StateManager


# 心跳扫描的高优先级源白名单（快速、高价值）
HEARTBEAT_SOURCES = {
    'exchange',      # 交易所上线
    'anthropic',     # Anthropic 官方
    'hackernews',    # HN 热帖
    'arxiv',         # 论文
    'github',        # GitHub Trending
    'reddit',        # Reddit 热帖
}

# 关键词分级（用于心跳快速过滤）
URGENT_KEYWORDS = [
    # 交易所上线信号
    'listing', '上线', '上币', '新增', 'new pair', 'new trading',
    # 模型发布
    'release', 'launch', 'announced', 'gpt', 'claude', 'gemini', 'llama',
    'model', '发布', '开源',
    # 监管/重大事件
    'ban', 'regulation', 'sec', 'arrest', 'hack', 'exploit', 'breach',
    'blackout', 'shutdown', '监管', '黑客', '漏洞',
    # 市场结构性事件
    'liquidation', 'whale', 'billion', 'flash crash', '清算', '鲸鱼',
]


def score_item_urgency(item) -> int:
    """快速评估条目紧急度（0-10）"""
    score = 0
    text = (item.title + " " + item.text[:200]).lower()
    meta = getattr(item, 'metadata', {}) or {}

    # 交易所上线：最高优先级
    if item.source == 'exchange_listing':
        title_lower = item.title.lower()
        # 真实上线公告（排除 CoinGecko Trending）
        if any(k in title_lower for k in ['上线', 'listing', 'new pair', 'new trading', '新增', '新上线']):
            score += 8
            if '🇰🇷' in item.title or 'upbit' in text or 'bithumb' in text:
                score += 2  # 韩国交易所上线额外加分

        # CoinGecko Trending 异动检测：价格变化 >20% 才值得关注
        elif 'coingecko trending' in title_lower:
            price_change = abs(meta.get('price_change_24h', 0))
            if price_change >= 50:
                score += 7   # 暴涨/暴跌 ≥50% → 🔴
            elif price_change >= 30:
                score += 5   # 大涨/大跌 30-50% → 🟡
            elif price_change >= 20:
                score += 3   # 明显异动 20-30% → 边界
            # <20% 纯热门榜，不加分，会被过滤掉

    # Anthropic 官方
    if item.source == 'anthropic_news':
        score += 5
        if any(k in text for k in ['claude', 'model', 'api', 'skill', 'agent']):
            score += 2

    # 关键词匹配
    for kw in URGENT_KEYWORDS:
        if kw in text:
            score += 1

    # HN 高分帖
    if meta:
        hn_score = meta.get('score', 0)
        if hn_score > 500:
            score += 3
        elif hn_score > 200:
            score += 1

    return min(score, 10)


def format_signal(item, urgency: int) -> dict:
    """格式化为心跳信号"""
    priority = "🔴" if urgency >= 7 else "🟡" if urgency >= 4 else "🟢"
    meta = getattr(item, 'metadata', {}) or {}
    sig = {
        "priority": priority,
        "urgency": urgency,
        "title": item.title,
        "url": item.url,
        "source": item.source,
        "channel": item.channel,
        "published": item.published_at.isoformat() if item.published_at else None,
    }
    # 附加有用的 metadata 字段
    if meta.get('price_change_24h') is not None:
        sig['price_change_24h'] = meta['price_change_24h']
    if meta.get('symbol'):
        sig['symbol'] = meta['symbol']
    return sig


def run_heartbeat_scan(hours: int = 2, source_filter: list = None) -> dict:
    """执行心跳扫描"""
    project_dir = Path(__file__).parent
    config_path = project_dir / 'config' / 'sources.yaml'
    state_file = project_dir / 'data' / 'state' / 'heartbeat-state.json'

    state_manager = StateManager(str(state_file), dedup_window_days=1)

    # 加载源
    registry = SourceRegistry(str(config_path))
    all_sources = registry.get_enabled_sources()

    # 过滤出心跳源
    if source_filter:
        target_types = set(source_filter)
    else:
        target_types = HEARTBEAT_SOURCES

    heartbeat_sources = []
    for src in all_sources:
        src_type = type(src).__name__.lower().replace('source', '')
        src_name = src.get_source_name().lower()
        if any(t in src_name or t in src_type for t in target_types):
            heartbeat_sources.append(src)

    if not heartbeat_sources:
        return {"signals": [], "summary": "无可用心跳源", "scanned": 0}

    # 并行抓取
    fetcher = ParallelFetcher(heartbeat_sources, state_manager)
    items = fetcher.fetch_all(hours_ago=hours)
    state_manager.save()

    # 快速评分 + 过滤
    signals = []
    for item in items:
        urgency = score_item_urgency(item)
        if urgency >= 4:  # 只报 🟡 以上
            signals.append(format_signal(item, urgency))

    # 按紧急度排序
    signals.sort(key=lambda x: x['urgency'], reverse=True)

    # 统计
    red_count = sum(1 for s in signals if s['priority'] == '🔴')
    yellow_count = sum(1 for s in signals if s['priority'] == '🟡')

    return {
        "signals": signals,
        "scanned": len(items),
        "red": red_count,
        "yellow": yellow_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": f"扫描 {len(items)} 条 → {red_count}🔴 {yellow_count}🟡",
    }


def main():
    parser = argparse.ArgumentParser(description='Newsloom 心跳增量扫描')
    parser.add_argument('--hours', type=int, default=2, help='扫描最近N小时（默认2）')
    parser.add_argument('--sources', type=str, help='指定源类型，逗号分隔（如：exchange,anthropic）')
    parser.add_argument('--json', action='store_true', help='JSON输出（供程序调用）')
    parser.add_argument('--min-urgency', type=int, default=4, help='最低紧急度阈值（默认4=🟡）')
    args = parser.parse_args()

    source_filter = None
    if args.sources:
        source_filter = [s.strip() for s in args.sources.split(',')]

    result = run_heartbeat_scan(hours=args.hours, source_filter=source_filter)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 人类可读输出
    print(f"\n🔍 心跳扫描完成 — {result['summary']}")
    print(f"时间：{datetime.now().strftime('%H:%M:%S')}")

    if not result['signals']:
        print("\n✅ 无新信号，HEARTBEAT_OK")
        return

    print(f"\n{'='*50}")
    for sig in result['signals']:
        if sig['urgency'] < args.min_urgency:
            continue
        print(f"\n{sig['priority']} [{sig['source']}] {sig['title']}")
        if sig['url']:
            print(f"   {sig['url']}")

    print(f"\n{'='*50}")
    print(f"🔴 {result['red']} 条紧急  🟡 {result['yellow']} 条重要")


if __name__ == '__main__':
    main()
