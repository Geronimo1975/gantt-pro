"""
Helper utilities for Gantt Pro.
"""

from datetime import date, datetime, timedelta
from typing import Optional, List
import re


def format_date(d: Optional[date], fmt: str = "%Y-%m-%d") -> str:
    """Format a date object to string."""
    if d is None:
        return ""
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime(fmt)


def parse_date(s: str) -> Optional[date]:
    """Parse a string to date object."""
    if not s:
        return None

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue

    return None


def format_duration(days: int) -> str:
    """Format duration in days to human readable string."""
    if days == 0:
        return "0 days"
    elif days == 1:
        return "1 day"
    elif days < 7:
        return f"{days} days"
    elif days < 30:
        weeks = days // 7
        remaining = days % 7
        if remaining == 0:
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        return f"{weeks}w {remaining}d"
    else:
        months = days // 30
        remaining = days % 30
        if remaining == 0:
            return f"{months} month{'s' if months > 1 else ''}"
        return f"{months}m {remaining}d"


def calculate_business_days(start: date, end: date,
                            holidays: Optional[List[date]] = None) -> int:
    """Calculate business days between two dates."""
    if start > end:
        start, end = end, start

    holidays = set(holidays or [])
    business_days = 0
    current = start

    while current <= end:
        # Weekday is 0-4 for Monday-Friday
        if current.weekday() < 5 and current not in holidays:
            business_days += 1
        current += timedelta(days=1)

    return business_days


def add_business_days(start: date, days: int,
                      holidays: Optional[List[date]] = None) -> date:
    """Add business days to a date."""
    holidays = set(holidays or [])
    current = start
    added = 0

    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in holidays:
            added += 1

    return current


def generate_wbs(parent_wbs: str, index: int) -> str:
    """Generate WBS number for a subtask."""
    if not parent_wbs:
        return str(index)
    return f"{parent_wbs}.{index}"


def validate_wbs(wbs: str) -> bool:
    """Validate WBS format."""
    if not wbs:
        return False
    pattern = r'^\d+(\.\d+)*$'
    return bool(re.match(pattern, wbs))


def get_wbs_level(wbs: str) -> int:
    """Get the level of a WBS number."""
    if not wbs:
        return 0
    return len(wbs.split('.'))


def get_parent_wbs(wbs: str) -> Optional[str]:
    """Get parent WBS number."""
    if not wbs:
        return None
    parts = wbs.split('.')
    if len(parts) <= 1:
        return None
    return '.'.join(parts[:-1])


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def truncate(text: str, length: int = 50, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def progress_bar(progress: float, width: int = 20,
                 fill: str = "█", empty: str = "░") -> str:
    """Generate ASCII progress bar."""
    progress = max(0, min(100, progress))
    filled = int(width * progress / 100)
    bar = fill * filled + empty * (width - filled)
    return f"[{bar}] {progress:.1f}%"


def color_for_progress(progress: float) -> str:
    """Get color code for progress percentage."""
    if progress >= 100:
        return "green"
    elif progress >= 75:
        return "blue"
    elif progress >= 50:
        return "yellow"
    elif progress >= 25:
        return "orange"
    else:
        return "red"


def days_until(target: date) -> int:
    """Calculate days until a target date."""
    return (target - date.today()).days


def is_weekend(d: date) -> bool:
    """Check if date is weekend."""
    return d.weekday() >= 5


def get_week_range(d: date) -> tuple:
    """Get start and end of week for a date."""
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_month_range(d: date) -> tuple:
    """Get start and end of month for a date."""
    start = d.replace(day=1)
    if d.month == 12:
        end = d.replace(year=d.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
    return start, end
