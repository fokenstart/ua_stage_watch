"""Envoi Telegram (HTML)."""

import os

import requests

from .formatters import format_stage_messages

TELEGRAM_API_BASE = "https://api.telegram.org"


def send_html(token: str, chat_id: str, text: str) -> bool:
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            print(f"[telegram] {resp.status_code} {resp.text[:200]}")
            return False
        return True
    except requests.RequestException as exc:
        print(f"[telegram] {exc}")
        return False


def send_stage_table(token: str, chat_id: str, jobs: list[dict]) -> int:
    sent = 0
    for message in format_stage_messages(jobs):
        if send_html(token, chat_id, message):
            sent += 1
    return sent
