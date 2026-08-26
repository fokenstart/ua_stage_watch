"""Format Telegram : 3 colonnes Titre | Source | LINK."""

import html

MAX_MESSAGE = 3500
MAX_TITLE = 80


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def format_stage_messages(jobs: list[dict]) -> list[str]:
    if not jobs:
        return []

    header = "<b>Titre</b> | <b>Source</b> | <b>Lien</b>"
    rows = []
    for job in jobs:
        title = (job.get("title") or "").strip().replace("\n", " ")
        if len(title) > MAX_TITLE:
            title = title[: MAX_TITLE - 1] + "…"
        platform = job.get("platform") or job.get("source_type") or "?"
        url = job.get("url") or ""
        rows.append(
            f"{_esc(title)} | {_esc(platform)} | <a href=\"{_esc(url)}\">LINK</a>"
        )

    messages = []
    chunk = [header]
    size = len(header)
    for row in rows:
        extra = 1 + len(row)
        if size + extra > MAX_MESSAGE and len(chunk) > 1:
            messages.append("\n".join(chunk))
            chunk = [header, row]
            size = len(header) + extra
        else:
            chunk.append(row)
            size += extra
    messages.append("\n".join(chunk))
    return messages
