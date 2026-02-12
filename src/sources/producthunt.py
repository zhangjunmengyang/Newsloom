"""Product Hunt 数据源 — 每日热门产品（via RSS）"""

import feedparser
import re
from typing import List, Optional
from datetime import datetime, timezone

from .base import DataSource, Item


class ProductHuntSource(DataSource):
    """
    Product Hunt 每日热门产品

    配置示例:
    ```yaml
    producthunt:
      enabled: true
      channel: "tech"
      type: "producthunt"
      count: 10
    ```
    """

    RSS_URL = "https://www.producthunt.com/feed"

    def get_source_name(self) -> str:
        return "producthunt"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """通过 RSS 抓取 Product Hunt 热门产品"""
        count = self.config.get('count', 10)

        print(f"    🚀 Product Hunt: 获取最多 {count} 个产品")

        try:
            feed = feedparser.parse(self.RSS_URL)

            if feed.bozo and not feed.entries:
                print(f"    ⚠️  Product Hunt RSS 解析失败: {feed.bozo_exception}")
                return []

            items: List[Item] = []

            for entry in feed.entries[:count]:
                item = self._parse_entry(entry)
                if item:
                    items.append(item)

            print(f"    ✅ Product Hunt: 获取到 {len(items)} 个产品")
            return items

        except Exception as e:
            print(f"    ⚠️  Product Hunt 抓取失败: {e}")
            return []

    def _parse_entry(self, entry) -> Optional[Item]:
        """解析单个 RSS entry"""
        title = entry.get('title', 'Unknown Product')
        url = entry.get('link', '')

        # 提取描述/tagline
        description = ''
        if hasattr(entry, 'summary'):
            description = self._clean_html(entry.summary)
        elif hasattr(entry, 'description'):
            description = self._clean_html(entry.description)

        # 解析时间
        published_at = self._parse_date(entry)

        # 作者
        author = entry.get('author', 'Product Hunt')

        # 构建 text
        text = description if description else title

        # 提取 tags
        tags = []
        if hasattr(entry, 'tags'):
            tags = [tag.term for tag in entry.tags]

        metadata = {
            'feed_name': 'Product Hunt',
            'tags': tags,
        }

        return self._make_item(
            native_id=entry.get('id', url),
            title=title,
            text=text,
            url=url,
            author=author,
            published_at=published_at,
            metadata=metadata,
        )

    def _parse_date(self, entry) -> datetime:
        """解析 RSS entry 日期"""
        for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    return datetime(*time_struct[:6], tzinfo=timezone.utc)
        return datetime.now(timezone.utc)

    def _clean_html(self, html: str) -> str:
        """移除 HTML 标签"""
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
