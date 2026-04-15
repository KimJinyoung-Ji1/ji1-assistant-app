#!/usr/bin/env python3
"""Telegram schedule bot for ji1-assistant-app.

Monitors the schedule topic (thread_id=1520) in the ji1 Telegram group
and handles schedule/task commands in Korean.

Commands:
    일정 내일 10시 회의          -> Google Calendar event 등록
    할일 제안서 검토             -> Supabase tasks INSERT
    오늘 일정                   -> 오늘 캘린더 이벤트 조회
    이번주 일정                 -> 이번주 캘린더 이벤트 조회
    일정 삭제 회의              -> 제목 매칭으로 이벤트 삭제

Usage:
    pip install -r requirements.txt
    export TELEGRAM_BOT_TOKEN=...
    python schedule_bot.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

import korean_date_parser
import gcal_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# --- Configuration ---

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1003774600328")
THREAD_ID = int(os.environ.get("SCHEDULE_TOPIC_THREAD_ID", "1520"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
POLL_TIMEOUT = 30  # long polling timeout in seconds


# --- Telegram helpers ---

def _tg_api(method: str, payload: dict) -> dict | None:
    """Call Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        with urllib.request.urlopen(req, timeout=POLL_TIMEOUT + 10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error("Telegram API %s error %s: %s", method, e.code, body)
        return None
    except Exception:
        logger.exception("Telegram API %s failed", method)
        return None


def send_message(text: str, reply_to: int | None = None) -> dict | None:
    """Send a message to the schedule topic."""
    payload: dict = {
        "chat_id": CHAT_ID,
        "text": text,
        "message_thread_id": THREAD_ID,
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    return _tg_api("sendMessage", payload)


def get_updates(offset: int | None = None) -> list[dict]:
    """Long-poll for new messages."""
    payload: dict = {"timeout": POLL_TIMEOUT, "allowed_updates": ["message"]}
    if offset is not None:
        payload["offset"] = offset
    result = _tg_api("getUpdates", payload)
    if result and result.get("ok"):
        return result.get("result", [])
    return []


# --- Supabase helpers ---

def _supabase_post(table: str, data: dict) -> dict | None:
    """INSERT a row into a Supabase table via REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase not configured — skipping INSERT")
        return None

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Prefer": "return=representation",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        logger.exception("Supabase INSERT to %s failed", table)
        return None


def create_task(title: str, notes: str = "") -> bool:
    """Insert a task into Supabase tasks table."""
    result = _supabase_post("tasks", {
        "title": title,
        "status": "todo",
        "assignee": "김진영",
        "notes": notes,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
    })
    return result is not None


# --- Command handlers ---

def handle_add_schedule(text: str, msg_id: int) -> None:
    """Handle '일정 ...' command: parse date/time + create calendar event."""
    # Strip the "일정" prefix
    body = text[len("일정"):].strip()
    if not body:
        send_message("사용법: 일정 내일 10시 회의", reply_to=msg_id)
        return

    dt = korean_date_parser.to_datetime(body)
    if dt is None:
        send_message(f"날짜를 인식할 수 없습니다: {body}", reply_to=msg_id)
        return

    # Extract title: remove date/time tokens from the body
    title = _extract_title(body)
    if not title:
        title = body  # fallback: use the whole body as title

    event = gcal_service.create_event(title=title, start=dt)
    dt_str = korean_date_parser.format_datetime_kr(dt)

    if event:
        send_message(f"등록: {dt_str} {title}", reply_to=msg_id)
    else:
        # Calendar not configured — still acknowledge
        send_message(
            f"일정 파싱: {dt_str} {title}\n(캘린더 미연동 — 수동 등록 필요)",
            reply_to=msg_id,
        )


def handle_add_todo(text: str, msg_id: int) -> None:
    """Handle '할일 ...' command: create Supabase task."""
    body = text[len("할일"):].strip()
    if not body:
        send_message("사용법: 할일 제안서 검토", reply_to=msg_id)
        return

    ok = create_task(title=body, notes="텔레그램 일정봇에서 등록")
    if ok:
        send_message(f"할일 등록: {body}", reply_to=msg_id)
    else:
        send_message(
            f"할일 파싱: {body}\n(Supabase 미연동 — 수동 등록 필요)",
            reply_to=msg_id,
        )


def handle_list_today(msg_id: int) -> None:
    """Handle '오늘 일정' command."""
    events = gcal_service.list_today()
    if not events:
        send_message("오늘 일정이 없습니다.", reply_to=msg_id)
        return

    lines = [f"오늘 일정 ({len(events)}건):"]
    for ev in events:
        lines.append(gcal_service.format_event(ev))
    send_message("\n".join(lines), reply_to=msg_id)


def handle_list_week(msg_id: int) -> None:
    """Handle '이번주 일정' command."""
    events = gcal_service.list_this_week()
    if not events:
        send_message("이번주 일정이 없습니다.", reply_to=msg_id)
        return

    lines = [f"이번주 일정 ({len(events)}건):"]
    for ev in events:
        lines.append(gcal_service.format_event(ev))
    send_message("\n".join(lines), reply_to=msg_id)


def handle_delete_schedule(text: str, msg_id: int) -> None:
    """Handle '일정 삭제 ...' command."""
    body = text[len("일정 삭제"):].strip() if text.startswith("일정 삭제") else text[len("일정삭제"):].strip()
    if not body:
        send_message("사용법: 일정 삭제 회의", reply_to=msg_id)
        return

    deleted = gcal_service.delete_event_by_title(body)
    if deleted:
        send_message(f"삭제: {deleted}", reply_to=msg_id)
    else:
        send_message(f"'{body}' 일정을 찾을 수 없습니다.", reply_to=msg_id)


def _extract_title(body: str) -> str:
    """Extract the event title by removing date/time tokens from text."""
    import re
    # Remove known date/time patterns
    cleaned = body
    patterns = [
        r"오전|오후",
        r"다음\s*주|이번\s*주|다다음\s*주",
        r"[월화수목금토일]요일",
        r"\d{1,2}\s*[월/.-]\s*\d{1,2}(?:일)?",
        r"\d{1,2}\s*[:시]\s*\d{0,2}(?:\s*분)?",
        r"\d{1,2}시",
        r"\d{1,2}일",
        r"오늘|내일|모레|글피",
    ]
    for pat in patterns:
        cleaned = re.sub(pat, "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


# --- Main loop ---

def dispatch(text: str, msg_id: int) -> None:
    """Route a message to the appropriate handler."""
    text = text.strip()

    if text.startswith("일정 삭제") or text.startswith("일정삭제"):
        handle_delete_schedule(text, msg_id)
    elif text.startswith("일정"):
        handle_add_schedule(text, msg_id)
    elif text.startswith("할일"):
        handle_add_todo(text, msg_id)
    elif text in ("오늘 일정", "오늘일정"):
        handle_list_today(msg_id)
    elif text in ("이번주 일정", "이번주일정", "금주 일정"):
        handle_list_week(msg_id)
    else:
        # Unknown command — silently ignore non-command messages
        pass


def main() -> None:
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    logger.info(
        "Schedule bot started (chat_id=%s, thread_id=%s)", CHAT_ID, THREAD_ID
    )

    # Check optional services
    if not SUPABASE_URL:
        logger.warning("SUPABASE_URL not set — task creation disabled")
    if not os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
        logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON not set — calendar disabled")

    offset = None
    consecutive_errors = 0

    while True:
        try:
            updates = get_updates(offset)
            consecutive_errors = 0

            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message")
                if not msg:
                    continue

                # Filter: only messages from the schedule topic
                if msg.get("message_thread_id") != THREAD_ID:
                    continue

                text = msg.get("text", "")
                if not text:
                    continue

                msg_id = msg["message_id"]
                logger.info("Received: %s (from %s)", text, msg.get("from", {}).get("first_name", "?"))

                try:
                    dispatch(text, msg_id)
                except Exception:
                    logger.exception("Error handling message: %s", text)
                    send_message("처리 중 오류가 발생했습니다.", reply_to=msg_id)

        except KeyboardInterrupt:
            logger.info("Shutting down")
            break
        except Exception:
            consecutive_errors += 1
            logger.exception("Polling error (#%d)", consecutive_errors)
            if consecutive_errors >= 10:
                logger.error("Too many consecutive errors, exiting")
                sys.exit(1)
            time.sleep(min(consecutive_errors * 2, 30))


if __name__ == "__main__":
    main()
