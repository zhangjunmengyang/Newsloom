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
                    # Store item timestamps for cleanup
                    if 'item_timestamps' not in data:
                        data['item_timestamps'] = {}
                    return data
            except Exception as e:
                print(f"⚠️  Failed to load state: {e}, starting fresh")

        return {
            'seen_items': set(),
            'item_timestamps': {},  # item_id -> ISO timestamp
            'updated_at': None,
            'last_cleanup': None
        }

    def is_seen(self, item_id: str) -> bool:
        """Check if item has been seen before"""
        return item_id in self.state['seen_items']

    def mark_seen(self, item_id: str, timestamp: Optional[datetime] = None):
        """Mark item as seen with timestamp"""
        self.state['seen_items'].add(item_id)

        # Record timestamp for cleanup
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        self.state['item_timestamps'][item_id] = timestamp.isoformat()

    def save(self, auto_cleanup: bool = True):
        """Persist state to file with automatic cleanup"""
        # Create parent directory if needed
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Auto cleanup old records
        if auto_cleanup:
            self._auto_cleanup()

        # Convert set to list for JSON serialization
        data = {
            'seen_items': list(self.state['seen_items']),
            'item_timestamps': self.state.get('item_timestamps', {}),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'last_cleanup': self.state.get('last_cleanup')
        }

        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _auto_cleanup(self):
        """Automatically cleanup old records based on dedup_window_days"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.dedup_window_days)

        item_timestamps = self.state.get('item_timestamps', {})
        old_items = set()

        for item_id, timestamp_str in item_timestamps.items():
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if timestamp < cutoff:
                    old_items.add(item_id)
            except Exception:
                # If timestamp parsing fails, consider it old
                old_items.add(item_id)

        if old_items:
            # Remove from seen_items
            self.state['seen_items'] -= old_items

            # Remove from timestamps
            for item_id in old_items:
                item_timestamps.pop(item_id, None)

            self.state['last_cleanup'] = datetime.now(timezone.utc).isoformat()
            print(f"🧹 Auto-cleaned {len(old_items)} old items (older than {self.dedup_window_days} days)")

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
