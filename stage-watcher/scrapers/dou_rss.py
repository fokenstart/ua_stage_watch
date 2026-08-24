"""
Scraper DOU (jobs.dou.ua) — le cas le PLUS FACILE de tout le système.

DOU expose un vrai flux RSS par entreprise, confirmé en inspectant une page
entreprise (le lien "RSS" en bas de page pointe vers ce pattern) :

    https://jobs.dou.ua/vacancies/{slug}/feeds/

où {slug} est le nom de l'entreprise tel qu'il apparaît dans l'URL de sa
page (ex: "kpmg", "deloitte"). Pas besoin de scraping HTML, feedparser
suffit à tout extraire proprement.

Pour trouver le slug d'une nouvelle boîte : va sur
https://jobs.dou.ua/companies/ et cherche l'entreprise, le slug est dans
l'URL de sa page (jobs.dou.ua/companies/{slug}/).
"""

import feedparser

from .base import BaseScraper


class DouRssScraper(BaseScraper):
    source_type = "dou_rss"

    def fetch(self, source_config: dict) -> list[dict]:
        slug = source_config.get("slug")
        if not slug:
            print(f"[dou_rss] slug manquant dans la config: {source_config}")
            return []

        feed_url = f"https://jobs.dou.ua/vacancies/{slug}/feeds/"

        try:
            parsed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"[dou_rss] Erreur fetch {feed_url}: {e}")
            return []

        if parsed.bozo and not parsed.entries:
            # bozo=1 signifie souvent un flux mal formé ou une 404 déguisée.
            print(f"[dou_rss] Flux vide ou invalide pour slug='{slug}' "
                  f"({feed_url}) — vérifie que le slug est correct.")
            return []

        jobs = []
        for entry in parsed.entries:
            link = entry.get("link", "")
            native_id = link.rstrip("/").split("/")[-1] or self.hash_url(link)
            jobs.append({
                "native_id": native_id,
                "title": entry.get("title", "").strip(),
                "url": link,
            })

        return jobs
