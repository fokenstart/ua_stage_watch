"""
Scraper Jooble UA — page de résultats de recherche (agrégateur).

⚠️ PLACEHOLDER À VÉRIFIER : Jooble est un agrégateur (il republie des offres
d'autres sites, dont robota.ua/work.ua que tu couvres déjà directement).
Deux choses à savoir avant de configurer ce scraper :

  1. Risque de DOUBLONS : une offre Deloitte visible sur Jooble peut être
     la même que celle déjà captée via robota_html ou workua_html, mais
     avec un native_id différent -> tu recevras 2 notifs pour 1 seule
     offre. C'est un compromis acceptable (mieux vaut un doublon qu'une
     offre manquée) mais sache que ça arrivera.
  2. Jooble propose aussi une API officielle gratuite sur demande
     (https://jooble.org/api/about) — si tu veux une intégration plus
     propre à terme, ça vaut le coup de la demander plutôt que scraper
     le HTML.

Sélecteur ci-dessous à confirmer/ajuster comme pour les autres scrapers HTML.
"""

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper

JOB_LINK_SELECTOR = "a.b-result-inner__link"  # PLACEHOLDER à ajuster

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


class JoobleHtmlScraper(BaseScraper):
    source_type = "jooble_html"

    def fetch(self, source_config: dict) -> list[dict]:
        url = source_config.get("url")
        if not url:
            print(f"[jooble_html] 'url' manquant dans la config: {source_config}")
            return []

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[jooble_html] Erreur fetch {url}: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select(JOB_LINK_SELECTOR)

        if not links:
            print(f"[jooble_html] 0 offre trouvée sur {url} — "
                  f"vérifie/ajuste JOB_LINK_SELECTOR (voir en-tête du fichier).")
            return []

        jobs = []
        seen_hrefs = set()
        for link in links:
            href = link.get("href", "")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)

            title = link.get_text(strip=True)
            native_id = self.hash_url(href)

            if title:
                jobs.append({
                    "native_id": native_id,
                    "title": title,
                    "url": href,
                })

        return jobs
