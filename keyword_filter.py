"""
Filtrage des offres par mots-clés — volontairement 100% déterministe
(pas de LLM, pas d'appel API tiers), pour rester gratuit, rapide et fiable.

Logique :
  1. L'offre est retenue si son titre contient AU MOINS un mot de
     `keywords_include` (insensible à la casse, insensible aux accents
     n'est PAS géré ici volontairement — l'ukrainien n'a pas d'accents
     à normaliser comme le français).
  2. Elle est rejetée si elle contient un mot de `keywords_exclude`,
     même si elle matchait un mot inclus.
"""

from typing import Iterable


def title_matches(title: str, include: Iterable[str], exclude: Iterable[str]) -> bool:
    if not title:
        return False

    title_lower = title.lower()
    include_list = [kw for kw in (include or []) if kw]
    exclude_list = [kw for kw in (exclude or []) if kw]

    if any(bad.lower() in title_lower for bad in exclude_list):
        return False

    # Liste include vide = aucun filtre d'inclusion (utile en test local).
    if not include_list:
        return True

    return any(good.lower() in title_lower for good in include_list)
