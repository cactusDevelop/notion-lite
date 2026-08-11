"""
Réglages globaux de l'application (PATCH 49, révisé PATCH 51).

Stockage simple en mémoire pour la durée de la session (même
approche que le thème courant dans ui.themes.theme, mais ces
réglages-ci sont indépendants de l'instance QApplication).
"""
from __future__ import annotations

# PATCH 51 — renommé (portée élargie aux tableaux/graphiques) et activé
# par défaut, suite au retour utilisateur.
_block_spacing = True

# PATCH 51 — sauvegarde automatique, activée par défaut dès qu'un
# document a été sauvegardé une première fois (voir main_window._maybe_autosave).
_autosave_enabled = True


def get_block_spacing() -> bool:
    """Espace supplémentaire au-dessus des titres/sous-titres, tableaux
    et graphiques, pour "laisser respirer" le document. Activable
    depuis le menu Affichage."""
    return _block_spacing


def set_block_spacing(value: bool) -> None:
    global _block_spacing
    _block_spacing = bool(value)


def get_autosave_enabled() -> bool:
    return _autosave_enabled


def set_autosave_enabled(value: bool) -> None:
    global _autosave_enabled
    _autosave_enabled = bool(value)
