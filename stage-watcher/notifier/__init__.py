"""
Envoi des notifications vers Telegram.

Sans TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, les messages sont imprimés
dans le terminal (mode local, zéro credential).
"""

import os
import requests

TELEGRAM_API_BASE = "https://api.telegram.org"


def send_telegram_message(text: str) -> bool:
    """Envoie un message texte au chat configuré. Retourne True si succès."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[notifier] TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquant "
              "dans les variables d'environnement -> notification ignorée.")
        print("[notifier] Message qui aurait été envoyé:\n" + text)
        return False

    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(url, data=payload, timeout=15)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[notifier] Échec envoi Telegram: {e}")
        return False


def format_job_message(company: str, source_label: str, title: str, url: str) -> str:
    """Formate une offre en message Telegram lisible avec lien cliquable."""
    return (
        f"🆕 <b>{company}</b> — {source_label}\n"
        f"{title}\n"
        f"<a href=\"{url}\">Voir l'offre</a>"
    )


def send_batch(jobs: list) -> None:
    """
    Envoie une notification par offre trouvée. `jobs` est une liste de dicts
    avec les clés: company, source_label, title, url.
    """
    if not jobs:
        print("[notifier] Aucune nouvelle offre à notifier.")
        return

    sent = 0
    for job in jobs:
        msg = format_job_message(
            job.get("company", ""),
            job.get("source_label", ""),
            job.get("title", ""),
            job.get("url", ""),
        )
        if send_telegram_message(msg):
            sent += 1

    if sent:
        print(f"[notifier] {sent} notification(s) envoyée(s).")
    else:
        print(f"[notifier] {len(jobs)} offre(s) à notifier, 0 envoi Telegram "
              f"(credentials absents ou API en échec).")
