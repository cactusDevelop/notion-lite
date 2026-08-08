"""
Recherche globale (PATCH 28).

Fonction pure, indépendante de Qt : parcourt tous les blocs du
document et retourne les correspondances sous forme de
`SearchResult`, pour rester facilement testable sans interface
graphique. Couvre le texte (texte, titres, citation, code), les
checklists, les listes et les deux moteurs de tableau (PATCH 14 et
PATCH 24).
"""
from __future__ import annotations

from dataclasses import dataclass

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.heading_block import HeadingBlock
from blocks.list_block import ListBlock
from blocks.quote_block import QuoteBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import TableBlock
from blocks.text_block import TextBlock
from core.document import Document

_SNIPPET_RADIUS = 30


@dataclass(frozen=True)
class SearchResult:
    """Une correspondance : bloc concerné, où dans le bloc, et un extrait."""

    block_id: str
    block_type: str
    location: str
    snippet: str


def _make_snippet(text: str, query: str) -> str:
    """Extrait `text` autour de la première occurrence de `query`."""
    lowered = text.lower()
    index = lowered.find(query.lower())
    if index == -1:
        return text[: _SNIPPET_RADIUS * 2]
    start = max(0, index - _SNIPPET_RADIUS)
    end = min(len(text), index + len(query) + _SNIPPET_RADIUS)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


def search_document(document: Document, query: str) -> list[SearchResult]:
    """Recherche insensible à la casse dans tout le document."""
    query = (query or "").strip()
    if not query:
        return []
    lowered_query = query.lower()
    results: list[SearchResult] = []

    for block in document.blocks:
        if isinstance(block, (TextBlock, HeadingBlock, QuoteBlock, CodeBlock)):
            content = getattr(block, "content", "")
            if lowered_query in content.lower():
                results.append(
                    SearchResult(block.id, block.type, "Texte", _make_snippet(content, query))
                )

        elif isinstance(block, ChecklistBlock):
            for item in block.items:
                text = item.get("text", "")
                if lowered_query in text.lower():
                    results.append(
                        SearchResult(
                            block.id,
                            block.type,
                            "Checklist — élément",
                            _make_snippet(text, query),
                        )
                    )

        elif isinstance(block, ListBlock):
            for item in block.items:
                text = item.get("text", "")
                if lowered_query in text.lower():
                    results.append(
                        SearchResult(
                            block.id, block.type, "Liste — élément", _make_snippet(text, query)
                        )
                    )

        elif isinstance(block, TableBlock):
            for row in block.rows:
                for column in block.columns:
                    value = str(block.get_cell(row["id"], column["id"]) or "")
                    if lowered_query in value.lower():
                        column_name = column.get("name") or "sans nom"
                        results.append(
                            SearchResult(
                                block.id,
                                block.type,
                                f"Tableau — colonne « {column_name} »",
                                _make_snippet(value, query),
                            )
                        )

        elif isinstance(block, SimpleTableBlock):
            for row_index, row in enumerate(block.rows):
                for cell in row:
                    if lowered_query in cell.lower():
                        results.append(
                            SearchResult(
                                block.id,
                                block.type,
                                f"Tableau simple — ligne {row_index + 1}",
                                _make_snippet(cell, query),
                            )
                        )

    return results
