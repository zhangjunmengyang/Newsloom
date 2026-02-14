"""RSS Feed 生成器 — 让 Newsloom 的输出可被 RSS 阅读器订阅"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from email.utils import format_datetime


class RSSGenerator:
    """
    生成 RSS 2.0 Feed
    
    从 analyzed briefs 或报告文件生成标准 RSS feed，
    可被 Feedly / Inoreader 等 RSS 阅读器订阅。
    """
    
    def __init__(self, 
                 title: str = "Newsloom Daily Intelligence",
                 link: str = "http://localhost:3000",
                 description: str = "AI-curated daily tech and AI news digest",
                 language: str = "zh-cn"):
        self.title = title
        self.link = link
        self.description = description
        self.language = language
    
    def generate_from_briefs(self, briefs: Dict[str, List[Dict]], 
                              date: str = None,
                              max_items: int = 30) -> str:
        """
        从 analyzed briefs 生成 RSS XML
        
        Args:
            briefs: {section: [brief_dicts]}
            date: 日期字符串
            max_items: 最大条目数
            
        Returns:
            str: RSS XML 字符串
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 收集所有 briefs 并按 importance 排序
        all_items = []
        for section, items in briefs.items():
            if section.startswith('__') or not isinstance(items, list):
                continue
            for item in items:
                item['_section'] = section
                all_items.append(item)
        
        all_items.sort(key=lambda x: x.get('importance', 3), reverse=True)
        all_items = all_items[:max_items]
        
        # 构建 RSS
        rss = ET.Element('rss', version='2.0')
        rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
        
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = self.title
        ET.SubElement(channel, 'link').text = self.link
        ET.SubElement(channel, 'description').text = self.description
        ET.SubElement(channel, 'language').text = self.language
        ET.SubElement(channel, 'lastBuildDate').text = format_datetime(datetime.now())
        ET.SubElement(channel, 'generator').text = 'Newsloom v0.2.0'
        
        # Atom self-link
        atom_link = ET.SubElement(channel, 'atom:link')
        atom_link.set('href', f'{self.link}/feed.xml')
        atom_link.set('rel', 'self')
        atom_link.set('type', 'application/rss+xml')
        
        for brief in all_items:
            item_el = ET.SubElement(channel, 'item')
            
            headline = brief.get('headline', 'No title')
            url = brief.get('url', '')
            section = brief.get('_section', '')
            importance = brief.get('importance', 3)
            detail = brief.get('detail', '')
            insight = brief.get('insight', '')
            source = brief.get('source', '')
            
            ET.SubElement(item_el, 'title').text = headline
            
            if url:
                ET.SubElement(item_el, 'link').text = url
                ET.SubElement(item_el, 'guid', isPermaLink='true').text = url
            else:
                guid = f"newsloom-{date}-{hash(headline) % 100000}"
                ET.SubElement(item_el, 'guid', isPermaLink='false').text = guid
            
            # Description = detail + insight
            desc_parts = []
            if detail:
                desc_parts.append(detail)
            if insight:
                desc_parts.append(f"💡 {insight}")
            if source:
                desc_parts.append(f"Source: {source}")
            
            ET.SubElement(item_el, 'description').text = "\n\n".join(desc_parts) if desc_parts else headline
            
            # Category = section
            if section:
                ET.SubElement(item_el, 'category').text = section
            
            # pubDate
            ET.SubElement(item_el, 'pubDate').text = format_datetime(datetime.now())
        
        # Pretty print
        xml_str = ET.tostring(rss, encoding='unicode', xml_declaration=True)
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent='  ', encoding=None)
    
    def generate_from_reports(self, reports_dir: str = "reports", 
                               max_items: int = 20) -> str:
        """
        从报告文件列表生成 RSS（每个报告 = 一个 RSS item）
        """
        reports_path = Path(reports_dir)
        if not reports_path.exists():
            return self._empty_feed()
        
        # 找所有 MD 报告（排除 latest 软链）
        files = sorted(
            [f for f in reports_path.rglob('*.md') if not f.is_symlink() and 'latest' not in f.name],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:max_items]
        
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = f"{self.title} - Reports"
        ET.SubElement(channel, 'link').text = self.link
        ET.SubElement(channel, 'description').text = "Daily intelligence reports"
        ET.SubElement(channel, 'language').text = self.language
        ET.SubElement(channel, 'lastBuildDate').text = format_datetime(datetime.now())
        
        for f in files:
            item_el = ET.SubElement(channel, 'item')
            ET.SubElement(item_el, 'title').text = f.stem
            ET.SubElement(item_el, 'guid', isPermaLink='false').text = f"newsloom-report-{f.stem}"
            
            # 读取前 500 字作为 description
            try:
                content = f.read_text(encoding='utf-8')[:500]
            except:
                content = ""
            ET.SubElement(item_el, 'description').text = content
            
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            ET.SubElement(item_el, 'pubDate').text = format_datetime(mtime)
        
        xml_str = ET.tostring(rss, encoding='unicode', xml_declaration=True)
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent='  ', encoding=None)
    
    def save_feed(self, xml_content: str, output_path: str = "reports/feed.xml"):
        """保存 RSS feed 到文件"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"  📡 RSS feed saved: {path}")
        return path
    
    def _empty_feed(self) -> str:
        """空 feed"""
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = self.title
        ET.SubElement(channel, 'description').text = "No reports yet"
        xml_str = ET.tostring(rss, encoding='unicode', xml_declaration=True)
        return xml_str