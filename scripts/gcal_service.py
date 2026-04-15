"""Google Calendar service wrapper.

Uses a service account for authentication.
Requires GOOGLE_SERVICE_ACCOUNT_JSON env var pointing to the JSON key file.

Setup:
1. Create a Google Cloud project
2. Enable Google Calendar API
3. Create a service account + download JSON key
4. Share your Google Calendar with the service account email
5. Set GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/key.json
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/calendar"]
_service = None


def _get_service():
    """Lazy-init Google Calendar API service."""
    global _service
    if _service is not None:
        return _service

    json_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not json_path or not os.path.isfile(json_path):
        logger.warning(
            "GOOGLE_SERVICE_ACCOUNT_JSON not set or file not found. "
            "Calendar features disabled."
        )
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            json_path, scopes=_SCOPES
        )
        _service = build("calendar", "v3", credentials=creds)
        logger.info("Google Calendar service initialized")
        return _service
    except Exception:
        logger.exception("Failed to initialize Google Calendar service")
        return None


def _calendar_id() -> str:
    return os.getenv("GOOGLE_CALENDAR_ID", "primary")


def create_event(
    title: str,
    start: datetime,
    end: datetime | None = None,
    description: str = "",
) -> dict[str, Any] | None:
    """Create a calendar event. Returns the created event or None."""
    svc = _get_service()
    if svc is None:
        return None

    if end is None:
        end = start + timedelta(hours=1)

    event_body = {
        "summary": title,
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": "Asia/Seoul",
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": "Asia/Seoul",
        },
    }
    if description:
        event_body["description"] = description

    try:
        event = svc.events().insert(
            calendarId=_calendar_id(), body=event_body
        ).execute()
        logger.info("Created event: %s (%s)", event.get("summary"), event.get("id"))
        return event
    except Exception:
        logger.exception("Failed to create event: %s", title)
        return None


def list_events(
    time_min: datetime,
    time_max: datetime,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """List events in a time range."""
    svc = _get_service()
    if svc is None:
        return []

    try:
        result = svc.events().list(
            calendarId=_calendar_id(),
            timeMin=time_min.isoformat() + "+09:00",
            timeMax=time_max.isoformat() + "+09:00",
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        return result.get("items", [])
    except Exception:
        logger.exception("Failed to list events")
        return []


def delete_event_by_title(title_query: str) -> str | None:
    """Delete the first event matching the title query. Returns deleted event summary or None."""
    svc = _get_service()
    if svc is None:
        return None

    now = datetime.now()
    events = list_events(now, now + timedelta(days=30))

    for event in events:
        summary = event.get("summary", "")
        if title_query in summary:
            try:
                svc.events().delete(
                    calendarId=_calendar_id(),
                    eventId=event["id"],
                ).execute()
                logger.info("Deleted event: %s", summary)
                return summary
            except Exception:
                logger.exception("Failed to delete event: %s", summary)
                return None

    return None


def list_today() -> list[dict[str, Any]]:
    """List today's events."""
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = now + timedelta(days=1)
    return list_events(now, end)


def list_this_week() -> list[dict[str, Any]]:
    """List this week's events (Mon-Sun)."""
    now = datetime.now()
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = monday + timedelta(days=7)
    return list_events(monday, sunday)


def format_event(event: dict[str, Any]) -> str:
    """Format a single event for display."""
    summary = event.get("summary", "(제목 없음)")
    start_raw = event.get("start", {})

    if "dateTime" in start_raw:
        dt_str = start_raw["dateTime"][:16]  # "2026-04-15T10:00"
        try:
            dt = datetime.fromisoformat(dt_str)
            time_str = dt.strftime("%H:%M")
        except ValueError:
            time_str = dt_str
    elif "date" in start_raw:
        time_str = "종일"
    else:
        time_str = "?"

    return f"  {time_str} {summary}"
