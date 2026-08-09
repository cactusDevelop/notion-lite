"""
Système de commandes "/" (PATCH 25).

Liste centralisée des commandes disponibles via le menu "/" façon
Notion. Chaque commande a un identifiant (matché sur `main_window`),
un nom affiché et un mot-clé de recherche.
"""
from __future__ import annotations

COMMANDS: list[dict[str, str]] = [
    {"id": "text", "label": "Texte", "keyword": "texte"},
    {"id": "heading1", "label": "Titre 1", "keyword": "titre1"},
    {"id": "heading2", "label": "Titre 2", "keyword": "titre2"},
    {"id": "heading3", "label": "Titre 3", "keyword": "titre3"},
    {"id": "checklist", "label": "Checklist", "keyword": "checklist"},
    {"id": "linked_checklist", "label": "Checklists liées", "keyword": "checklistsliees"},
    {"id": "table", "label": "Tableau", "keyword": "tableau"},
    {"id": "simple_table", "label": "Tableau simple", "keyword": "tableausimple"},
    {"id": "gantt", "label": "Gantt", "keyword": "gantt"},
    {"id": "image", "label": "Image", "keyword": "image"},
    {"id": "separator", "label": "Séparateur", "keyword": "separateur"},
    {"id": "quote", "label": "Citation", "keyword": "citation"},
    {"id": "code", "label": "Code", "keyword": "code"},
    {"id": "list", "label": "Liste", "keyword": "liste"},
]


def filter_commands(query: str) -> list[dict[str, str]]:
    """Filtre les commandes dont le libellé ou le mot-clé contient `query`."""
    query = (query or "").strip().lower()
    if not query:
        return list(COMMANDS)
    return [
        command
        for command in COMMANDS
        if query in command["keyword"] or query in command["label"].lower()
    ]
