"""
Scraper pour robota.ua — DIFFICULTÉ : MOYENNE (scraping HTML)

robota.ua n'a pas d'API publique. La liste des offres est présente dans le HTML
statique de la page (pas besoin de JS pour l'affichage initial), donc un scraping
classique requests + BeautifulSoup fonctionne — mais les sélecteurs CSS ci-dessous
sont des PLACEHOLDERS À VALIDER car ils n'ont pas pu être vérifiés en conditions
réelles (structure exacte du DOM non inspectée en direct).

COMMENT VALIDER/CORRIGER LES SÉLECTEURS (une seule fois par plateforme, pas par entreprise) :
  1. Ouvre une page company robota.ua dans Chrome/Firefox
     (ex: https://robota.ua/ru/company567736)
  2. Clic droit sur le titre d'une offre listée > "Inspecter"
  3. Repère la balise et sa classe CSS (ex: <a class="santa-e-text ...">)
  4. Remplace OFFER_CARD_SELECTOR, TITLE_SELECTOR, LINK_SELECTOR ci-dessous
  5. Teste avec : python -m scrapers.robota (ajoute un bloc __main__ si besoin de debug)

NOTE : robota.ua peut charger une partie du contenu dynamiquement même si le
premier rendu est statique. Si le scraping renvoie 0 résultat alors que des offres
sont visibles au navigateur, c'est probablement le signe qu'il faut basculer sur
une approche Playwright (voir scrapers/base.py pour le pattern, à dupliquer).
"""

import requests
from bs4 import BeautifulSoup
from .base import BaseScraper, Offer

# =========== PLACEHOLDERS À VALIDER — voir docstring ci-dessus ===========
OFFER_CARD_SELECTOR = "div.santa-card"       # conteneur d'une offre individuelle
TITLE_LINK_SELECTOR = "a.santa-e-text"       # lien contenant le titre du poste
# ===========================================================================


class RobotaScraper(BaseScraper):
    platform_name = "robota"

    def fetch(self, company_slug: str, company_config: dict) -> list[Offer]:
        if not company_config:
            return []

        url = company_config["url"]
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except Exception as e:
            print(f"[ERREUR réseau robota.ua] {company_slug} : {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(OFFER_CARD_SELECTOR)

        if not cards:
            print(
                f"[AVERTISSEMENT] 0 offre trouvée pour {company_slug} sur robota.ua — "
                f"les sélecteurs CSS sont probablement à corriger (voir docstring du fichier)."
            )

        offers = []
        for card in cards:
            link_tag = card.select_one(TITLE_LINK_SELECTOR)
            if not link_tag:
                continue
            title = link_tag.get_text(strip=True)
            href = link_tag.get("href", "")
            full_url = href if href.startswith("http") else f"https://robota.ua{href}"

            offers.append(
                Offer(
                    id=full_url,   # l'URL complète sert d'ID unique et stable
                    title=title,
                    url=full_url,
                    company=company_slug,
                    platform=self.platform_name,
                    description=title,
                )
            )
        return offers
