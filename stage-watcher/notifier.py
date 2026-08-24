"""
Envoi des notifications vers Telegram.

⚠️ PLACEHOLDER À TOI DE FAIRE (5 min, une seule fois) :
  1. Ouvre Telegram, cherche "@BotFather".
  2. Envoie /newbot, suis les instructions -> tu reçois un TOKEN
     (ressemble à "123456789:ABCdefGhIJKlmNoPQRstuVWXyz").
  3. Démarre une conversation avec TON NOUVEAU bot (cherche son
     @username, clique Start / envoie n'importe quel message).
  4. Récupère ton CHAT_ID :
       - va sur https://api.telegram.org/bot<TOKEN>/getUpdates
         (remplace <TOKEN> par le tien) dans un navigateur juste après
         avoir envoyé un message au bot
       - cherche "chat":{"id": XXXXXXXXX} dans la réponse JSON -> c'est
         ton CHAT_ID.
  5. Dans GitHub, va dans Settings > Secrets and variables > Actions
     de ton repo, et ajoute deux secrets :
       TELEGRAM_BOT_TOKEN = le token de l'étape 2
       TELEGRAM_CHAT_ID   = l'ID de l'étape 4
     (voir .github/workflows/daily_scrape.yml, ces secrets sont déjà
     référencés et injectés en variables d'environnement)
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

    On envoie un message par offre (pas un gros paquet) pour que chaque
    lien reste cliquable indépendamment et que tu puisses swiper/traiter
    une offre à la fois sur mobile.
    """
    if not jobs:
        print("[notifier] Aucune nouvelle offre à notifier.")
        return

    for job in jobs:
        msg = format_job_message(job["company"], job["source_label"], job["title"], job["url"])
        send_telegram_message(msg)

    print(f"[notifier] {len(jobs)} notification(s) envoyée(s).")
