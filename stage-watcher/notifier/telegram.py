"""
Notification Telegram — envoie chaque nouvelle offre détectée dans ton chat.

PLACEHOLDER OBLIGATOIRE — SETUP TELEGRAM (à faire une seule fois, ~10 min) :

  1. Ouvre Telegram, cherche "@BotFather", envoie /newbot
  2. Suis les instructions (nom du bot, username se terminant par "bot")
  3. BotFather te donne un TOKEN du type "123456789:AAExxxxxxxxxxxxxxxxxxxx"
     -> à stocker comme secret GitHub Actions "TELEGRAM_BOT_TOKEN"

  4. Pour trouver ton CHAT_ID (l'ID de la conversation où recevoir les messages) :
     a. Envoie n'importe quel message à ton nouveau bot depuis ton compte Telegram
     b. Ouvre dans un navigateur :
        https://api.telegram.org/bot<TON_TOKEN>/getUpdates
     c. Cherche "chat":{"id": XXXXXXXXX, ...} dans la réponse JSON — ce nombre
        (potentiellement négatif si c'est un groupe) est ton CHAT_ID
     -> à stocker comme secret GitHub Actions "TELEGRAM_CHAT_ID"

  5. Les deux secrets sont lus automatiquement depuis les variables d'environnement
     ci-dessous — voir README.md pour la procédure d'ajout des secrets sur GitHub.
"""

import os
import requests
from scrapers.base import Offer

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_offers(offers: list[Offer]) -> None:
    """Envoie un message Telegram par nouvelle offre détectée."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print(
            "[CONFIG MANQUANTE] TELEGRAM_BOT_TOKEN et/ou TELEGRAM_CHAT_ID absents. "
            "Les nouvelles offres ci-dessous n'ont PAS été envoyées sur Telegram "
            "(voir docstring de telegram.py pour le setup) :"
        )
        for offer in offers:
            print(f"  - [{offer.company}/{offer.platform}] {offer.title} -> {offer.url}")
        return

    if not offers:
        return

    for offer in offers:
        text = (
            f"🆕 <b>{offer.company.upper()}</b> — {offer.platform}\n"
            f"{offer.title}\n"
            f"{offer.url}"
        )
        try:
            resp = requests.post(
                TELEGRAM_API_URL.format(token=token),
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )
            if resp.status_code != 200:
                print(f"[ERREUR Telegram] statut {resp.status_code} : {resp.text}")
        except Exception as e:
            print(f"[ERREUR Telegram] {e}")
