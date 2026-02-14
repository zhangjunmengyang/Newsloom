"""趋势检测器 — 跨天关键词热度追踪"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import Counter


class TrendDetector:
    """
    基于关键词频率的趋势检测
    
    原理：
    1. 从今日 briefs 提取关键词（headline + tags）
    2. 从历史数据（前 N 天的 analyzed JSON）提取关键词
    3. 对比频率变化，标注 trending up / trending down / new
    """
    
    def __init__(self, data_dir: str = "data", lookback_days: int = 7):
        self.data_dir = Path(data_dir)
        self.lookback_days = lookback_days
    
    def detect(self, today_briefs: Dict[str, List[Dict]], today_date: str = None) -> List[Dict]:
        """
        检测趋势
        
        Args:
            today_briefs: 今日的 {section: [briefs]} 数据
            today_date: 日期字符串 YYYY-MM-DD（默认今天）
            
        Returns:
            List[Dict]: 趋势列表，每个包含:
                - keyword: str
                - trend: "🔥 rising" | "📈 steady" | "🆕 new" | "📉 declining"  
                - today_count: int
                - avg_count: float
                - change_pct: float
                - related_headlines: List[str] (最多3条)
        """
        if today_date is None:
            today_date = datetime.now().strftime("%Y-%m-%d")
        
        # 1. 提取今日关键词
        today_keywords = self._extract_keywords(today_briefs)
        
        # 2. 加载历史数据并提取关键词
        historical = self._load_historical(today_date)
        
        if not historical:
            # 没有历史数据，全部标为 new
            return [
                {
                    "keyword": kw,
                    "trend": "🆕 new",
                    "today_count": count,
                    "avg_count": 0,
                    "change_pct": 100,
                    "related_headlines": self._find_headlines(kw, today_briefs)[:3]
                }
                for kw, count in today_keywords.most_common(15)
            ]
        
        # 3. 计算历史平均
        avg_keywords = Counter()
        for day_kws in historical.values():
            for kw, count in day_kws.items():
                avg_keywords[kw] += count
        
        num_days = len(historical)
        for kw in avg_keywords:
            avg_keywords[kw] /= num_days
        
        # 4. 对比
        trends = []
        all_keywords = set(today_keywords.keys()) | set(avg_keywords.keys())
        
        for kw in all_keywords:
            today_count = today_keywords.get(kw, 0)
            avg_count = avg_keywords.get(kw, 0)
            
            if today_count == 0:
                continue  # 今天没出现的不报
            
            if avg_count == 0:
                trend = "🆕 new"
                change_pct = 100
            elif today_count >= avg_count * 2:
                trend = "🔥 rising"
                change_pct = ((today_count - avg_count) / avg_count) * 100
            elif today_count >= avg_count * 0.8:
                trend = "📈 steady"
                change_pct = ((today_count - avg_count) / avg_count) * 100
            else:
                trend = "📉 declining"
                change_pct = ((today_count - avg_count) / avg_count) * 100
            
            trends.append({
                "keyword": kw,
                "trend": trend,
                "today_count": today_count,
                "avg_count": round(avg_count, 1),
                "change_pct": round(change_pct, 1),
                "related_headlines": self._find_headlines(kw, today_briefs)[:3]
            })
        
        # 按变化幅度排序，rising 优先
        trend_priority = {"🔥 rising": 0, "🆕 new": 1, "📈 steady": 2, "📉 declining": 3}
        trends.sort(key=lambda x: (trend_priority.get(x["trend"], 9), -abs(x["change_pct"])))
        
        return trends[:20]  # Top 20
    
    def save_today_keywords(self, briefs: Dict[str, List[Dict]], date: str = None):
        """保存今日关键词到历史数据（供未来对比）"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        keywords = self._extract_keywords(briefs)
        
        history_dir = self.data_dir / "trend_history"
        history_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = history_dir / f"{date}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dict(keywords), f, ensure_ascii=False, indent=2)
    
    def _extract_keywords(self, briefs: Dict[str, List[Dict]]) -> Counter:
        """从 briefs 中提取关键词频率"""
        keywords = Counter()
        
        for section, items in briefs.items():
            if section.startswith('__') or not isinstance(items, list):
                continue
            for item in items:
                # 从 headline 提取
                headline = item.get('headline', '')
                words = self._tokenize(headline)
                keywords.update(words)
                
                # 从 tags 提取
                tags = item.get('category_tags', [])
                keywords.update([t.lower().strip() for t in tags if len(t) > 1])
        
        return keywords
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词：提取有意义的词（2+ 字符，过滤停用词）"""
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'shall', 'must',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'out', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where',
            'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just', 'because',
            'but', 'and', 'or', 'if', 'while', 'about', 'up', 'down',
            'new', 'what', 'that', 'this', 'its', 'it', 'your', 'their',
            'our', 'my', 'his', 'her', 'who', 'which',
            # 中文停用词
            '的', '了', '和', '是', '在', '不', '有', '我', '他', '这',
            '中', '大', '来', '上', '个', '要', '就', '与', '及', '等',
        }
        
        # 英文分词
        words = re.findall(r'[a-zA-Z]{2,}', text.lower())
        # 中文：提取2-4字组合（简单 bigram/trigram）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
        
        result = [w for w in words if w not in stopwords and len(w) > 2]
        result.extend([c for c in chinese_chars if c not in stopwords])
        
        return result
    
    def _load_historical(self, today_date: str) -> Dict[str, Counter]:
        """加载历史N天的关键词数据"""
        history_dir = self.data_dir / "trend_history"
        if not history_dir.exists():
            return {}
        
        today = datetime.strptime(today_date, "%Y-%m-%d")
        historical = {}
        
        for i in range(1, self.lookback_days + 1):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            filepath = history_dir / f"{date}.json"
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    historical[date] = Counter(data)
        
        return historical
    
    def _find_headlines(self, keyword: str, briefs: Dict[str, List[Dict]]) -> List[str]:
        """找到包含关键词的 headlines"""
        headlines = []
        kw_lower = keyword.lower()
        
        for section, items in briefs.items():
            if section.startswith('__') or not isinstance(items, list):
                continue
            for item in items:
                headline = item.get('headline', '')
                if kw_lower in headline.lower() or kw_lower in ' '.join(item.get('category_tags', [])).lower():
                    headlines.append(headline)
        
        return headlines