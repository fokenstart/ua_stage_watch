"""Scrape les sources configurées et met à jour data/jobs.json.

    python main.py
"""

import os
import time

import yaml

from scrapers.registry import get_scraper
from store import stats, upsert_jobs

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "sources.yaml")
DELAY_SECONDS = 1


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def run_scrape() -> dict:
    config = load_config()
    sources = config.get("sources") or []
    print(f"[main] scrape — {len(sources)} source(s)")

    for source in sources:
        source_type = source.get("type")
        scraper = get_scraper(source_type)
        if scraper is None:
            continue
        try:
            jobs = scraper.fetch(source)
        except Exception as exc:
            print(f"[main] erreur {source_type}: {exc}")
            jobs = []
        print(f"[main] {source.get('label', source_type)}: {len(jobs)} offre(s)")
        upsert_jobs(jobs, source_type)
        time.sleep(DELAY_SECONDS)

    summary = stats()
    print(
        f"[main] terminé — total={summary['total']} "
        f"pending={summary['pending']} last={summary['last_scrape']}"
    )
    return summary


if __name__ == "__main__":
    run_scrape()
