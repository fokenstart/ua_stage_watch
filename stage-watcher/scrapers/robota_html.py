"""
Scraper robota.ua — page entreprise (ex: robota.ua/ua/company826651).

⚠️ PLACEHOLDER À VÉRIFIER (important) : robota.ua peut charger sa liste
d'offres via JavaScript selon les pages. Les sélecteurs CSS ci-dessous sont
une estimation raisonnable basée sur la structure habituelle des sites de
job board (liste de <a> avec un attribut href contenant "/vacancy/" ou
similaire) mais N'ONT PAS pu être vérifiés en conditions réelles.

Comment corriger si ça ne matche rien :
  1. Ouvre la page entreprise robota.ua dans ton navigateur
  2. Clic droit sur le titre d'une offre > "Inspecter"
  3. Repère la balise et sa classe CSS exacte (ex: <a class="vacancy-card-title" href="...">)
  4. Remplace JOB_LINK_SELECTOR ci-dessous par ce sélecteur CSS
  5. Si la liste reste vide après ça, c'est que le contenu est chargé en JS
     -> il faudra alors basculer ce scraper sur Playwright (voir README §3)
"""

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper

JOB_LINK_SELECTOR = "a[href*='/vacancy/']"  # PLACEHOLDER à ajuster
BASE_URL = "https://robota.ua"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


class RobotaHtmlScraper(BaseScraper):
    source_type = "robota_html"

    def fetch(self, source_config: dict) -> list[dict]:
        company_id = source_config.get("company_id")
        fallback_url = source_config.get("search_fallback_url")

        if company_id:
            url = f"{BASE_URL}/ua/company{company_id}"
        elif fallback_url:
            url = fallback_url
        else:
            print(f"[robota_html] Ni company_id ni search_fallback_url: {source_config}")
            return []

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[robota_html] Erreur fetch {url}: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select(JOB_LINK_SELECTOR)

        if not links:
            print(f"[robota_html] 0 offre trouvée sur {url} — "
                  f"le sélecteur '{JOB_LINK_SELECTOR}' ne matche probablement "
                  f"plus rien, ou le contenu est chargé en JS. Voir le "
                  f"commentaire en tête de fichier pour corriger.")
            return []

        jobs = []
        seen_hrefs = set()
        for link in links:
            href = link.get("href", "")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)

            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            title = link.get_text(strip=True)
            native_id = href.rstrip("/").split("/")[-1] or self.hash_url(full_url)

            if title:
                jobs.append({
                    "native_id": native_id,
                    "title": title,
                    "url": full_url,
                })

        return jobs
