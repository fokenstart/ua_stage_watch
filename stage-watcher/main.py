"""
Point d'entrée principal — orchestre tout le pipeline :

  1. Charge la config (companies.yaml)
  2. Pour chaque entreprise x chaque source : appelle le scraper concerné
  3. Filtre les offres par mots-clés (keyword_filter.py)
  4. Compare aux offres déjà notifiées (state.py)
  5. Envoie une notif Telegram pour chaque NOUVELLE offre (notifier.py)
  6. Sauvegarde le nouvel état

Exécuté automatiquement chaque jour par GitHub Actions
(.github/workflows/daily_scrape.yml), mais peut aussi tourner en local :

    pip install -r requirements.txt
    export TELEGRAM_BOT_TOKEN="..."
    export TELEGRAM_CHAT_ID="..."
    python main.py
"""

import os
import time
import yaml

from scrapers.registry import get_scraper
from keyword_filter import title_matches
from state import load_seen_ids, save_seen_ids, make_job_id
from notifier import send_batch

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "companies.yaml")

# Pause entre deux requêtes HTTP pour rester poli envers les serveurs cibles
# et limiter le risque de blocage IP. Ajustable si besoin.
DELAY_BETWEEN_REQUESTS_SECONDS = 2


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run() -> None:
    config = load_config()
    companies = config.get("companies", [])
    include_kw = config.get("keywords_include", [])
    exclude_kw = config.get("keywords_exclude", [])

    seen_ids = load_seen_ids()
    updated_ids = set(seen_ids)  # copie qu'on va enrichir au fil du run
    new_jobs_to_notify = []

    total_sources = sum(len(c.get("sources", [])) for c in companies)
    print(f"[main] Démarrage du run — {len(companies)} entreprise(s), "
          f"{total_sources} source(s) à interroger.")

    for company in companies:
        company_name = company.get("name", "INCONNU")

        for source in company.get("sources", []):
            source_type = source.get("type")
            source_label = source.get("label", source_type)

            scraper = get_scraper(source_type)
            if scraper is None:
                continue

            print(f"[main] -> {company_name} / {source_label} ...")

            try:
                jobs = scraper.fetch(source)
            except Exception as e:
                # Filet de sécurité ultime : un scraper qui plante ne doit
                # jamais interrompre le run entier pour les autres sources.
                print(f"[main] ERREUR inattendue sur {company_name}/{source_label}: {e}")
                jobs = []

            print(f"[main]    {len(jobs)} offre(s) brute(s) trouvée(s).")

            for job in jobs:
                title = job.get("title", "")

                if not title_matches(title, include_kw, exclude_kw):
                    continue  # ne correspond pas aux mots-clés de veille stage/junior

                job_id = make_job_id(company_name, source_type, job["native_id"])

                if job_id in seen_ids:
                    continue  # déjà notifié lors d'un run précédent

                updated_ids.add(job_id)
                new_jobs_to_notify.append({
                    "company": company_name,
                    "source_label": source_label,
                    "title": title,
                    "url": job["url"],
                })

            time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)

    print(f"[main] {len(new_jobs_to_notify)} nouvelle(s) offre(s) pertinente(s) détectée(s).")

    send_batch(new_jobs_to_notify)
    save_seen_ids(updated_ids)

    print("[main] Run terminé.")


if __name__ == "__main__":
    run()
