"""
Scraper pour sites carrière rendus en JavaScript (SPA) — Deloitte, PwC CEE,
EY font partie de cette catégorie d'après l'inspection initiale (leur HTML
brut ne contient aucune offre, tout est injecté après exécution du JS).

⚠️ CE FICHIER EST UN SQUELETTE NON ACTIVÉ PAR DÉFAUT.

Pourquoi ne pas l'activer directement : Playwright a besoin d'installer un
vrai navigateur headless (~300 Mo) dans l'environnement GitHub Actions, ce
qui alourdit et ralentit chaque run (10-20 sec de plus par site, contre
<1 sec pour du HTML statique). Ça reste largement faisable gratuitement sur
GitHub Actions, mais ce n'est pas activé par défaut pour garder le pipeline
rapide tant que ce n'est pas nécessaire.

MARCHE À SUIVRE POUR ACTIVER (quand tu es prêt) :
  1. Décommente la ligne d'installation Playwright dans
     .github/workflows/daily_watch.yml (étape Playwright à ajouter si besoin)
     commentaire, cherche "PLACEHOLDER: activer Playwright").
  2. Pour chaque site (Deloitte/PwC/EY), ouvre-le dans Chrome, DevTools
     (F12) > Network > XHR, recharge la page, et cherche si une requête
     JSON contient déjà la liste des offres. Si oui : c'est BIEN PLUS
     SIMPLE de copier cet endpoint dans un nouveau scraper type
     workable_api.py plutôt que d'utiliser Playwright. Vérifie ça EN
     PREMIER pour chaque site avant de passer à l'étape 3.
  3. Si vraiment aucun endpoint JSON n'est trouvable, adapte la fonction
     ci-dessous : remplace la config `wait_selector` par le sélecteur CSS
     qui apparaît UNE FOIS que les offres sont chargées sur la page (pour
     dire à Playwright "attends que ça soit là avant de lire le HTML").
  4. Ajoute une entrée dans scrapers/registry.py pour ce type ("html_js").
  5. Change `type: html_generic` en `type: html_js` dans companies.yaml
     pour la source concernée, avec les mêmes clés `url` et `selectors`
     que html_generic.py.

Dépendance à ajouter dans requirements.txt : playwright==1.47.0
Puis exécuter une fois (déjà géré dans le workflow si tu l'actives) :
    playwright install --with-deps chromium
"""

from .base import BaseScraper


class HtmlJsPlaywrightScraper(BaseScraper):
    source_type = "html_js"

    def fetch(self, source_config: dict) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[html_js] Playwright non installé. Ce scraper est "
                  "désactivé par défaut -> voir le commentaire en tête de "
                  "fichier pour l'activer (installer la dépendance + "
                  "décommenter l'étape dans le workflow GitHub Actions).")
            return []

        url = source_config.get("url")
        selectors = source_config.get("selectors")
        if not url or not selectors:
            print(f"[html_js] Config incomplète: {source_config}")
            return []

        wait_selector = selectors.get("wait_selector", "body")
        job_link_selector = selectors.get("job_link")
        if not job_link_selector:
            print(f"[html_js] 'selectors.job_link' manquant pour {url}")
            return []

        jobs = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url, timeout=30000)
                page.wait_for_selector(wait_selector, timeout=15000)

                links = page.query_selector_all(job_link_selector)
                seen_hrefs = set()
                for link in links:
                    href = link.get_attribute("href") or ""
                    title = (link.inner_text() or "").strip()
                    if not href or not title or href in seen_hrefs:
                        continue
                    seen_hrefs.add(href)
                    full_url = href if href.startswith("http") else url.rstrip("/") + "/" + href.lstrip("/")
                    jobs.append({
                        "native_id": self.hash_url(full_url),
                        "title": title,
                        "url": full_url,
                    })

                browser.close()
        except Exception as e:
            print(f"[html_js] Erreur Playwright sur {url}: {e}")
            return []

        return jobs
