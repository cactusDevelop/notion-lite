"""
Remplacement de texte (PATCH 29).

Fonction pure, indépendante de Qt, construite sur les mêmes
catégories de blocs que la recherche globale (PATCH 28) :
texte/titres/citation/code, checklists, listes, et les deux moteurs
de tableau (PATCH 14 typé et PATCH 24 simple).

Dans le tableau typé (PATCH 15), seules les colonnes dont la valeur
est du texte simple sont concernées (texte, nombre, liste déroulante,
liste multiple, éléments d'une checklist imbriquée). Les colonnes
Personne sont volontairement exclues : les renommer doit passer par
le gestionnaire de personnes (PATCH 16) pour rester synchronisé avec
le registre partagé. Les colonnes Date/Durée/Booléen ne sont pas
textuelles et ne sont donc pas concernées.
"""
from __future__ import annotations

import re

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.heading_block import HeadingBlock
from blocks.list_block import ListBlock
from blocks.quote_block import QuoteBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import (
    COLUMN_TYPE_CHECKLIST,
    COLUMN_TYPE_MULTI_SELECT,
    COLUMN_TYPE_NUMBER,
    COLUMN_TYPE_SELECT,
    COLUMN_TYPE_TEXT,
    TableBlock,
)
from blocks.text_block import TextBlock
from core.document import Document

_TEXTUAL_COLUMN_TYPES = {
    COLUMN_TYPE_TEXT,
    COLUMN_TYPE_NUMBER,
    COLUMN_TYPE_SELECT,
}
_LIST_OF_TEXT_COLUMN_TYPES = {COLUMN_TYPE_MULTI_SELECT}


def _replace_in_text(text: str, pattern: re.Pattern, replacement: str) -> tuple[str, int]:
    count = len(pattern.findall(text))
    if count == 0:
        return text, 0
    return pattern.sub(lambda _match: replacement, text), count


def replace_all(document: Document, query: str, replacement: str) -> int:
    """Remplace toutes les occurrences (insensible à la casse) de
    `query` par `replacement` dans tout le document.

    Retourne le nombre total d'occurrences remplacées.
    """
    query = (query or "").strip()
    if not query:
        return 0
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    total = 0

    for block in document.blocks:
        if isinstance(block, (TextBlock, HeadingBlock, QuoteBlock, CodeBlock)):
            new_content, count = _replace_in_text(block.content, pattern, replacement)
            if count:
                block.content = new_content
                total += count
                if isinstance(block, TextBlock) and block.html:
                    # La mise en forme riche (PATCH 6) porte sur l'ancien
                    # texte : on l'efface plutôt que de la laisser
                    # désynchronisée du nouveau contenu.
                    block.html = ""

        elif isinstance(block, ChecklistBlock):
            for item in block.items:
                new_text, count = _replace_in_text(item.get("text", ""), pattern, replacement)
                if count:
                    item["text"] = new_text
                    total += count

        elif isinstance(block, ListBlock):
            for item in block.items:
                new_text, count = _replace_in_text(item.get("text", ""), pattern, replacement)
                if count:
                    item["text"] = new_text
                    total += count

        elif isinstance(block, TableBlock):
            total += _replace_in_table(block, pattern, replacement)

        elif isinstance(block, SimpleTableBlock):
            for row_index, row in enumerate(block.rows):
                for col_index, cell in enumerate(row):
                    new_cell, count = _replace_in_text(cell, pattern, replacement)
                    if count:
                        block.set_cell(row_index, col_index, new_cell)
                        total += count

    return total


def _replace_in_table(block: TableBlock, pattern: re.Pattern, replacement: str) -> int:
    total = 0
    for row in block.rows:
        for column in block.columns:
            col_type = column.get("type")
            value = block.get_cell(row["id"], column["id"])

            if col_type in _TEXTUAL_COLUMN_TYPES and isinstance(value, str):
                new_value, count = _replace_in_text(value, pattern, replacement)
                if count:
                    block.set_cell(row["id"], column["id"], new_value)
                    total += count

            elif col_type in _LIST_OF_TEXT_COLUMN_TYPES and isinstance(value, list):
                new_values = []
                changed = False
                for entry in value:
                    new_entry, count = _replace_in_text(str(entry), pattern, replacement)
                    if count:
                        changed = True
                        total += count
                    new_values.append(new_entry)
                if changed:
                    block.set_cell(row["id"], column["id"], new_values)

            elif col_type == COLUMN_TYPE_CHECKLIST and isinstance(value, list):
                changed = False
                for entry in value:
                    if not isinstance(entry, dict):
                        continue
                    new_text, count = _replace_in_text(entry.get("text", ""), pattern, replacement)
                    if count:
                        entry["text"] = new_text
                        changed = True
                        total += count
                if changed:
                    block.set_cell(row["id"], column["id"], value)

    return total
