"""
Gestion de l'état persistant : quelles offres ont déjà été notifiées.

Le fichier data/seen_jobs.json est commité dans le repo Git à chaque run
par la GitHub Action (voir .github/workflows/daily_watch.yml), ce qui sert
de "base de données" gratuite sans serveur externe.

Format du fichier :
{
  "job_ids": ["deloitte::dou::12345", "kpmg::workable::abcde", ...],
  "last_run": "2026-08-23T08:00:00Z"
}

Chaque ID est préfixé par "entreprise::source::id_natif" pour éviter les
collisions entre plateformes qui réutilisent parfois les mêmes IDs numériques.
"""

import json
import os
from datetime import datetime, timezone

STATE_PATH = os.path.join(os.path.dirname(__file__), "data", "seen_jobs.json")


def load_seen_ids() -> set:
    """Charge la liste des IDs déjà notifiés. Retourne un set vide si absent."""
    if not os.path.exists(STATE_PATH):
        return set()
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("job_ids", []))
    except (json.JSONDecodeError, OSError):
        # Fichier corrompu ou illisible -> on repart de zéro plutôt que de
        # planter tout le pipeline. On perd juste la dédup pour ce run.
        return set()


def save_seen_ids(all_ids: set) -> None:
    """Sauvegarde la liste complète des IDs vus (anciens + nouveaux)."""
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    payload = {
        "job_ids": sorted(all_ids),
        "last_run": datetime.now(timezone.utc).isoformat(),
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def make_job_id(company: str, source_type: str, native_id: str) -> str:
    """Construit un identifiant unique et stable pour une offre."""
    return f"{company}::{source_type}::{native_id}".lower()
