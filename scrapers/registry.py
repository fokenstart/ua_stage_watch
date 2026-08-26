"""Associe le champ type: de config/sources.yaml au scraper.

Pour ajouter une plateforme :
  1. Crée scrapers/ma_plateforme.py (hérite de BaseScraper)
  2. Importe-la ici et ajoute-la à SCRAPER_REGISTRY
  3. Ajoute une entrée type: ma_plateforme dans config/sources.yaml
"""

from .robota import RobotaScraper

SCRAPER_REGISTRY = {
    "robota": RobotaScraper(),
}


def get_scraper(source_type: str):
    scraper = SCRAPER_REGISTRY.get(source_type)
    if scraper is None:
        print(f"[registry] Type inconnu: '{source_type}'")
    return scraper
