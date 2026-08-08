"""
Aperçu textuel d'un bloc (PATCH 30).

Fonction pure (indépendante de Qt) utilisée par le sélecteur de blocs
des liens internes : donne un court texte représentatif du contenu
d'un bloc, quel que soit son type.
"""
from __future__ import annotations

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.gantt_block import GanttBlock
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.list_block import ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import TableBlock
from blocks.text_block import TextBlock

_MAX_PREVIEW_LENGTH = 60


def _truncate(text: str) -> str:
    text = " ".join(text.split())  # aplatit les retours à la ligne
    if len(text) <= _MAX_PREVIEW_LENGTH:
        return text
    return text[:_MAX_PREVIEW_LENGTH].rstrip() + "…"


def preview_for_block(block) -> str:
    """Court texte représentatif du contenu d'un bloc, pour l'afficher
    dans une liste (sélecteur de lien interne, résultats divers, ...)."""
    if isinstance(block, (TextBlock, HeadingBlock, QuoteBlock, CodeBlock)):
        return _truncate(block.content) or "(vide)"

    if isinstance(block, ChecklistBlock):
        if block.items:
            return _truncate(block.items[0].get("text", "")) or "(checklist)"
        return "(checklist vide)"

    if isinstance(block, ListBlock):
        if block.items:
            return _truncate(block.items[0].get("text", "")) or "(liste)"
        return "(liste vide)"

    if isinstance(block, TableBlock):
        return f"(tableau, {len(block.columns)} colonne{'s' if len(block.columns) != 1 else ''})"

    if isinstance(block, SimpleTableBlock):
        return f"(tableau simple, {block.row_count}×{block.column_count})"

    if isinstance(block, ImageBlock):
        return "(image)"

    if isinstance(block, GanttBlock):
        return "(diagramme de Gantt)"

    if isinstance(block, SeparatorBlock):
        return "(séparateur)"

    return "(bloc)"
