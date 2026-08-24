"""
Scraper pour les sites carrière hébergés sur Workable (ex: KPMG Ukraine).

⚠️ PLACEHOLDER À VÉRIFIER : la page https://apply.workable.com/kpmg-ukraine/
est une SPA (contenu chargé en JavaScript, le HTML brut est vide). Workable
expose un endpoint JSON interne non-officiel mais largement utilisé par les
outils de veille emploi :

    POST https://apply.workable.com/api/v3/accounts/{account}/jobs

Ce endpoint peut changer sans préavis (c'est une API privée, pas publique).
Si ce scraper renvoie une liste vide en continu, voici comment le réparer :
  1. Ouvre https://apply.workable.com/kpmg-ukraine/ dans Chrome/Firefox
  2. Ouvre les DevTools (F12) > onglet "Network" > filtre "Fetch/XHR"
  3. Recharge la page
  4. Cherche une requête qui retourne une liste de "jobs" en JSON
  5. Copie son URL exacte et sa méthode (GET/POST) ici, remplace
     WORKABLE_JOBS_ENDPOINT et WORKABLE_METHOD ci-dessous.
"""

import requests

from .base import BaseScraper

WORKABLE_JOBS_ENDPOINT = "https://apply.workable.com/api/v3/accounts/{account}/jobs"
WORKABLE_METHOD = "POST"  # PLACEHOLDER: à confirmer via DevTools si ça casse


class WorkableApiScraper(BaseScraper):
    source_type = "workable_api"

    def fetch(self, source_config: dict) -> list[dict]:
        account = source_config.get("account")
        if not account:
            print(f"[workable_api] 'account' manquant dans la config: {source_config}")
            return []

        endpoint = WORKABLE_JOBS_ENDPOINT.format(account=account)
        base_job_url = f"https://apply.workable.com/{account}/j/"

        try:
            if WORKABLE_METHOD == "POST":
                resp = requests.post(endpoint, json={}, timeout=15)
            else:
                resp = requests.get(endpoint, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[workable_api] Erreur fetch {endpoint}: {e}")
            print("[workable_api] -> Voir le commentaire en tête de fichier "
                  "pour retrouver le bon endpoint via DevTools.")
            return []

        raw_jobs = data.get("results", data.get("jobs", []))
        jobs = []
        for job in raw_jobs:
            shortcode = job.get("shortcode") or job.get("id")
            title = job.get("title", "").strip()
            if not shortcode or not title:
                continue
            jobs.append({
                "native_id": str(shortcode),
                "title": title,
                "url": f"{base_job_url}{shortcode}",
            })

        return jobs
