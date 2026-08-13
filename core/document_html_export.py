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
from blocks.bar_chart_block import BarChartBlock, sync_bars_from_gantt
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
from blocks.table_block import COLUMN_TYPE_BOOLEAN, COLUMN_TYPE_CHECKLIST, COLUMN_TYPE_DATE, COLUMN_TYPE_DURATION, COLUMN_TYPE_MULTI_SELECT, COLUMN_TYPE_PERSON, COLUMN_TYPE_TEXT, TableBlock
from blocks.text_block import TextBlock
from core.duration import format_duration


def _esc(text) -> str:
    if text is None:
        text = ""
    elif not isinstance(text, str):
        text = str(text)
    return html_module.escape(text)


def _format_day(value: float) -> str:
    """Formate un décalage en jours (float) en texte lisible, ex.
    3.0 -> "Jour 3", 2.5 -> "Jour 2.5" (PATCH 62 — correctif export PDF)."""
    rounded = round(value, 2)
    if rounded == int(rounded):
        return f"Jour {int(rounded)}"
    return f"Jour {rounded:g}"


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


def _compute_column_spans(block: TableBlock, column: dict) -> list[int]:
    """Pour une colonne donnée, calcule le rowspan à appliquer à chaque
    ligne (par index) : N si la ligne démarre une fusion de N lignes,
    1 si elle n'est pas fusionnée, 0 si elle est absorbée par la fusion
    d'une ligne précédente (ne doit alors pas être rendue). Reproduit
    exactement la logique de `TableBlockWidget._apply_merged_cells`
    (PATCH 63 — correctif export PDF) : fusion manuelle (clic droit)
    en priorité, sinon fusion automatique des valeurs identiques
    consécutives d'une colonne "Texte".
    """
    rows = block.rows
    spans = [1] * len(rows)
    row_index_by_id = {row["id"]: i for i, row in enumerate(rows)}

    manual_groups = block.manual_merge_groups(column["id"])
    if manual_groups:
        for group in manual_groups:
            indices = sorted(row_index_by_id[rid] for rid in group if rid in row_index_by_id)
            if len(indices) < 2:
                continue
            if indices == list(range(indices[0], indices[0] + len(indices))):
                spans[indices[0]] = len(indices)
                for i in indices[1:]:
                    spans[i] = 0
        return spans

    if column["type"] != COLUMN_TYPE_TEXT:
        return spans

    run_start = 0
    while run_start < len(rows):
        value = rows[run_start]["cells"].get(column["id"])
        run_end = run_start + 1
        while run_end < len(rows) and rows[run_end]["cells"].get(column["id"]) == value and value:
            run_end += 1
        run_length = run_end - run_start
        if run_length > 1:
            spans[run_start] = run_length
            for i in range(run_start + 1, run_end):
                spans[i] = 0
        run_start = run_end
    return spans


def _render_table_block(document, block: TableBlock) -> str:
    header = "".join(f"<th>{_esc(c['name'])}</th>" for c in block.columns)
    column_spans = [_compute_column_spans(block, column) for column in block.columns]
    rows_html = ""
    for row_index, row in enumerate(block.rows):
        cells = ""
        for col_index, column in enumerate(block.columns):
            span = column_spans[col_index][row_index]
            if span == 0:
                continue  # absorbée par la fusion d'une ligne précédente
            rowspan_attr = f' rowspan="{span}"' if span > 1 else ""
            value_html = _render_table_cell(document, column, row["cells"].get(column["id"]))
            cells += f"<td{rowspan_attr}>{value_html}</td>"
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


def _render_dependency_gantt_block(document, block: DependencyGanttBlock) -> str:
    schedule = compute_schedule(document, block)
    if not schedule:
        return "<p><i>(Gantt par dépendances vide ou non configuré)</i></p>"
    rows_html = "".join(
        f"<tr><td>{_esc(t['label'])}</td><td>{_esc(', '.join(t['person_names']))}</td>"
        f"<td>{_esc(_format_day(t['start']))}</td><td>{_esc(_format_day(t['end']))}</td>"
        f"<td>{_esc(_format_day(t['resolution']))}</td></tr>"
        for t in schedule
    )
    return (
        '<table border="1" cellspacing="0" cellpadding="4">'
        "<tr><th>Sous-tâche</th><th>Personnes</th><th>Début</th><th>Fin</th><th>Résolution</th></tr>"
        + rows_html
        + "</table>"
    )


