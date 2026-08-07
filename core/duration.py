"""
Système de durée (PATCH 17).

Une durée est représentée par {"amount": int, "unit": str}, avec
`unit` parmi DURATION_UNITS ("heures", "jours", "semaines") — voir
`blocks/table_block.py` (colonne "Durée", introduite au PATCH 15).

Ce module fournit le moteur indépendant de l'UI :
    - format_duration : représentation lisible ("2 semaines", "1 jour").
    - parse_duration_text : lecture d'une saisie libre ("2 semaines",
      "3h", "1j") vers {"amount", "unit"}.
    - to_hours : conversion en heures, pour comparer/additionner des
      durées d'unités différentes (utile à la vue Gantt du PATCH 19).

Conversion retenue (calendaire, pas en jours ouvrés) :
    1 jour = 24 heures, 1 semaine = 7 jours = 168 heures.
"""
from __future__ import annotations

import re
from typing import Optional

HOURS_PER_UNIT: dict[str, int] = {"heures": 1, "jours": 24, "semaines": 168}

# Alias reconnus en saisie libre, vers l'unité canonique.
_UNIT_ALIASES: dict[str, str] = {
    "h": "heures", "heure": "heures", "heures": "heures",
    "j": "jours", "jour": "jours", "jours": "jours",
    "s": "semaines", "sem": "semaines", "semaine": "semaines", "semaines": "semaines",
}

_PARSE_RE = re.compile(r"^\s*(\d+)\s*([a-zA-Zéèê]+)\s*$")


def format_duration(duration: dict) -> str:
    """Formate une durée en texte lisible, avec accord singulier/pluriel.

    Ex. : {"amount": 1, "unit": "jours"} -> "1 jour"
          {"amount": 2, "unit": "semaines"} -> "2 semaines"
    """
    amount = int(duration.get("amount", 0))
    unit = duration.get("unit", "jours")
    singular = {"heures": "heure", "jours": "jour", "semaines": "semaine"}.get(unit, unit)
    label = singular if amount == 1 else unit
    return f"{amount} {label}"


def parse_duration_text(text: str) -> Optional[dict]:
    """Interprète une saisie libre ("2 semaines", "3h", "1 j") en durée.

    Retourne None si le texte ne correspond à aucun format reconnu.
    """
    match = _PARSE_RE.match(text or "")
    if not match:
        return None
    amount_str, unit_str = match.groups()
    unit = _UNIT_ALIASES.get(unit_str.lower())
    if unit is None:
        return None
    return {"amount": int(amount_str), "unit": unit}


def to_hours(duration: dict) -> int:
    """Convertit une durée en nombre d'heures (base de comparaison commune)."""
    amount = int(duration.get("amount", 0))
    unit = duration.get("unit", "jours")
    return amount * HOURS_PER_UNIT.get(unit, HOURS_PER_UNIT["jours"])
