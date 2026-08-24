"""
Registre central : associe le champ `type:` de companies.yaml à la classe
de scraper correspondante.

POUR AJOUTER UN NOUVEAU TYPE DE PLATEFORME (ex: un job board pas encore
couvert) :
  1. Crée un nouveau fichier scrapers/mon_nouveau_scraper.py qui hérite de
     BaseScraper (voir scrapers/base.py pour le contrat à respecter).
  2. Importe-le ci-dessous et ajoute-le au dict SCRAPER_REGISTRY.
  3. Utilise ce `type:` dans companies.yaml.

Aucun autre fichier n'a besoin d'être modifié.
"""

from .dou_rss import DouRssScraper
from .workable_api import WorkableApiScraper
from .robota_html import RobotaHtmlScraper
from .workua_html import WorkUaHtmlScraper
from .jooble_html import JoobleHtmlScraper
from .html_generic import HtmlGenericScraper
from .html_js_playwright import HtmlJsPlaywrightScraper

SCRAPER_REGISTRY = {
    "dou_rss": DouRssScraper(),
    "workable_api": WorkableApiScraper(),
    "robota_html": RobotaHtmlScraper(),
    "workua_html": WorkUaHtmlScraper(),
    "jooble_html": JoobleHtmlScraper(),
    "html_generic": HtmlGenericScraper(),
    "html_js": HtmlJsPlaywrightScraper(),
}


def get_scraper(source_type: str):
    scraper = SCRAPER_REGISTRY.get(source_type)
    if scraper is None:
        print(f"[registry] Type de scraper inconnu: '{source_type}' — "
              f"vérifie l'orthographe dans companies.yaml ou ajoute-le "
              f"dans scrapers/registry.py")
    return scraper
