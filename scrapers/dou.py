"""
Scraper pour jobs.dou.ua — DIFFICULTÉ : FACILE

DOU expose un flux RSS natif pour chaque page "vacancies" d'entreprise.
Pas besoin de parser du HTML : feedparser fait tout le travail.

PLACEHOLDER À VÉRIFIER PAR TOI (une seule fois, pour chaque entreprise DOU) :
  L'URL du flux RSS suit généralement le format :
    https://jobs.dou.ua/companies/<slug>/vacancies/feed/
  mais DOU a changé son format d'URL par le passé. Pour vérifier :
    1. Ouvre la page vacancies de l'entreprise dans un navigateur
       (ex: https://jobs.dou.ua/companies/deloitte/vacancies/)
    2. Regarde le code source (Ctrl+U) et cherche une balise :
       <link rel="alternate" type="application/rss+xml" href="...">
    3. Si l'URL trouvée diffère du format ci-dessous, mets-la directement
       dans companies.yaml sous forme "feed_url_override" (voir fetch() ci-dessous).
"""

import feedparser
from .base import BaseScraper, Offer


class DouScraper(BaseScraper):
    platform_name = "dou"

    def fetch(self, company_slug: str, company_config: dict) -> list[Offer]:
        if not company_config:
            return []

        # Permet de forcer une URL de flux différente si le format standard ne marche pas
        # (PLACEHOLDER : ajoute "feed_url_override: ..." dans companies.yaml si besoin)
        feed_url = company_config.get("feed_url_override")

        if not feed_url:
            base_url = company_config["url"].rstrip("/")
            feed_url = f"{base_url}/feed/"

        parsed = feedparser.parse(feed_url)

        if parsed.bozo and not parsed.entries:
            # bozo=True signifie que le flux n'a pas pu être parsé correctement.
            # On ne lève pas d'exception ici : safe_fetch() logguera le souci en amont
            # si jamais entries reste vide alors qu'on attendait des résultats.
            print(f"[AVERTISSEMENT] Flux RSS DOU potentiellement invalide : {feed_url}")

        offers = []
        for entry in parsed.entries:
            offers.append(
                Offer(
                    id=entry.get("link", entry.get("id", entry.title)),
                    title=entry.title,
                    url=entry.get("link", ""),
                    company=company_slug,
                    platform=self.platform_name,
                    description=entry.get("summary", entry.title),
                )
            )
        return offers
