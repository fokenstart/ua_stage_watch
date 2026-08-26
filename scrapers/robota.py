"""Scraper robota.ua — API publique, fallback HTML.

Filtre MVP :
  https://robota.ua/zapros/stazhuvannya/ukraine/params;rubrics=18,14
  14 = Консалтинг / Аналітика / Аудит
  18 = Банки / Інвестиції / Лізинг
"""

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper

API_SEARCH = "https://api.robota.ua/vacancy/search"
SITE_ORIGIN = "https://robota.ua"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
    "Origin": SITE_ORIGIN,
    "Referer": f"{SITE_ORIGIN}/zapros/stazhuvannya/ukraine/params;rubrics=18,14",
}
PAGE_SIZE = 40
MAX_PAGES = 8


class RobotaScraper(BaseScraper):
    source_type = "robota"

    def fetch(self, source_config: dict) -> list[dict]:
        label = source_config.get("label") or "robota.ua"
        keywords = source_config.get("keywords") or "стажування"
        rubrics = [int(x) for x in (source_config.get("rubrics") or [18, 14])]

        jobs = self._fetch_api(keywords, rubrics, label)
        if jobs:
            return jobs

        print("[robota] API vide/indisponible → fallback HTML")
        url = source_config.get("url") or (
            f"{SITE_ORIGIN}/zapros/stazhuvannya/ukraine/params;rubrics="
            + ",".join(str(r) for r in rubrics)
        )
        return self._fetch_html(url, label)

    def _fetch_api(self, keywords: str, rubrics: list[int], label: str) -> list[dict]:
        by_id: dict[str, dict] = {}
        for rubric in rubrics:
            page = 0
            while page < MAX_PAGES:
                try:
                    resp = requests.get(
                        API_SEARCH,
                        params={
                            "keyWords": keywords,
                            "parentId": rubric,
                            "count": PAGE_SIZE,
                            "page": page,
                        },
                        headers=HEADERS,
                        timeout=25,
                    )
                    resp.raise_for_status()
                    payload = resp.json()
                except Exception as exc:
                    print(f"[robota] API rubric={rubric} page={page}: {exc}")
                    break

                documents = payload.get("documents") or []
                if not documents:
                    break

                for doc in documents:
                    job = self._from_api_doc(doc, label)
                    if job:
                        by_id[job["native_id"]] = job

                total = payload.get("total") or 0
                if (page + 1) * PAGE_SIZE >= total:
                    break
                page += 1

        jobs = list(by_id.values())
        print(f"[robota] API: {len(jobs)} offre(s) (rubrics={rubrics})")
        return jobs

    def _from_api_doc(self, doc: dict, label: str) -> dict | None:
        vacancy_id = doc.get("id")
        title = (doc.get("name") or "").strip()
        if not vacancy_id or not title:
            return None
        company_id = doc.get("notebookId") or ""
        url = f"{SITE_ORIGIN}/company{company_id}/vacancy{vacancy_id}"
        return {
            "native_id": str(vacancy_id),
            "title": title,
            "url": url,
            "platform": label,
        }

    def _fetch_html(self, url: str, label: str) -> list[dict]:
        html_headers = dict(HEADERS)
        html_headers["Accept"] = "text/html,application/xhtml+xml"
        try:
            resp = requests.get(url, headers=html_headers, timeout=25)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"[robota] HTML fetch {url}: {exc}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        titles = soup.select("h2.santa-typo-h3")
        jobs = []
        seen = set()
        for heading in titles:
            title = heading.get_text(" ", strip=True)
            link = heading.find_parent("a", href=True)
            if link is None:
                link = heading.find_next("a", href=True)
            href = (link.get("href") if link else "") or ""
            if not title or not href or "/vacancy" not in href:
                continue
            full_url = href if href.startswith("http") else urljoin(SITE_ORIGIN, href)
            if full_url in seen:
                continue
            seen.add(full_url)
            jobs.append({
                "native_id": self.hash_url(full_url),
                "title": title,
                "url": full_url,
                "platform": label,
            })
        print(f"[robota] HTML: {len(jobs)} offre(s)")
        return jobs
