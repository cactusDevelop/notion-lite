"""
Système de commandes "/" (PATCH 25).

Liste centralisée des commandes disponibles via le menu "/" façon
Notion. Chaque commande a un identifiant (matché sur `main_window`),
un nom affiché et un mot-clé de recherche.

PATCH 80 : le libellé passe par `tr()` (voir ui.i18n) et est donc
recalculé à chaque appel de `get_commands()`/`filter_commands()`
plutôt que figé au chargement du module.
"""
from __future__ import annotations

from ui.i18n import tr

_COMMAND_DEFS: list[dict[str, str]] = [
    {"id": "text", "i18n_key": "command.text", "keyword": "texte"},
    {"id": "heading1", "i18n_key": "command.heading1", "keyword": "titre1"},
    {"id": "heading2", "i18n_key": "command.heading2", "keyword": "titre2"},
    {"id": "heading3", "i18n_key": "command.heading3", "keyword": "titre3"},
    {"id": "checklist", "i18n_key": "command.checklist", "keyword": "checklist"},
    {"id": "linked_checklist", "i18n_key": "command.linked_checklist", "keyword": "checklistsliees"},
    {"id": "table", "i18n_key": "command.table", "keyword": "tableau"},
    {"id": "simple_table", "i18n_key": "command.simple_table", "keyword": "tableausimple"},
    {"id": "gantt", "i18n_key": "command.gantt", "keyword": "gantt"},
    {"id": "dependency_gantt", "i18n_key": "command.dependency_gantt", "keyword": "planningdependances"},
    {"id": "line_chart", "i18n_key": "command.line_chart", "keyword": "courbes"},
    {"id": "bar_chart", "i18n_key": "command.bar_chart", "keyword": "batonnets"},
    {"id": "formula", "i18n_key": "command.formula", "keyword": "resultat"},
    {"id": "image", "i18n_key": "command.image", "keyword": "image"},
    {"id": "separator", "i18n_key": "command.separator", "keyword": "separateur"},
    {"id": "quote", "i18n_key": "command.quote", "keyword": "citation"},
    {"id": "code", "i18n_key": "command.code", "keyword": "code"},
    {"id": "list", "i18n_key": "command.list", "keyword": "liste"},
]


def get_commands() -> list[dict[str, str]]:
    """Retourne `_COMMAND_DEFS` avec le libellé traduit dans la langue
    courante (recalculé à chaque appel, contrairement à un ancien
    `COMMANDS` figé au chargement du module)."""
    return [
        {"id": c["id"], "label": tr(c["i18n_key"]), "keyword": c["keyword"]}
        for c in _COMMAND_DEFS
    ]


# Conservé pour compatibilité (code qui importait COMMANDS directement) :
# reflète la langue au moment de l'import du module.
COMMANDS: list[dict[str, str]] = get_commands()


def filter_commands(query: str) -> list[dict[str, str]]:
    """Filtre les commandes dont le libellé ou le mot-clé contient `query`."""
    commands = get_commands()
    query = (query or "").strip().lower()
    if not query:
        return commands
    return [
        command
        for command in commands
        if query in command["keyword"] or query in command["label"].lower()
    ]
