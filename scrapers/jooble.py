"""
Scraper pour Jooble — DIFFICULTÉ : MOYENNE (API officielle, mais clé requise)

Contrairement à robota.ua/work.ua, Jooble propose une VRAIE API partenaire
gratuite mais nécessitant une inscription : https://jooble.org/api/about

PLACEHOLDER OBLIGATOIRE — ACTION DE TA PART :
  1. Va sur https://jooble.org/api/about et demande une clé API (gratuit,
     généralement délivrée rapidement par email)
  2. Une fois reçue, ajoute-la comme secret GitHub Actions nommé JOOBLE_API_KEY
     (voir .github/workflows/daily_watch.yml et README.md pour la procédure)
  3. Le script ci-dessous lira automatiquement la clé depuis la variable
     d'environnement JOOBLE_API_KEY — rien d'autre à modifier dans le code.

NOTE DE PRIORITÉ : comme mentionné dans nos échanges précédents, Jooble agrège
souvent des offres déjà présentes sur robota.ua/work.ua. Ce scraper est donc
un "bonus redondant" — active-le en dernier, une fois les autres validés.
"""

import os
import requests
from .base import BaseScraper, Offer

JOOBLE_API_URL = "https://jooble.org/api/{key}"


class JoobleScraper(BaseScraper):
    platform_name = "jooble"

    def fetch(self, company_slug: str, company_config: dict) -> list[Offer]:
        if not company_config:
            return []

        api_key = os.environ.get("JOOBLE_API_KEY")
        if not api_key:
            print(
                "[CONFIG MANQUANTE] JOOBLE_API_KEY absente des variables d'environnement — "
                "scraper Jooble ignoré (voir docstring de jooble.py pour l'obtenir)."
            )
            return []

        # Le nom de l'entreprise sert de terme de recherche via l'API Jooble
        search_term = company_config.get("search_term", company_slug)

        payload = {
            "keywords": search_term,
            "location": "Україна",
        }

        try:
            resp = requests.post(
                JOOBLE_API_URL.format(key=api_key),
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[ERREUR API Jooble] {company_slug} : {e}")
            return []

        offers = []
        for job in data.get("jobs", []):
            job_id = job.get("id") or job.get("link")
            offers.append(
                Offer(
                    id=str(job_id),
                    title=job.get("title", ""),
                    url=job.get("link", ""),
                    company=company_slug,
                    platform=self.platform_name,
                    description=job.get("snippet", job.get("title", "")),
                )
            )
        return offers
