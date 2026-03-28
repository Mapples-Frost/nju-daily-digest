from __future__ import annotations

import re
from datetime import datetime
from time import struct_time
from zoneinfo import ZoneInfo


FULL_DATE_RE = re.compile(
    r"(?P<year>20\d{2}|19\d{2})[年/\-.](?P<month>\d{1,2})[月/\-.](?P<day>\d{1,2})"
    r"(?:[日号]?\s*(?P<hour>\d{1,2})[:时](?P<minute>\d{1,2})(?:[:分](?P<second>\d{1,2}))?)?"
)
MONTH_DAY_RE = re.compile(
    r"(?<!\d)(?P<month>\d{1,2})[月/\-.](?P<day>\d{1,2})(?:[日号]?\s*(?P<hour>\d{1,2})[:时](?P<minute>\d{1,2}))?"
)


def now_local(timezone_name: str) -> datetime:
    return datetime.now(ZoneInfo(timezone_name))


def parse_datetime(value: str | None, timezone_name: str) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d",
    ):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=ZoneInfo(timezone_name))
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ZoneInfo(timezone_name))
    return parsed.astimezone(ZoneInfo(timezone_name))


def format_datetime(dt: datetime | None, timezone_name: str) -> str:
    if dt is None:
        return ""
    return dt.astimezone(ZoneInfo(timezone_name)).strftime("%Y-%m-%d %H:%M:%S")


def extract_datetime_from_text(text: str | None, timezone_name: str) -> str | None:
    if not text:
        return None

    match = FULL_DATE_RE.search(text)
    if match:
        try:
            year = int(match.group("year"))
            month = int(match.group("month"))
            day = int(match.group("day"))
            hour = int(match.group("hour") or 0)
            minute = int(match.group("minute") or 0)
            second = int(match.group("second") or 0)
            dt = datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo(timezone_name))
            return dt.isoformat()
        except ValueError:
            pass

    match = MONTH_DAY_RE.search(text)
    if match:
        try:
            current_year = now_local(timezone_name).year
            month = int(match.group("month"))
            day = int(match.group("day"))
            hour = int(match.group("hour") or 0)
            minute = int(match.group("minute") or 0)
            dt = datetime(current_year, month, day, hour, minute, 0, tzinfo=ZoneInfo(timezone_name))
            return dt.isoformat()
        except ValueError:
            pass

    compact = re.search(r"(20\d{2})(\d{2})(\d{2})", text)
    if compact:
        try:
            dt = datetime(
                int(compact.group(1)),
                int(compact.group(2)),
                int(compact.group(3)),
                tzinfo=ZoneInfo(timezone_name),
            )
            return dt.isoformat()
        except ValueError:
            pass
    return None


def format_publish_text(published_at: str | None, timezone_name: str, fallback_prefix: str = "未提取到，按抓取时间归档") -> str:
    dt = parse_datetime(published_at, timezone_name)
    if dt is None:
        return f"{fallback_prefix}：{now_local(timezone_name).strftime('%Y-%m-%d')}"
    return dt.strftime("%Y-%m-%d %H:%M")


def sort_items(items: list[dict], timezone_name: str) -> list[dict]:
    def sort_key(item: dict) -> tuple[int, float]:
        dt = parse_datetime(item.get("published_at"), timezone_name)
        if dt is None:
            return (1, 0.0)
        return (0, -dt.timestamp())

    return sorted(items, key=sort_key)


def struct_time_to_iso(value: struct_time | None, timezone_name: str) -> str | None:
    if value is None:
        return None
    dt = datetime(
        value.tm_year,
        value.tm_mon,
        value.tm_mday,
        value.tm_hour,
        value.tm_min,
        value.tm_sec,
        tzinfo=ZoneInfo("UTC"),
    )
    return dt.astimezone(ZoneInfo(timezone_name)).isoformat()
