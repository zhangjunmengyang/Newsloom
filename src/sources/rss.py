"""RSS Feed data source"""

import feedparser
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from .base import DataSource, Item


class RSSSource(DataSource):
    """RSS Feed data source implementation"""

    def get_source_name(self) -> str:
        return f"rss_{self.config.get('channel', 'tech')}"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """Fetch RSS feeds"""
        feeds = self.config.get('feeds', [])
        max_per_feed = self.config.get('max_per_feed', 30)

        all_items = []
        cutoff_time = None

        if hours_ago is not None:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)

        for feed_config in feeds:
            feed_url = feed_config.get('url')
            feed_name = feed_config.get('name', feed_url)

            try:
                items = self._fetch_feed(feed_url, feed_name, max_per_feed, cutoff_time)
                all_items.extend(items)
            except Exception as e:
                print(f"    ⚠️  Failed to fetch {feed_name}: {e}")
                continue

        return all_items

    def _fetch_feed(
        self,
        feed_url: str,
        feed_name: str,
        max_items: int,
        cutoff_time: Optional[datetime]
    ) -> List[Item]:
        """Fetch single RSS feed"""
        feed = feedparser.parse(feed_url)
        items = []

        for entry in feed.entries[:max_items]:
            # Extract publish date
            published_at = self._parse_date(entry)

            # Filter by time if specified
            if cutoff_time and published_at < cutoff_time:
                continue

            # Extract content
            title = entry.get('title', 'No title')

            # Try different content fields
            text = ''
            if hasattr(entry, 'content'):
                text = entry.content[0].value
            elif hasattr(entry, 'summary'):
                text = entry.summary
            elif hasattr(entry, 'description'):
                text = entry.description

            # Clean HTML tags
            text = self._clean_html(text)

            url = entry.get('link', '')
            author = entry.get('author', feed_name)

            # Create metadata
            metadata = {
                'feed_title': feed.feed.get('title', feed_name),
                'feed_url': feed_url,
            }

            # Add tags if available
            if hasattr(entry, 'tags'):
                metadata['tags'] = [tag.term for tag in entry.tags]

            # Create item
            item = self._make_item(
                native_id=entry.get('id', url),
                title=title,
                text=text,
                url=url,
                author=author,
                published_at=published_at,
                metadata=metadata
            )

            items.append(item)

        return items

    def _parse_date(self, entry) -> datetime:
        """Parse RSS entry date"""
        # Try different date fields
        for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    dt = datetime(*time_struct[:6], tzinfo=timezone.utc)
                    return dt

        # Fallback to current time
        return datetime.now(timezone.utc)

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text"""
        import re
        # Simple HTML tag removal
        text = re.sub(r'<[^>]+>', '', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
