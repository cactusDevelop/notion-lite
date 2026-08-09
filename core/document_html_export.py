"""
Rendu HTML du document (PATCH 36 — support de l'export PDF).

Fonction pure `document_to_html(document)` : traduit chaque bloc en un
fragment HTML autonome (indépendant de Qt, testable sans QApplication).
`ui/export_pdf.py` réutilise ce HTML avec QTextDocument + QPrinter
pour produire le fichier PDF final.
"""
from __future__ import annotations

import html as html_module

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.formula_block import FormulaBlock, compute_formula_result, format_formula_text
from blocks.gantt_block import GanttBlock, compute_gantt_rows
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.linked_checklist_block import LinkedChecklistBlock
from blocks.list_block import LIST_TYPE_NUMBERED, ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import COLUMN_TYPE_BOOLEAN, COLUMN_TYPE_CHECKLIST, COLUMN_TYPE_DATE, COLUMN_TYPE_DURATION, COLUMN_TYPE_MULTI_SELECT, COLUMN_TYPE_PERSON, TableBlock
from blocks.text_block import TextBlock
from core.duration import format_duration


def _esc(text: str) -> str:
    return html_module.escape(text or "")


def _render_table_cell(document, column: dict, value) -> str:
    col_type = column["type"]
    if value is None:
        return ""
    if col_type == COLUMN_TYPE_BOOLEAN:
        return "☑" if value else "☐"
    if col_type == COLUMN_TYPE_DURATION:
        return _esc(format_duration(value))
    if col_type == COLUMN_TYPE_DATE and isinstance(value, dict):
        return _esc(f"{value.get('start', '')} → {value.get('end', '')}")
    if col_type == COLUMN_TYPE_PERSON:
        names = [(document.find_person(pid) or {}).get("name", "?") for pid in (value or [])]
        return _esc(", ".join(names))
    if col_type == COLUMN_TYPE_MULTI_SELECT:
        return _esc(", ".join(value or []))
    if col_type == COLUMN_TYPE_CHECKLIST:
        done = sum(1 for item in (value or []) if item.get("checked"))
        return _esc(f"{done}/{len(value or [])}")
    return _esc(str(value))


def _render_table_block(document, block: TableBlock) -> str:
    header = "".join(f"<th>{_esc(c['name'])}</th>" for c in block.columns)
    rows_html = ""
    for row in block.rows:
        cells = "".join(
            f"<td>{_render_table_cell(document, column, row['cells'].get(column['id']))}</td>"
            for column in block.columns
        )
        rows_html += f"<tr>{cells}</tr>"
    return f'<table border="1" cellspacing="0" cellpadding="4"><tr>{header}</tr>{rows_html}</table>'


def _render_simple_table_block(block: SimpleTableBlock) -> str:
    rows_html = "".join(
        "<tr>" + "".join(f"<td>{_esc(cell)}</td>" for cell in row) + "</tr>" for row in block.rows
    )
    return f'<table border="1" cellspacing="0" cellpadding="4">{rows_html}</table>'


def _render_gantt_block(document, block: GanttBlock) -> str:
    rows = compute_gantt_rows(document, block)
    if not rows:
        return "<p><i>(Gantt vide ou non configuré)</i></p>"
    rows_html = "".join(
        f"<tr><td>{_esc(r['label'])}</td><td>{_esc(r['start'] or '')}</td>"
        f"<td>{_esc(r['end'] or '')}</td></tr>"
        for r in rows
    )
    return (
        '<table border="1" cellspacing="0" cellpadding="4">'
        "<tr><th>Tâche</th><th>Début</th><th>Fin</th></tr>" + rows_html + "</table>"
    )


def _render_checklist_block(block: ChecklistBlock) -> str:
    items = "".join(
        f"<li>{'☑' if item.get('checked') else '☐'} {_esc(item.get('text', ''))}</li>"
        for item in block.items
    )
    return f"<ul>{items}</ul>"


def _render_linked_checklist_block(block: LinkedChecklistBlock) -> str:
    todo = "".join(f"<li>☐ {_esc(item.get('text', ''))}</li>" for item in block.todo_items())
    done = "".join(f"<li>☑ {_esc(item.get('text', ''))}</li>" for item in block.done_items())
    return (
        '<table border="0" cellspacing="0" cellpadding="4"><tr>'
        f'<td valign="top"><b>À faire</b><ul>{todo}</ul></td>'
        f'<td valign="top"><b>Faites</b><ul>{done}</ul></td>'
        "</tr></table>"
    )


def _render_list_block(block: ListBlock) -> str:
    tag = "ol" if block.list_type == LIST_TYPE_NUMBERED else "ul"
    items = "".join(f"<li>{_esc(item.get('text', ''))}</li>" for item in block.items)
    return f"<{tag}>{items}</{tag}>"


def _render_block(document, block) -> str:
    if isinstance(block, HeadingBlock):
        level = block.data.get("level", 1)
        return f"<h{level}>{_esc(block.content)}</h{level}>"
    if isinstance(block, TextBlock):
        return block.html or f"<p>{_esc(block.content)}</p>"
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
    if isinstance(block, FormulaBlock):
        return f"<p>{_esc(format_formula_text(block, compute_formula_result(document, block)))}</p>"
    if isinstance(block, ImageBlock):
        if not block.data.get("image_base64"):
            return "<p><i>(image vide)</i></p>"
        fmt = block.data.get("format", "png")
        width_attr = f' width="{block.data["width"]}"' if block.data.get("width") else ""
        return f'<img src="data:image/{fmt};base64,{block.data["image_base64"]}"{width_attr} />'
    if isinstance(block, QuoteBlock):
        return f"<blockquote><i>{_esc(block.content)}</i></blockquote>"
    if isinstance(block, CodeBlock):
        return f"<pre><code>{_esc(block.content)}</code></pre>"
    if isinstance(block, SeparatorBlock):
        return "<hr/>"
    return ""


def document_to_html(document) -> str:
    """Convertit tout le document en un unique fragment HTML, dans
    l'ordre des blocs. Chaque bloc est rendu de façon indépendante ;
    un bloc au rendu inconnu (nouveau type non géré ici) est ignoré
    plutôt que de faire échouer tout l'export."""
    parts = [_render_block(document, block) for block in document.blocks]
    return "\n".join(part for part in parts if part)


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; max-width: 800px;
          margin: 40px auto; padding: 0 16px; line-height: 1.5; color: #222; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
  blockquote {{ border-left: 3px solid #999; margin: 12px 0; padding-left: 12px; color: #555; }}
  pre {{ background: #f5f5f5; border: 1px solid #ddd; padding: 10px; overflow-x: auto; }}
  img {{ max-width: 100%; }}
  hr {{ border: none; border-top: 1px solid #ccc; margin: 20px 0; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def document_to_full_html(document, title: str = "Document") -> str:
    """PATCH 38 — Document HTML autonome et lisible dans un navigateur
    (doctype, head avec charset + CSS minimal, body). Réutilise
    `document_to_html` pour le contenu, sans dupliquer la logique de
    rendu par bloc — un seul moteur pour les exports PDF et HTML."""
    return _PAGE_TEMPLATE.format(title=_esc(title), body=document_to_html(document))
