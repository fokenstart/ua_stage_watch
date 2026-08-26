"""Contrat commun : chaque scraper retourne une liste de dicts
{native_id, title, url, platform}."""

from abc import ABC, abstractmethod
import hashlib


class BaseScraper(ABC):
    source_type: str = "base"

    @abstractmethod
    def fetch(self, source_config: dict) -> list[dict]:
        raise NotImplementedError

    @staticmethod
    def hash_url(url: str) -> str:
        return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