def _render_line_chart_block(document, block: LineChartBlock) -> str:
    series = compute_line_series(document, block)
    title = block.title or "(sans titre)"
    axes = f" — {_esc(block.x_axis_label)} / {_esc(block.y_axis_label)}" if (block.x_axis_label or block.y_axis_label) else ""
    if not series:
        return f"<p><b>{_esc(title)}</b>{axes} (aucune série)</p>"
    rows_html = "".join(
        f"<tr><td>{_esc(s['name'])}</td><td>{_esc(s['slope'])}</td></tr>" for s in series
    )
    return (
        f"<p><b>{_esc(title)}</b>{axes}</p>"
        '<table border="1" cellspacing="0" cellpadding="4">'
        "<tr><th>Droite</th><th>Pente</th></tr>" + rows_html + "</table>"
    )


def _render_bar_chart_block(document, block: BarChartBlock, chart_renderer=None) -> str:
    # PATCH 78 — si un `chart_renderer` (callback fourni par l'export PDF,
    # voir ui/export_pdf.py) sait produire une image du graphique tel
    # qu'affiché dans l'app, on l'utilise à la place du tableau de
    # données ci-dessous (conservé comme repli, ex. export HTML pur
    # sans Qt disponible, ou graphique vide).
    if chart_renderer is not None:
        image_html = chart_renderer(document, block)
        if image_html is not None:
            return image_html
    bars = sync_bars_from_gantt(document, block)
    if not bars:
        return f"<p><b>{_esc(block.title)}</b> (aucune barre)</p>"
    rows_html = "".join(
        f"<tr><td>{_esc(b['label'])}</td><td>{_esc(b['value'])}</td>"
        f"<td>{_esc(b['actual']) if b['actual'] is not None else '—'}</td></tr>"
        for b in bars
    )
    return (
        f"<p><b>{_esc(block.title)}</b> ({_esc(block.y_axis_label)})</p>"
        '<table border="1" cellspacing="0" cellpadding="4">'
        "<tr><th>Catégorie</th><th>Prévu</th><th>Réel</th></tr>" + rows_html + "</table>"
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


def _render_block(document, block, chart_renderer=None) -> str:
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
    if isinstance(block, DependencyGanttBlock):
        return _render_dependency_gantt_block(document, block)
    if isinstance(block, FormulaBlock):
        return f"<p>{_esc(format_formula_text(block, compute_formula_result(document, block)))}</p>"
    if isinstance(block, LineChartBlock):
        return _render_line_chart_block(document, block)
    if isinstance(block, BarChartBlock):
        return _render_bar_chart_block(document, block, chart_renderer)
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


def document_to_html(document, chart_renderer=None) -> str:
    """Convertit tout le document en un unique fragment HTML, dans
    l'ordre des blocs. Chaque bloc est rendu de façon indépendante ;
    un bloc au rendu inconnu (nouveau type non géré ici) est ignoré
    plutôt que de faire échouer tout l'export.

    PATCH 78 — `chart_renderer(document, block) -> str | None` est un
    callback optionnel (fourni par `ui/export_pdf.py`, qui a accès à
    Qt) capable de rendre un bloc graphique en véritable image
    (identique à l'app) plutôt qu'en tableau de données. Ce module
    reste volontairement sans dépendance Qt : sans callback (export
    HTML, tests), le repli en tableau est utilisé.
    """
    parts = [_render_block(document, block, chart_renderer) for block in document.blocks]
    return "\n".join(part for part in parts if part)


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; max-width: 800px;
          margin: 40px auto; padding: 0 16px; line-height: 1.5; color: #222; }}
  h1, h2, h3 {{ margin-top: 28px; margin-bottom: 10px; }}
  p {{ margin: 8px 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 18px 0; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; vertical-align: top; }}
  blockquote {{ border-left: 3px solid #999; margin: 12px 0; padding-left: 12px; color: #555; }}
  pre {{ background: #f5f5f5; border: 1px solid #ddd; padding: 10px; overflow-x: auto; margin: 12px 0; }}
  img {{ max-width: 100%; margin: 18px 0; }}
  hr {{ border: none; border-top: 1px solid #ccc; margin: 20px 0; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def document_to_full_html(document, title: str = "Document", chart_renderer=None) -> str:
    """PATCH 38 — Document HTML autonome et lisible dans un navigateur
    (doctype, head avec charset + CSS minimal, body). Réutilise
    `document_to_html` pour le contenu, sans dupliquer la logique de
    rendu par bloc — un seul moteur pour les exports PDF et HTML.
    PATCH 78 — voir `document_to_html` pour `chart_renderer`."""
    return _PAGE_TEMPLATE.format(title=_esc(title), body=document_to_html(document, chart_renderer))