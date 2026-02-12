"""Abstract base class for all data sources"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import hashlib


@dataclass
class Item:
    """Unified data item format across all sources"""

    id: str                    # Unique identifier: {source}:{native_id}
    source: str                # Data source name (twitter/rss/arxiv/...)
    channel: str               # Classification channel (ai/tech/finance/papers/...)
    title: str                 # Title (first 120 characters)
    text: str                  # Full text content
    url: str                   # Original URL
    author: str                # Author/source
    published_at: datetime     # Publication time (UTC aware)

    # Optional metadata (source-specific)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Examples:
    # - Twitter: likes, retweets, views, image_url
    # - arXiv: authors, categories, pdf_url
    # - GitHub: stars, language, daily_stars
    # - RSS: feed_title, tags

    # Processing information
    score: float = 0.0         # Filter score
    filtered: bool = False      # Whether passed filtering

    def to_dict(self) -> dict:
        """Serialize to dictionary (for JSONL storage)"""
        data = asdict(self)
        # Convert datetime to ISO format string
        if isinstance(data['published_at'], datetime):
            data['published_at'] = data['published_at'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Item':
        """Deserialize from dictionary"""
        # Convert ISO format string to datetime
        if isinstance(data['published_at'], str):
            data['published_at'] = datetime.fromisoformat(data['published_at'])
        return cls(**data)

    @staticmethod
    def generate_id(source: str, content: str) -> str:
        """Generate unique ID from source and content"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"{source}:{content_hash}"


class DataSource(ABC):
    """Abstract base class for all data sources"""

    def __init__(self, config: dict):
        self.config = config
        self.source_name = self.get_source_name()
        self.channel = config.get('channel', 'general')

    @abstractmethod
    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """
        Fetch data and return unified Item list

        Args:
            hours_ago: Only fetch items from last N hours (None = all available)

        Returns:
            List[Item]: List of unified Item objects
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return unique data source identifier"""
        pass

    def is_enabled(self) -> bool:
        """Check if data source is enabled"""
        return self.config.get('enabled', True)

    def get_channel(self) -> str:
        """Return data source channel (for categorization)"""
        return self.channel

    def _make_item(
        self,
        native_id: str,
        title: str,
        text: str,
        url: str,
        author: str,
        published_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Item:
        """
        Create standardized Item object

        This helper ensures consistent item creation across all sources
        """
        # Ensure published_at is timezone-aware
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        # Generate unique ID
        item_id = Item.generate_id(self.source_name, f"{url}:{published_at.isoformat()}")

        # Truncate title
        title = title[:120] if len(title) > 120 else title

        return Item(
            id=item_id,
            source=self.source_name,
            channel=self.channel,
            title=title,
            text=text,
            url=url,
            author=author,
            published_at=published_at,
            metadata=metadata or {},
        )
