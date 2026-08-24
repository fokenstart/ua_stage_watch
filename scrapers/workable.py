"""
Scraper pour sites carrière hébergés sur Workable (ex: KPMG Ukraine) — DIFFICULTÉ : FACILE

Workable expose une API JSON publique non documentée officiellement mais stable
et largement utilisée par la communauté : https://apply.workable.com/api/v3/accounts/<slug>/jobs

PLACEHOLDER À CONFIRMER PAR TOI :
  Le "account_slug" dans companies.yaml (actuellement "kpmg-ukraine" en best guess).
  Méthode de vérification :
    1. Ouvre https://apply.workable.com/<slug>/ dans un navigateur
    2. Si la page liste des offres normalement, le slug est bon
    3. Sinon : F12 > onglet Network > filtre "Fetch/XHR" > recharge la page
       > cherche une requête vers .../api/v3/accounts/XXXX/jobs > XXXX est le vrai slug
"""

import requests
from .base import BaseScraper, Offer


class WorkableScraper(BaseScraper):
    platform_name = "workable"

    API_TEMPLATE = "https://apply.workable.com/api/v3/accounts/{slug}/jobs"

    def fetch(self, company_slug: str, company_config: dict) -> list[Offer]:
        if not company_config:
            return []

        account_slug = company_config.get("account_slug")
        if not account_slug:
            print(f"[CONFIG MANQUANTE] account_slug absent pour {company_slug} (workable)")
            return []

        url = self.API_TEMPLATE.format(slug=account_slug)
        # Workable attend parfois une requête POST avec un body JSON vide plutôt qu'un GET simple
        # selon la version de l'API — si le GET échoue (ex: 405), essaie POST en fallback.
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                resp = requests.post(url, timeout=15, json={}, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[ERREUR API Workable] {company_slug} : {e}")
            return []

        offers = []
        for job in data.get("results", []):
            job_id = job.get("shortcode") or job.get("id")
            title = job.get("title", "")
            job_url = f"https://apply.workable.com/{account_slug}/j/{job_id}/"
            offers.append(
                Offer(
                    id=str(job_id),
                    title=title,
                    url=job_url,
                    company=company_slug,
                    platform=self.platform_name,
                    description=title,
                )
            )
        return offers
