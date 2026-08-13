"""
Internationalisation de l'interface (PATCH 79).

Réglage de langue de session, même principe que `ui.settings`
(stockage en mémoire, pas de persistance entre lancements pour
l'instant). Seuls le français (langue par défaut, historique de
l'app) et l'anglais sont proposés pour le moment — d'autres langues
pourront être ajoutées à `LANGUAGES`/`_STRINGS` sans toucher au reste
du code, qui ne connaît que des clés (`tr("menu.file")`, ...).

Périmètre actuel des chaînes traduites : la barre de menu principale
(Fichier/Édition/Affichage) et son sous-menu "Langue". Le reste de
l'interface (barre d'outils, blocs, boîtes de dialogue) reste en
français pour l'instant et sera traduit progressivement.
"""
from __future__ import annotations

LANGUAGE_FR = "fr"
LANGUAGE_EN = "en"

# Ordre d'affichage dans le sous-menu "Langue".
LANGUAGES: dict[str, str] = {
    LANGUAGE_FR: "Français",
    LANGUAGE_EN: "English",
}

_language = LANGUAGE_FR

_STRINGS: dict[str, dict[str, str]] = {
    "menu.file": {"fr": "&Fichier", "en": "&File"},
    "menu.file.templates": {"fr": "Templates", "en": "Templates"},
    "menu.file.template_og": {"fr": "Modèle OG", "en": "OG template"},
    "menu.file.new_blank": {"fr": "Nouveau document vide", "en": "New blank document"},
    "menu.file.open": {"fr": "Ouvrir...", "en": "Open..."},
    "menu.file.save": {"fr": "Sauvegarder", "en": "Save"},
    "menu.file.save_as": {"fr": "Sauvegarder sous...", "en": "Save as..."},
    "menu.file.export_pdf": {"fr": "Exporter en PDF...", "en": "Export as PDF..."},
    "menu.edit": {"fr": "&Édition", "en": "&Edit"},
    "menu.edit.undo": {"fr": "Annuler", "en": "Undo"},
    "menu.edit.redo": {"fr": "Rétablir", "en": "Redo"},
    "menu.edit.search": {"fr": "Rechercher...", "en": "Find..."},
    "menu.edit.replace": {"fr": "Remplacer...", "en": "Replace..."},
    "menu.view": {"fr": "&Affichage", "en": "&View"},
    "menu.view.dark_mode": {"fr": "Mode sombre", "en": "Dark mode"},
    "menu.view.theme": {"fr": "Thème", "en": "Theme"},
    "menu.view.block_spacing": {
        "fr": "Espacer les titres, tableaux et graphiques",
        "en": "Add spacing above headings, tables and charts",
    },
    "menu.view.autosave": {"fr": "Sauvegarde automatique", "en": "Autosave"},
    "menu.view.explorer": {"fr": "Explorateur de fichiers", "en": "File explorer"},
    "menu.view.language": {"fr": "Langue", "en": "Language"},
}


def get_language() -> str:
    return _language


def set_language(language: str) -> None:
    global _language
    if language in LANGUAGES:
        _language = language


def tr(key: str) -> str:
    """Traduit `key` dans la langue courante. Repli sur le français
    (ou sur la clé elle-même) si `key` n'est pas encore traduite."""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_language) or entry.get(LANGUAGE_FR, key)
