"""Korean date/time expression parser.

Parses natural Korean date and time expressions into datetime objects.
Examples:
    "내일 10시" -> tomorrow at 10:00
    "다음주 월요일 오후 3시" -> next Monday at 15:00
    "4/20 14시 30분" -> April 20 at 14:30
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from typing import NamedTuple


class ParsedDateTime(NamedTuple):
    date: date | None
    time: time | None


# Day-of-week mapping (Monday=0)
_WEEKDAY_MAP: dict[str, int] = {
    "월": 0, "월요일": 0,
    "화": 1, "화요일": 1,
    "수": 2, "수요일": 2,
    "목": 3, "목요일": 3,
    "금": 4, "금요일": 4,
    "토": 5, "토요일": 5,
    "일": 6, "일요일": 6,
}

# Relative date keywords
_RELATIVE_DATES: dict[str, int] = {
    "오늘": 0,
    "내일": 1,
    "모레": 2,
    "글피": 3,
}


def _parse_date(text: str, today: date | None = None) -> date | None:
    """Extract a date from Korean text."""
    today = today or date.today()

    # Relative: 오늘, 내일, 모레, 글피
    for keyword, delta in _RELATIVE_DATES.items():
        if keyword in text:
            return today + timedelta(days=delta)

    # "다음주 월요일" / "이번주 금요일"
    m = re.search(r"(이번\s*주|다음\s*주|다다음\s*주)\s*([월화수목금토일](?:요일)?)", text)
    if m:
        prefix, day_str = m.group(1).replace(" ", ""), m.group(2)
        target_weekday = _WEEKDAY_MAP.get(day_str)
        if target_weekday is not None:
            # Calendar-week based: find Monday of this week, then offset
            this_monday = today - timedelta(days=today.weekday())
            if "다다음" in prefix:
                return this_monday + timedelta(days=target_weekday + 14)
            elif "다음" in prefix:
                return this_monday + timedelta(days=target_weekday + 7)
            else:  # 이번주
                return this_monday + timedelta(days=target_weekday)

    # Bare weekday: "월요일 3시" (assumes this week, or next week if past)
    m = re.search(r"([월화수목금토일])(?:요일)?", text)
    if m and not re.search(r"\d", text[:m.start()]):
        target_weekday = _WEEKDAY_MAP.get(m.group(1))
        if target_weekday is not None:
            days_ahead = (target_weekday - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # next occurrence
            return today + timedelta(days=days_ahead)

    # "2026년 4월 20일" or "2026-04-20"
    m = re.search(r"(\d{4})\s*[-년.]\s*(\d{1,2})\s*[-월.]\s*(\d{1,2})(?:일)?", text)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # "4월 20일" or "4/20"
    m = re.search(r"(\d{1,2})\s*[월/.-]\s*(\d{1,2})(?:일)?", text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            target = date(today.year, month, day)
            # If date already passed this year, use next year
            if target < today:
                target = date(today.year + 1, month, day)
            return target

    # "20일" (day only, current or next month)
    m = re.search(r"(\d{1,2})일", text)
    if m:
        day = int(m.group(1))
        if 1 <= day <= 31:
            try:
                target = date(today.year, today.month, day)
                if target < today:
                    # next month
                    if today.month == 12:
                        target = date(today.year + 1, 1, day)
                    else:
                        target = date(today.year, today.month + 1, day)
                return target
            except ValueError:
                pass

    return None


def _parse_time(text: str) -> time | None:
    """Extract a time from Korean text."""
    # "14:00" or "14시 30분"
    m = re.search(r"(\d{1,2})\s*[:시]\s*(\d{1,2})(?:\s*분)?", text)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
    else:
        # "10시" (no minutes)
        m = re.search(r"(\d{1,2})\s*시", text)
        if m:
            hour, minute = int(m.group(1)), 0
        else:
            return None

    # Apply 오전/오후
    am_pm = re.search(r"(오전|오후)", text)
    if am_pm:
        period = am_pm.group(1)
        if period == "오후" and hour < 12:
            hour += 12
        elif period == "오전" and hour == 12:
            hour = 0

    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return time(hour, minute)
    return None


def parse_datetime(text: str, today: date | None = None) -> ParsedDateTime:
    """Parse Korean date/time expression.

    Returns ParsedDateTime with date and/or time components.
    Either may be None if not found in the text.
    """
    parsed_date = _parse_date(text, today)
    parsed_time = _parse_time(text)
    return ParsedDateTime(date=parsed_date, time=parsed_time)


def to_datetime(text: str, today: date | None = None) -> datetime | None:
    """Parse Korean expression into a full datetime.

    Returns None if no date could be parsed.
    Defaults to 09:00 if no time specified.
    Defaults to today if no date specified but time is given.
    """
    result = parse_datetime(text, today)
    if result.date is None and result.time is None:
        return None

    d = result.date or (today or date.today())
    t = result.time or time(9, 0)
    return datetime.combine(d, t)


def format_datetime_kr(dt: datetime) -> str:
    """Format datetime in Korean style: '4/20(월) 10:00'"""
    weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
    wd = weekday_names[dt.weekday()]
    return f"{dt.month}/{dt.day}({wd}) {dt.strftime('%H:%M')}"
