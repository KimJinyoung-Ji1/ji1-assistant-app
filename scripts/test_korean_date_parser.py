"""Tests for korean_date_parser module."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, time, datetime
import korean_date_parser as kdp


def test_relative_dates():
    today = date(2026, 4, 15)
    assert kdp._parse_date("오늘 회의", today) == date(2026, 4, 15)
    assert kdp._parse_date("내일 10시", today) == date(2026, 4, 16)
    assert kdp._parse_date("모레 출장", today) == date(2026, 4, 17)
    assert kdp._parse_date("글피 미팅", today) == date(2026, 4, 18)
    print("  relative_dates: PASS")


def test_weekday():
    today = date(2026, 4, 15)  # Wednesday
    assert kdp._parse_date("이번주 금요일", today) == date(2026, 4, 17)
    assert kdp._parse_date("다음주 월요일", today) == date(2026, 4, 20)
    assert kdp._parse_date("다다음주 수요일", today) == date(2026, 4, 29)
    print("  weekday: PASS")


def test_absolute_dates():
    today = date(2026, 4, 15)
    assert kdp._parse_date("4/20 회의", today) == date(2026, 4, 20)
    assert kdp._parse_date("4월 20일 출장", today) == date(2026, 4, 20)
    assert kdp._parse_date("20일 미팅", today) == date(2026, 4, 20)
    assert kdp._parse_date("2026년 5월 1일", today) == date(2026, 5, 1)
    print("  absolute_dates: PASS")


def test_past_date_rolls_forward():
    today = date(2026, 4, 15)
    # 4/10 already passed -> next year
    assert kdp._parse_date("4/10 회의", today) == date(2027, 4, 10)
    # 10일 already passed -> next month
    assert kdp._parse_date("10일 미팅", today) == date(2026, 5, 10)
    print("  past_date_rolls_forward: PASS")


def test_time_parsing():
    assert kdp._parse_time("10시 회의") == time(10, 0)
    assert kdp._parse_time("오후 3시") == time(15, 0)
    assert kdp._parse_time("오전 9시 30분") == time(9, 30)
    assert kdp._parse_time("14:00 미팅") == time(14, 0)
    assert kdp._parse_time("14시 30분") == time(14, 30)
    assert kdp._parse_time("회의") is None
    print("  time_parsing: PASS")


def test_to_datetime():
    today = date(2026, 4, 15)
    dt = kdp.to_datetime("내일 10시 회의", today)
    assert dt == datetime(2026, 4, 16, 10, 0)

    dt = kdp.to_datetime("4/20 오후 3시 출장", today)
    assert dt == datetime(2026, 4, 20, 15, 0)

    # No time -> defaults to 09:00
    dt = kdp.to_datetime("내일 회의", today)
    assert dt == datetime(2026, 4, 16, 9, 0)

    # Nothing parseable
    assert kdp.to_datetime("그냥 텍스트", today) is None
    print("  to_datetime: PASS")


def test_format():
    dt = datetime(2026, 4, 15, 10, 0)  # Wednesday
    assert kdp.format_datetime_kr(dt) == "4/15(수) 10:00"
    print("  format: PASS")


if __name__ == "__main__":
    print("Testing korean_date_parser...")
    test_relative_dates()
    test_weekday()
    test_absolute_dates()
    test_past_date_rolls_forward()
    test_time_parsing()
    test_to_datetime()
    test_format()
    print("All tests passed!")
