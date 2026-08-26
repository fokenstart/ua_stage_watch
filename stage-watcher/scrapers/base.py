"""
Classe de base pour tous les scrapers.

Chaque scraper doit retourner une liste de dicts au format standard :
{
    "native_id": str,   # identifiant unique côté plateforme (ID interne, ou hash de l'URL si pas d'ID)
    "title": str,        # titre de l'offre
    "url": str,           # lien direct vers l'offre
}

Cette normalisation permet à main.py de traiter toutes les sources de façon
identique, quel que soit le type de plateforme derrière.
"""

from abc import ABC, abstractmethod
import hashlib


class BaseScraper(ABC):
    source_type: str = "base"  # à override dans chaque sous-classe

    @abstractmethod
    def fetch(self, source_config: dict) -> list[dict]:
        """
        Récupère les offres pour une source donnée.
        `source_config` = l'entrée YAML correspondante (url, slug, etc.)
        Doit toujours retourner une liste (vide si erreur/rien trouvé),
        jamais lever d'exception non gérée -> un scraper cassé ne doit
        pas faire planter tout le pipeline.
        """
        raise NotImplementedError

    @staticmethod
    def hash_url(url: str) -> str:
        """Fallback pour générer un ID stable quand la plateforme n'expose
        pas d'ID natif exploitable (on hash l'URL de l'offre elle-même)."""
        return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
