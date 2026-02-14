"""周报/月报聚合器 — 自动从日报中聚合周期性报告"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter, defaultdict


class ReportAggregator:
    """
    从日报 analyzed JSON 数据聚合生成周报/月报
    
    原理：
    1. 收集指定时间范围内的所有日报 analyzed JSON
    2. 合并所有 briefs，按 importance 排序
    3. 提取 Top N 最重要的事件
    4. 统计关键词趋势
    5. 生成聚合 markdown
    """
    
    def __init__(self, data_dir: str = "data", reports_dir: str = "reports"):
        self.data_dir = Path(data_dir)
        self.reports_dir = Path(reports_dir)
    
    def generate_weekly(self, end_date: str = None) -> str:
        """生成周报 (最近7天)"""
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        end = datetime.strptime(end_date, "%Y-%m-%d")
        start = end - timedelta(days=6)
        start_date = start.strftime("%Y-%m-%d")
        
        briefs = self._collect_briefs(start_date, end_date)
        trends = self._collect_trends(start_date, end_date)
        
        return self._render_report(
            title=f"📅 Weekly Report: {start_date} ~ {end_date}",
            briefs=briefs,
            trends=trends,
            period="week",
            start_date=start_date,
            end_date=end_date
        )
    
    def generate_monthly(self, year: int = None, month: int = None) -> str:
        """生成月报"""
        now = datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        # 计算月份范围
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = datetime(year, month + 1, 1) - timedelta(days=1)
        end_date = end.strftime("%Y-%m-%d")
        
        briefs = self._collect_briefs(start_date, end_date)
        trends = self._collect_trends(start_date, end_date)
        
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        
        return self._render_report(
            title=f"📊 Monthly Report: {month_names[month]} {year}",
            briefs=briefs,
            trends=trends,
            period="month",
            start_date=start_date,
            end_date=end_date
        )
    
    def _collect_briefs(self, start_date: str, end_date: str) -> Dict[str, List[Dict]]:
        """收集日期范围内的所有 briefs"""
        all_briefs = defaultdict(list)
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        current = start
        days_found = 0
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            
            # 尝试找 analyzed JSON
            json_path = self.data_dir / "analyzed" / f"{date_str}.json"
            if not json_path.exists():
                json_path = self.data_dir / f"analyzed_{date_str}.json"
            
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        day_data = json.load(f)
                    
                    # 处理两种数据结构：直接的 briefs 或包含 "briefs" 键的字典
                    day_briefs = day_data.get('briefs', day_data) if isinstance(day_data, dict) else day_data
                    
                    for section, items in day_briefs.items():
                        if section.startswith('__') or not isinstance(items, list):
                            continue
                        for item in items:
                            item['_date'] = date_str
                            all_briefs[section].append(item)
                    
                    days_found += 1
                except Exception as e:
                    print(f"  ⚠️ Failed to load {json_path}: {e}")
            
            current += timedelta(days=1)
        
        print(f"  📂 Collected data from {days_found} days")
        
        # 按 importance 排序每个 section，取 Top items
        for section in all_briefs:
            all_briefs[section] = sorted(
                all_briefs[section],
                key=lambda x: x.get('importance', 3),
                reverse=True
            )
        
        return dict(all_briefs)
    
    def _collect_trends(self, start_date: str, end_date: str) -> List[Dict]:
        """聚合趋势数据"""
        trend_dir = self.data_dir / "trend_history"
        if not trend_dir.exists():
            return []
        
        all_keywords = Counter()
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            filepath = trend_dir / f"{date_str}.json"
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    day_kws = json.load(f)
                    all_keywords.update(day_kws)
            current += timedelta(days=1)
        
        return [{"keyword": kw, "count": count} for kw, count in all_keywords.most_common(30)]
    
    def _render_report(self, title: str, briefs: Dict[str, List[Dict]], 
                       trends: List[Dict], period: str,
                       start_date: str, end_date: str) -> str:
        """渲染聚合报告为 Markdown"""
        lines = []
        lines.append(f"# {title}")
        lines.append(f"\n> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"> Period: {start_date} to {end_date}")
        
        # 统计概览
        total = sum(len(items) for items in briefs.values())
        sections = len(briefs)
        lines.append(f"\n## 📈 Overview\n")
        lines.append(f"- **Total articles analyzed**: {total}")
        lines.append(f"- **Sections covered**: {sections}")
        
        # 每个 section 的 Top 5
        top_n = 5 if period == "week" else 10
        
        for section, items in sorted(briefs.items()):
            top_items = items[:top_n]
            if not top_items:
                continue
            
            lines.append(f"\n## {section.title()}\n")
            lines.append(f"Top {len(top_items)} most important:\n")
            
            for i, item in enumerate(top_items, 1):
                importance = item.get('importance', 3)
                stars = "🔴" if importance >= 5 else "🟡" if importance >= 4 else "🟢"
                headline = item.get('headline', 'No headline')
                url = item.get('url', '')
                date = item.get('_date', '')
                insight = item.get('insight', '')
                
                lines.append(f"{i}. {stars} **{headline}**")
                if url:
                    lines.append(f"   - Link: {url}")
                if date:
                    lines.append(f"   - Date: {date}")
                if insight:
                    lines.append(f"   - 💡 {insight}")
                lines.append("")
        
        # 热门关键词
        if trends:
            lines.append(f"\n## 🔥 Hot Keywords\n")
            lines.append("| Keyword | Mentions |")
            lines.append("|---------|----------|")
            for t in trends[:15]:
                lines.append(f"| {t['keyword']} | {t['count']} |")
        
        lines.append(f"\n---\n*Generated by Newsloom v0.2.0*")
        
        return "\n".join(lines)
    
    def save_report(self, content: str, filename: str):
        """保存报告到 reports 目录"""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.reports_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  💾 Saved: {filepath}")
        return filepath