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
THEME_SEPIA = "sepia"
THEME_HIGH_CONTRAST = "high_contrast"

# Ordre d'affichage dans le sous-menu "Thème" (PATCH 33) et de rotation
# de `cycle_theme`. `toggle_theme` (PATCH 32) reste un simple binaire
# clair/sombre, inchangé, pour ne pas casser son contrat existant.
THEMES: list[str] = [THEME_LIGHT, THEME_DARK, THEME_SEPIA, THEME_HIGH_CONTRAST]

THEME_LABELS: dict[str, str] = {
    THEME_LIGHT: "Clair",
    THEME_DARK: "Sombre",
    THEME_SEPIA: "Sépia",
    THEME_HIGH_CONTRAST: "Contraste élevé",
}

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


def _sepia_palette() -> QPalette:
    """Thème "Sépia" (PATCH 33) : fond chaud beige, confortable en
    lecture prolongée, à mi-chemin entre clair et sombre."""
    palette = QPalette()

    window = QColor(238, 227, 203)
    base = QColor(250, 243, 227)
    alternate_base = QColor(230, 216, 188)
    text = QColor(59, 44, 28)
    disabled_text = QColor(150, 135, 110)
    highlight = QColor(176, 122, 46)

    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, alternate_base)
    palette.setColor(QPalette.ToolTipBase, base)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, window)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, QColor(160, 40, 20))
    palette.setColor(QPalette.Link, highlight)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)

    return palette


def _high_contrast_palette() -> QPalette:
    """Thème "Contraste élevé" (PATCH 33) : noir/blanc pur et accent
    saturé, pour l'accessibilité (faible vision, luminosité ambiante
    difficile)."""
    palette = QPalette()

    window = QColor(0, 0, 0)
    base = QColor(0, 0, 0)
    alternate_base = QColor(30, 30, 30)
    text = QColor(255, 255, 255)
    disabled_text = QColor(160, 160, 160)
    highlight = QColor(255, 210, 0)

    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, alternate_base)
    palette.setColor(QPalette.ToolTipBase, window)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, window)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, QColor(255, 60, 60))
    palette.setColor(QPalette.Link, highlight)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)

    return palette


_PALETTE_BUILDERS: dict[str, "callable"] = {
    THEME_LIGHT: _light_palette,
    THEME_DARK: _dark_palette,
    THEME_SEPIA: _sepia_palette,
    THEME_HIGH_CONTRAST: _high_contrast_palette,
}


def build_palette(theme_name: str) -> QPalette:
    """Construit la QPalette correspondant à `theme_name` (fonction pure,
    testable sans boucle d'événements). Repli sur le thème clair si
    `theme_name` est inconnu."""
    builder = _PALETTE_BUILDERS.get(theme_name, _light_palette)
    return builder()


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
    """Bascule clair <-> sombre et retourne le nouveau thème (PATCH 32,
    contrat conservé tel quel : toujours binaire, indépendant des
    thèmes supplémentaires du PATCH 33)."""
    new_theme = THEME_DARK if current_theme(app) == THEME_LIGHT else THEME_LIGHT
    apply_theme(app, new_theme)
    return new_theme


def cycle_theme(app: QApplication) -> str:
    """PATCH 33 — Passe au thème suivant dans `THEMES` (boucle), pour
    parcourir l'ensemble des thèmes disponibles (pas seulement
    clair/sombre)."""
    current = current_theme(app)
    index = THEMES.index(current) if current in THEMES else 0
    new_theme = THEMES[(index + 1) % len(THEMES)]
    apply_theme(app, new_theme)
    return new_theme
