"""
Réglages globaux de l'application (PATCH 49).

Stockage simple en mémoire pour la durée de la session (même
approche que le thème courant dans ui.themes.theme, mais ces
réglages-ci sont indépendants de l'instance QApplication).
"""
from __future__ import annotations

_heading_extra_spacing = False


def get_heading_extra_spacing() -> bool:
    """Espacement supplémentaire au-dessus des titres/sous-titres,
    activable depuis le menu Affichage."""
    return _heading_extra_spacing


def set_heading_extra_spacing(value: bool) -> None:
    global _heading_extra_spacing
    _heading_extra_spacing = bool(value)
