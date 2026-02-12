"""Layer 1: Parallel data fetching"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
import json
from pathlib import Path

from sources.base import DataSource, Item
from utils.state import StateManager


class ParallelFetcher:
    """
    Parallel data scraper (inspired by morning-brief)
    Fetches from multiple sources concurrently
    """

    def __init__(self, sources: List[DataSource], state_manager: StateManager):
        self.sources = sources
        self.state = state_manager

    def fetch_all(self, hours_ago: Optional[int] = None) -> List[Item]:
        """
        Fetch data from all sources in parallel

        Args:
            hours_ago: Only fetch items from last N hours

        Returns:
            List of deduplicated Item objects
        """
        all_items = []

        print(f"\n📡 Fetching from {len(self.sources)} sources...")

        with ThreadPoolExecutor(max_workers=len(self.sources)) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self._fetch_source, src, hours_ago): src
                for src in self.sources
            }

            # Collect results
            for future in as_completed(futures):
                source = futures[future]
                try:
                    items = future.result(timeout=30)

                    # Deduplicate against state
                    new_items = [
                        item for item in items
                        if not self.state.is_seen(item.id)
                    ]

                    # Mark as seen
                    for item in new_items:
                        self.state.mark_seen(item.id)

                    all_items.extend(new_items)
                    print(f"  ✓ {source.source_name}: {len(new_items)} new items (total fetched: {len(items)})")

                except Exception as e:
                    print(f"  ✗ {source.source_name}: {e}")

        print(f"\n✅ Total new items: {len(all_items)}")
        return all_items

    def _fetch_source(self, source: DataSource, hours_ago: Optional[int]) -> List[Item]:
        """Fetch single data source (with error handling)"""
        return source.fetch(hours_ago=hours_ago)

    def save_raw_data(self, items: List[Item], output_path: Path):
        """Save raw fetched data to JSONL"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in items:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + '\n')

        print(f"💾 Saved raw data: {output_path}")

    def load_raw_data(self, input_path: Path) -> List[Item]:
        """Load raw data from JSONL"""
        items = []

        with open(input_path, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    items.append(Item.from_dict(data))

        return items
