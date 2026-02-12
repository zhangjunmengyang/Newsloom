"""State manager for deduplication and persistence"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Set, Optional


class StateManager:
    """
    State management for cross-run deduplication
    Inspired by twitter-watchdog's state management
    """

    def __init__(self, state_file: Path, dedup_window_days: int = 7):
        self.state_file = Path(state_file)
        self.dedup_window_days = dedup_window_days
        self.state = self._load()

    def _load(self) -> dict:
        """Load state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                    # Convert list back to set
                    data['seen_items'] = set(data.get('seen_items', []))
                    return data
            except Exception as e:
                print(f"⚠️  Failed to load state: {e}, starting fresh")

        return {
            'seen_items': set(),
            'updated_at': None,
            'last_cleanup': None
        }

    def is_seen(self, item_id: str) -> bool:
        """Check if item has been seen before"""
        return item_id in self.state['seen_items']

    def mark_seen(self, item_id: str):
        """Mark item as seen"""
        self.state['seen_items'].add(item_id)

    def save(self):
        """Persist state to file"""
        # Create parent directory if needed
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert set to list for JSON serialization
        data = {
            'seen_items': list(self.state['seen_items']),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'last_cleanup': self.state.get('last_cleanup')
        }

        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

    def cleanup_old_items(self, item_timestamps: dict):
        """
        Remove old items from seen_items set based on dedup window

        Args:
            item_timestamps: dict mapping item_id -> timestamp (datetime)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.dedup_window_days)

        old_items = {
            item_id for item_id in self.state['seen_items']
            if item_id in item_timestamps and item_timestamps[item_id] < cutoff
        }

        self.state['seen_items'] -= old_items
        self.state['last_cleanup'] = datetime.now(timezone.utc).isoformat()

        if old_items:
            print(f"🧹 Cleaned up {len(old_items)} old items from state")

    def get_stats(self) -> dict:
        """Get state statistics"""
        return {
            'total_seen': len(self.state['seen_items']),
            'updated_at': self.state.get('updated_at'),
            'last_cleanup': self.state.get('last_cleanup')
        }
