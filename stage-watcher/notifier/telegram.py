"""
Notification Telegram — envoie chaque nouvelle offre détectée dans ton chat.
"""

import os
import requests
from scrapers.base import Offer

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_offers(offers: list) -> None:
    """Envoie un message Telegram par nouvelle offre détectée.
    Accepte une liste d'objets Offer OU de dictionnaires.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not offers:
        return

    # Normalisation : convertit les dictionnaires en objets Offer si besoin
    normalized_offers = []
    for item in offers:
        if isinstance(item, dict):
            normalized_offers.append(
                Offer(
                    company=item.get("company", ""),
                    platform=item.get("source_label", ""),
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    native_id="",
                )
            )
        else:
            normalized_offers.append(item)

    if not token or not chat_id:
        print(
            "[CONFIG MANQUANTE] TELEGRAM_BOT_TOKEN et/ou TELEGRAM_CHAT_ID absents. "
            "Les nouvelles offres ci-dessous n'ont PAS été envoyées sur Telegram :"
        )
        for offer in normalized_offers:
            print(f"  - [{offer.company}/{offer.platform}] {offer.title} -> {offer.url}")
        return

    for offer in normalized_offers:
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


# ALIAS : donne un 2ème nom à la fonction pour la rendre compatible avec main.py
send_batch = send_offers