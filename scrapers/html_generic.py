"""
Scraper HTML générique — réutilisable pour n'importe quel site carrière
propre, TANT QU'IL EST STATIQUE (HTML généré côté serveur, pas de JS lourd).

⚠️ IMPORTANT : ce scraper ne fonctionnera PAS tel quel sur les sites
suivants, qui chargent leur contenu en JavaScript (SPA / frameworks type
React, Workday, SuccessFactors...) :
  - https://www2.deloitte.com/ua/uk/careers.html
  - https://jobs-cee.pwc.com/ua/ua/search-results
  - https://www.ey.com/uk_ua/careers/job-search

Pour CES sites, deux options (voir README §3 pour le détail) :
  A) Playwright headless (fiable mais plus lourd) — squelette fourni dans
     scrapers/html_js_playwright.py
  B) Trouver l'endpoint JSON caché appelé en coulisse par leur JS (souvent
     plus simple et rapide une fois trouvé) — méthode DevTools identique
     à celle décrite dans workable_api.py

Ce scraper générique reste utile pour :
  - de nouvelles boîtes hors Big4 dont le site carrière est simple/statique
  - si un des 3 sites ci-dessus change un jour d'architecture vers du HTML
    statique (ça arrive)

Configuration attendue dans companies.yaml pour ce type :
    selectors:
      job_link: "a.job-card"      # sélecteur CSS du lien vers l'offre
      title: null                  # optionnel: sélecteur du titre si != texte du lien
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .base import BaseScraper

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


class HtmlGenericScraper(BaseScraper):
    source_type = "html_generic"

    def fetch(self, source_config: dict) -> list[dict]:
        url = source_config.get("url")
        selectors = source_config.get("selectors")

        if not url:
            print(f"[html_generic] 'url' manquant dans la config: {source_config}")
            return []

        if not selectors:
            print(f"[html_generic] 'selectors' non renseigné pour {url} "
                  f"-> PLACEHOLDER non complété, source ignorée. "
                  f"Voir le commentaire en tête de fichier pour la marche à suivre "
                  f"(probablement un site JS -> Playwright nécessaire).")
            return []

        job_link_selector = selectors.get("job_link")
        title_selector = selectors.get("title")  # optionnel

        if not job_link_selector:
            print(f"[html_generic] 'selectors.job_link' manquant pour {url} "
                  f"-> source ignorée.")
            return []

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[html_generic] Erreur fetch {url}: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select(job_link_selector)

        if not links:
            print(f"[html_generic] 0 offre trouvée sur {url} avec le "
                  f"sélecteur '{job_link_selector}'.")
            return []

        jobs = []
        seen_hrefs = set()
        for link in links:
            href = link.get("href", "")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)

            full_url = urljoin(url, href)

            if title_selector:
                title_el = link.select_one(title_selector)
                title = title_el.get_text(strip=True) if title_el else ""
            else:
                title = link.get_text(strip=True)

            native_id = self.hash_url(full_url)

            if title:
                jobs.append({
                    "native_id": native_id,
                    "title": title,
                    "url": full_url,
                })

        return jobs
