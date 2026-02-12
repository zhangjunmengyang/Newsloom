"""Time utility functions"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def parse_time_ago(hours: int) -> datetime:
    """Get datetime N hours ago (UTC)"""
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def is_within_hours(dt: datetime, hours: int) -> bool:
    """Check if datetime is within last N hours"""
    cutoff = parse_time_ago(hours)
    # Ensure dt is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= cutoff


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return dt.strftime(fmt)


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime from ISO format string"""
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


def get_date_str(dt: Optional[datetime] = None) -> str:
    """Get date string in YYYY-MM-DD format"""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d")
