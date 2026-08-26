"""Bot Telegram — commande /stage.

    python bot.py

Lit TELEGRAM_BOT_TOKEN (et optionnellement TELEGRAM_CHAT_ID) depuis
l'environnement ou un fichier .env à la racine.
"""

from __future__ import annotations

import os
import time

import requests

from main import run_scrape
from notifier import send_html, send_stage_table
from store import mark_delivered, pending_jobs, stats

API = "https://api.telegram.org"
POLL_TIMEOUT = 25


def load_dotenv() -> None:
    path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def allowed_chat(chat_id: str) -> bool:
    expected = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    return not expected or str(chat_id) == expected


def handle_stage(token: str, chat_id: str) -> None:
    send_html(token, chat_id, "Mise à jour des offres…")
    summary = run_scrape()
    jobs = pending_jobs()
    if not jobs:
        if summary.get("total"):
            send_html(
                token,
                chat_id,
                f"Aucune nouvelle offre. Base : {summary['total']} stage(s) connu(s).",
            )
        else:
            send_html(token, chat_id, "Aucune offre trouvée pour le moment.")
        return

    send_stage_table(token, chat_id, jobs)
    mark_delivered([job["id"] for job in jobs])


def handle_start(token: str, chat_id: str) -> None:
    info = stats()
    send_html(
        token,
        chat_id,
        "Stage Watcher prêt.\n"
        "/stage — nouvelles offres (colonnes Titre | Source | LINK)\n"
        "Le 1er scrape constitue la base ; /stage n’envoie que ce qui est apparu après.\n"
        f"Base : {info['total']} offre(s), {info['pending']} nouvelle(s) non lue(s).",
    )


def process_update(token: str, update: dict) -> None:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()
    if not chat_id or not text:
        return
    if not allowed_chat(str(chat_id)):
        return
    cmd = text.split()[0].split("@")[0].lower()
    if cmd in ("/start", "/help"):
        handle_start(token, str(chat_id))
    elif cmd == "/stage":
        handle_stage(token, str(chat_id))


def run_bot() -> None:
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN manquant. Copie .env.example vers .env "
            "et renseigne le token BotFather."
        )

    requests.post(
        f"{API}/bot{token}/setMyCommands",
        json={
            "commands": [
                {"command": "start", "description": "Aide"},
                {"command": "stage", "description": "Nouvelles offres de stage"},
            ]
        },
        timeout=15,
    )

    offset = None
    print("[bot] en écoute — /stage")
    while True:
        try:
            params = {"timeout": POLL_TIMEOUT}
            if offset is not None:
                params["offset"] = offset
            resp = requests.get(
                f"{API}/bot{token}/getUpdates",
                params=params,
                timeout=POLL_TIMEOUT + 10,
            )
            resp.raise_for_status()
            updates = resp.json().get("result") or []
        except Exception as exc:
            print(f"[bot] poll: {exc}")
            time.sleep(3)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            try:
                process_update(token, update)
            except Exception as exc:
                print(f"[bot] update: {exc}")


def preview_table() -> None:
    """Affiche le tableau /stage dans le terminal (sans Telegram)."""
    jobs = pending_jobs()
    from notifier.formatters import format_stage_messages

    print(f"pending={len(jobs)} total={stats()['total']}")
    if not jobs:
        print("Aucune nouvelle offre à envoyer.")
        return
    for msg in format_stage_messages(jobs):
        print(msg)


if __name__ == "__main__":
    import sys

    if "--preview" in sys.argv:
        preview_table()
    else:
        run_bot()
