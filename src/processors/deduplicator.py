"""事件去重与聚合器"""

from typing import List, Dict, Tuple
from difflib import SequenceMatcher
import re


class Deduplicator:
    """
    基于标题相似度 + URL 域名的去重器
    
    策略：
    1. URL 精确匹配（去掉 query params 后）
    2. 标题相似度 > 0.6 且 URL 域名不同 → 聚合为一条（保留 importance 最高的，合并 sources）
    3. 标题相似度 > 0.85 且 URL 域名相同 → 去重（只保留一条）
    """
    
    def __init__(self, title_threshold: float = 0.6, strict_threshold: float = 0.85):
        self.title_threshold = title_threshold
        self.strict_threshold = strict_threshold
    
    def deduplicate(self, briefs: List[Dict]) -> List[Dict]:
        """
        去重并聚合 briefs
        
        每条 brief 需要有: headline, url, source, importance
        返回去重后的 briefs，聚合的条目会有 'related_sources' 字段
        """
        if not briefs:
            return []
        
        # 按 importance 降序，高分优先保留
        sorted_briefs = sorted(briefs, key=lambda x: x.get('importance', 3), reverse=True)
        
        clusters = []  # List of (representative_brief, [related_briefs])
        
        for brief in sorted_briefs:
            merged = False
            for cluster in clusters:
                rep = cluster[0]
                sim = self._title_similarity(brief.get('headline', ''), rep.get('headline', ''))
                same_domain = self._same_domain(brief.get('url', ''), rep.get('url', ''))
                
                if same_domain and sim > self.strict_threshold:
                    # 同域高相似 → 丢弃
                    merged = True
                    break
                elif sim > self.title_threshold and not same_domain:
                    # 不同域但相似 → 聚合，记录来源
                    cluster[1].append(brief)
                    merged = True
                    break
            
            if not merged:
                clusters.append((brief, []))
        
        # 构建输出
        result = []
        for rep, related in clusters:
            if related:
                sources = [rep.get('source', '')]
                sources.extend([b.get('source', '') for b in related])
                rep['related_sources'] = list(set(s for s in sources if s))
                rep['mention_count'] = len(related) + 1
            result.append(rep)
        
        return result
    
    @staticmethod
    def _title_similarity(t1: str, t2: str) -> float:
        """标题相似度（忽略大小写和标点）"""
        def clean(t):
            return re.sub(r'[^\w\s]', '', t.lower().strip())
        return SequenceMatcher(None, clean(t1), clean(t2)).ratio()
    
    @staticmethod  
    def _same_domain(url1: str, url2: str) -> bool:
        """URL 域名是否相同"""
        from urllib.parse import urlparse
        try:
            d1 = urlparse(url1).netloc.replace('www.', '')
            d2 = urlparse(url2).netloc.replace('www.', '')
            return d1 == d2 and d1 != ''
        except:
            return False