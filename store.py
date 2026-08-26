"""Base locale des offres (data/jobs.json), commitée par GitHub Actions."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

STORE_PATH = os.path.join(os.path.dirname(__file__), "data", "jobs.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty() -> dict:
    return {"baseline_done": False, "last_scrape": None, "jobs": {}}


def load_store() -> dict:
    if not os.path.exists(STORE_PATH):
        return _empty()
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        data.setdefault("baseline_done", False)
        data.setdefault("last_scrape", None)
        data.setdefault("jobs", {})
        return data
    except (json.JSONDecodeError, OSError):
        return _empty()


def save_store(data: dict) -> None:
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def make_job_id(platform_type: str, native_id: str) -> str:
    return f"{platform_type}::{native_id}".lower()


def upsert_jobs(fetched: list[dict], source_type: str) -> dict:
    """Intègre les offres scrapées.

    Premier run : constitue la base (rien n'est marqué 'nouveau').
    Runs suivants : les IDs inconnus deviennent disponibles pour /stage.
    """
    store = load_store()
    jobs = store["jobs"]
    first_run = not store.get("baseline_done")
    added = 0

    for item in fetched:
        native_id = item.get("native_id")
        title = (item.get("title") or "").strip()
        url = item.get("url") or ""
        if not native_id or not title or not url:
            continue
        job_id = make_job_id(source_type, native_id)
        if job_id in jobs:
            jobs[job_id]["title"] = title
            jobs[job_id]["url"] = url
            jobs[job_id]["platform"] = item.get("platform") or jobs[job_id].get("platform")
            continue
        jobs[job_id] = {
            "id": job_id,
            "native_id": str(native_id),
            "title": title,
            "url": url,
            "platform": item.get("platform") or source_type,
            "source_type": source_type,
            "first_seen": _now(),
            "is_new": not first_run,
            "delivered": first_run,
        }
        added += 1

    store["jobs"] = jobs
    store["baseline_done"] = True
    store["last_scrape"] = _now()
    save_store(store)
    print(
        f"[store] {'baseline' if first_run else 'update'}: "
        f"+{added} nouvelle(s), total={len(jobs)}"
    )
    return store


def pending_jobs() -> list[dict]:
    store = load_store()
    pending = [
        job for job in store.get("jobs", {}).values()
        if job.get("is_new") and not job.get("delivered")
    ]
    pending.sort(key=lambda j: j.get("first_seen") or "", reverse=True)
    return pending


def mark_delivered(job_ids: list[str]) -> None:
    store = load_store()
    jobs = store.get("jobs", {})
    for job_id in job_ids:
        if job_id in jobs:
            jobs[job_id]["delivered"] = True
    save_store(store)


def stats() -> dict:
    store = load_store()
    jobs = store.get("jobs", {})
    return {
        "total": len(jobs),
        "pending": len(pending_jobs()),
        "baseline_done": bool(store.get("baseline_done")),
        "last_scrape": store.get("last_scrape"),
    }
