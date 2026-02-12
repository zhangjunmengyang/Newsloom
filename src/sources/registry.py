"""Data source registry and management"""

from typing import List, Dict, Type
import yaml
from pathlib import Path
from .base import DataSource
from .rss import RSSSource


class SourceRegistry:
    """Data source registration and management"""

    # Map source types to implementation classes
    SOURCE_MAP: Dict[str, Type[DataSource]] = {
        'rss': RSSSource,
        # More sources will be added in Phase 2:
        # 'twitter': TwitterSource,
        # 'arxiv': ArxivSource,
        # 'github': GitHubSource,
        # 'hackernews': HackerNewsSource,
    }

    def __init__(self, sources_config_path: str):
        self.sources_config_path = Path(sources_config_path)
        self.sources_config = self._load_sources_config()

    def _load_sources_config(self) -> dict:
        """Load sources configuration from YAML"""
        if not self.sources_config_path.exists():
            raise FileNotFoundError(f"Sources config not found: {self.sources_config_path}")

        with open(self.sources_config_path) as f:
            config = yaml.safe_load(f)

        return config.get('sources', {})

    def get_enabled_sources(self) -> List[DataSource]:
        """Return all enabled data source instances"""
        enabled = []

        for source_name, source_config in self.sources_config.items():
            # Check if enabled
            if not source_config.get('enabled', False):
                continue

            # Get source type
            source_type = source_config.get('type')
            if not source_type:
                print(f"⚠️  Source '{source_name}' missing 'type' field, skipping")
                continue

            # Get implementation class
            source_class = self.SOURCE_MAP.get(source_type)
            if not source_class:
                print(f"⚠️  Unknown source type '{source_type}' for '{source_name}', skipping")
                continue

            # Create instance
            try:
                instance = source_class(source_config)
                enabled.append(instance)
            except Exception as e:
                print(f"⚠️  Failed to initialize '{source_name}': {e}")
                continue

        return enabled

    def register_source(self, source_type: str, source_class: Type[DataSource]):
        """Register a new data source type"""
        self.SOURCE_MAP[source_type] = source_class
