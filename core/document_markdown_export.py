"""
Rendu Markdown du document (PATCH 37).

Fonction pure `document_to_markdown(document)` : traduit chaque bloc
en Markdown standard (GitHub-flavored pour les tableaux et cases à
cocher). Le bloc Texte riche (gras, italique...) est exporté en texte
brut : Markdown n'a pas d'équivalent direct pour toute la mise en
forme HTML supportée par TextBlock (PATCH 6) ; l'export PDF (PATCH 36)
reste la référence pour une fidélité complète.
"""
from __future__ import annotations

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.formula_block import FormulaBlock, compute_formula_result, format_formula_text
from blocks.bar_chart_block import BarChartBlock
from blocks.dependency_gantt_block import DependencyGanttBlock, compute_schedule
from blocks.line_chart_block import LineChartBlock, compute_line_series
from blocks.gantt_block import GanttBlock, compute_gantt_rows
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.linked_checklist_block import LinkedChecklistBlock
from blocks.list_block import LIST_TYPE_NUMBERED, ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import (
    COLUMN_TYPE_BOOLEAN,
    COLUMN_TYPE_CHECKLIST,
    COLUMN_TYPE_DATE,
    COLUMN_TYPE_DURATION,
    COLUMN_TYPE_MULTI_SELECT,
    COLUMN_TYPE_PERSON,
    TableBlock,
)
from blocks.text_block import TextBlock
from core.duration import format_duration


def _md_escape_cell(text: str) -> str:
    """Échappe le caractère "|" (séparateur de colonnes Markdown)."""
    return (text or "").replace("|", "\\|").replace("\n", " ")


def _render_table_cell(document, column: dict, value) -> str:
    col_type = column["type"]
    if value is None:
        return ""
    if col_type == COLUMN_TYPE_BOOLEAN:
        return "☑" if value else "☐"
    if col_type == COLUMN_TYPE_DURATION:
        return format_duration(value)
    if col_type == COLUMN_TYPE_DATE and isinstance(value, dict):
        return f"{value.get('start', '')} → {value.get('end', '')}"
    if col_type == COLUMN_TYPE_PERSON:
        names = [(document.find_person(pid) or {}).get("name", "?") for pid in (value or [])]
        return ", ".join(names)
    if col_type == COLUMN_TYPE_MULTI_SELECT:
        return ", ".join(value or [])
    if col_type == COLUMN_TYPE_CHECKLIST:
        done = sum(1 for item in (value or []) if item.get("checked"))
        return f"{done}/{len(value or [])}"
    return str(value)


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(_md_escape_cell(h) for h in headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"
    row_lines = [
        "| " + " | ".join(_md_escape_cell(cell) for cell in row) + " |" for row in rows
    ]
    return "\n".join([header_line, separator_line, *row_lines])


def _render_table_block(document, block: TableBlock) -> str:
    headers = [c["name"] or "" for c in block.columns]
    rows = [
        [_render_table_cell(document, column, row["cells"].get(column["id"])) for column in block.columns]
        for row in block.rows
    ]
    return _markdown_table(headers, rows)


def _render_simple_table_block(block: SimpleTableBlock) -> str:
    if not block.rows:
        return ""
    return _markdown_table(block.rows[0], block.rows[1:])


def _render_gantt_block(document, block: GanttBlock) -> str:
    rows = compute_gantt_rows(document, block)
    if not rows:
        return "*(Gantt vide ou non configuré)*"
    return _markdown_table(
        ["Tâche", "Début", "Fin"],
        [[r["label"], r["start"] or "", r["end"] or ""] for r in rows],
    )


def _render_dependency_gantt_block(document, block: DependencyGanttBlock) -> str:
    schedule = compute_schedule(document, block)
    if not schedule:
        return "*(Gantt par dépendances vide ou non configuré)*"
    return _markdown_table(
        ["Sous-tâche", "Personnes", "Début", "Fin", "Résolution"],
        [
            [t["label"], ", ".join(t["person_names"]), str(t["start"]), str(t["end"]), str(t["resolution"])]
            for t in schedule
        ],
    )


def _render_line_chart_block(document, block: LineChartBlock) -> str:
    series = compute_line_series(document, block)
    if not series:
        return f"**{block.title}** *(aucune série)*"
    table = _markdown_table(["Droite", "Pente"], [[s["name"], str(s["slope"])] for s in series])
    return f"**{block.title}**\n\n{table}"


def _render_bar_chart_block(block: BarChartBlock) -> str:
    if not block.bars:
        return f"**{block.title}** *(aucune barre)*"
    table = _markdown_table(["Catégorie", "Valeur"], [[b["label"], str(b["value"])] for b in block.bars])
    return f"**{block.title}** ({block.y_axis_label})\n\n{table}"


def _render_checklist_block(block: ChecklistBlock) -> str:
    return "\n".join(
        f"- [{'x' if item.get('checked') else ' '}] {item.get('text', '')}"
        for item in block.items
    )


def _render_linked_checklist_block(block: LinkedChecklistBlock) -> str:
    todo = "\n".join(f"- [ ] {item.get('text', '')}" for item in block.todo_items())
    done = "\n".join(f"- [x] {item.get('text', '')}" for item in block.done_items())
    parts = [p for p in ("**À faire**\n" + todo, "**Faites**\n" + done) if p.strip()]
    return "\n\n".join(parts)


def _render_list_block(block: ListBlock) -> str:
    if block.list_type == LIST_TYPE_NUMBERED:
        return "\n".join(f"{i + 1}. {item.get('text', '')}" for i, item in enumerate(block.items))
    return "\n".join(f"- {item.get('text', '')}" for item in block.items)


def _render_block(document, block) -> str:
    if isinstance(block, HeadingBlock):
        level = block.data.get("level", 1)
        return f"{'#' * level} {block.content}"
    if isinstance(block, TextBlock):
        return block.content
    if isinstance(block, ChecklistBlock):
        return _render_checklist_block(block)
    if isinstance(block, LinkedChecklistBlock):
        return _render_linked_checklist_block(block)
    if isinstance(block, ListBlock):
        return _render_list_block(block)
    if isinstance(block, TableBlock):
        return _render_table_block(document, block)
    if isinstance(block, SimpleTableBlock):
        return _render_simple_table_block(block)
    if isinstance(block, GanttBlock):
        return _render_gantt_block(document, block)
    if isinstance(block, DependencyGanttBlock):
        return _render_dependency_gantt_block(document, block)
    if isinstance(block, FormulaBlock):
        return format_formula_text(block, compute_formula_result(document, block))
    if isinstance(block, LineChartBlock):
        return _render_line_chart_block(document, block)
    if isinstance(block, BarChartBlock):
        return _render_bar_chart_block(block)
    if isinstance(block, ImageBlock):
        if not block.data.get("image_base64"):
            return "*(image vide)*"
        fmt = block.data.get("format", "png")
        return f"![](data:image/{fmt};base64,{block.data['image_base64']})"
    if isinstance(block, QuoteBlock):
        return "\n".join(f"> {line}" for line in (block.content or "").split("\n")) or "> "
    if isinstance(block, CodeBlock):
        return f"```{block.language if block.language != 'text' else ''}\n{block.content}\n```"
    if isinstance(block, SeparatorBlock):
        return "---"
    return ""


def document_to_markdown(document) -> str:
    """Convertit tout le document en Markdown, blocs séparés par une
    ligne vide (obligatoire pour que le rendu Markdown standard
    distingue correctement les blocs successifs, ex. deux tableaux)."""
    parts = [_render_block(document, block) for block in document.blocks]
    return "\n\n".join(part for part in parts if part)
