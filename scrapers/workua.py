"""
Scraper pour work.ua — DIFFICULTÉ : MOYENNE (scraping HTML)

Même logique que robota.py : pas d'API publique, mais HTML statique exploitable.
Sélecteurs CSS ci-dessous = PLACEHOLDERS À VALIDER (même procédure que robota.py,
en inspectant une page comme https://www.work.ua/en/jobs/by-company/1685297/).

IMPORTANT : les pages "recherche par mot-clé" (ex: EY sur work.ua qui utilise
https://www.work.ua/en/jobs-стажировка/ plutôt qu'une page company dédiée) renvoient
TOUTES les offres correspondant au mot-clé, pas seulement celles de l'entreprise visée.
Le paramètre filter_title_contains dans companies.yaml permet de ne garder que les
offres dont le titre/description mentionne l'entreprise — voir logique ci-dessous.
"""

import requests
from bs4 import BeautifulSoup
from .base import BaseScraper, Offer

# =========== PLACEHOLDERS À VALIDER — voir docstring ci-dessus ===========
OFFER_CARD_SELECTOR = "div.card.card-hover.card-visited.wordwrap"  # conteneur d'une offre
TITLE_LINK_SELECTOR = "h2 a"                                        # lien titre du poste
# ===========================================================================


class WorkUaScraper(BaseScraper):
    platform_name = "workua"

    def fetch(self, company_slug: str, company_config: dict) -> list[Offer]:
        if not company_config:
            return []

        url = company_config["url"]
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except Exception as e:
            print(f"[ERREUR réseau work.ua] {company_slug} : {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(OFFER_CARD_SELECTOR)

        if not cards:
            print(
                f"[AVERTISSEMENT] 0 offre trouvée pour {company_slug} sur work.ua — "
                f"sélecteurs CSS probablement à corriger (voir docstring du fichier)."
            )

        # Si cette page est une recherche par mot-clé générale (pas une page company
        # dédiée), on filtre sur la mention du nom de l'entreprise dans le texte.
        # PLACEHOLDER : ajoute "filter_title_contains: EY" dans companies.yaml
        # pour ce cas de figure (cf. commentaire dans companies.yaml pour EY).
        filter_term = company_config.get("filter_title_contains")

        offers = []
        for card in cards:
            link_tag = card.select_one(TITLE_LINK_SELECTOR)
            if not link_tag:
                continue
            title = link_tag.get_text(strip=True)
            href = link_tag.get("href", "")
            full_url = href if href.startswith("http") else f"https://www.work.ua{href}"

            if filter_term and filter_term.lower() not in title.lower():
                # Récupère aussi le texte de la carte entière pour un filtrage plus large
                card_text = card.get_text(" ", strip=True).lower()
                if filter_term.lower() not in card_text:
                    continue

            offers.append(
                Offer(
                    id=full_url,
                    title=title,
                    url=full_url,
                    company=company_slug,
                    platform=self.platform_name,
                    description=title,
                )
            )
        return offers
