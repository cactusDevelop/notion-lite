"""
Système de thèmes (préparé au PATCH 1, implémenté ici) et mode sombre
complet (PATCH 32).

Approche retenue : style Qt "Fusion" + QPalette dédiée par thème.
Fusion est le seul style Qt qui respecte fidèlement la QPalette pour
TOUS les widgets standards (boutons, cases à cocher, listes, tables,
menus, champs de texte...), y compris ceux utilisés par les blocs
personnalisés (checklist, tableau, code, citation...) sans qu'il soit
nécessaire de maintenir une feuille de style QSS séparée par widget.
Basculer de thème revient donc simplement à changer la QPalette de
l'application, un point unique pour tout le programme.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

THEME_LIGHT = "light"
THEME_DARK = "dark"
THEMES: list[str] = [THEME_LIGHT, THEME_DARK]

_QSS_STYLE_NAME = "Fusion"


def _light_palette() -> QPalette:
    """Palette claire explicite (PATCH 32 correctif).

    Volontairement codée en dur plutôt que `QPalette()` : sur certains
    systèmes (ou IDE, ex. PyCharm) la palette Qt par défaut suit déjà
    le thème sombre de l'OS, ce qui rendait le thème "clair" à peine
    différent du thème sombre lors du basculement.
    """
    palette = QPalette()

    window = QColor(240, 240, 240)
    base = QColor(255, 255, 255)
    alternate_base = QColor(233, 233, 233)
    text = QColor(20, 20, 20)
    disabled_text = QColor(150, 150, 150)
    highlight = QColor(61, 132, 199)

    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, alternate_base)
    palette.setColor(QPalette.ToolTipBase, base)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, window)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, QColor(200, 0, 0))
    palette.setColor(QPalette.Link, highlight)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)

    return palette


def _dark_palette() -> QPalette:
    """Palette sombre complète : fond, texte, champs de saisie, sélection,
    infobulles, et états désactivés."""
    palette = QPalette()

    window = QColor(45, 45, 45)
    base = QColor(35, 35, 35)
    alternate_base = QColor(53, 53, 53)
    text = QColor(220, 220, 220)
    disabled_text = QColor(127, 127, 127)
    highlight = QColor(61, 132, 199)

    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, alternate_base)
    palette.setColor(QPalette.ToolTipBase, window)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, window)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, QColor(255, 80, 80))
    palette.setColor(QPalette.Link, highlight)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)

    return palette


def build_palette(theme_name: str) -> QPalette:
    """Construit la QPalette correspondant à `theme_name` (fonction pure,
    testable sans boucle d'événements)."""
    return _dark_palette() if theme_name == THEME_DARK else _light_palette()


def apply_theme(app: QApplication, theme_name: str) -> None:
    """Applique le thème à toute l'application (un seul point d'entrée)."""
    if theme_name not in THEMES:
        theme_name = THEME_LIGHT
    app.setStyle(_QSS_STYLE_NAME)
    app.setPalette(build_palette(theme_name))
    app.setProperty("notion_lite_theme", theme_name)


def current_theme(app: QApplication) -> str:
    """Thème actuellement appliqué (clair par défaut si jamais défini)."""
    return app.property("notion_lite_theme") or THEME_LIGHT


def toggle_theme(app: QApplication) -> str:
    """Bascule clair <-> sombre et retourne le nouveau thème."""
    new_theme = THEME_DARK if current_theme(app) == THEME_LIGHT else THEME_LIGHT
    apply_theme(app, new_theme)
    return new_theme
