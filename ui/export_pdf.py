"""
Export PDF (PATCH 36).

Réutilise `core.document_html_export.document_to_html` (rendu HTML
pur du document), l'injecte dans un QTextDocument, puis l'imprime
dans un fichier PDF via QPrinter — la même approche que l'aperçu
avant impression natif de Qt, donc fiable et sans dépendance externe.

PATCH 78 — les blocs graphiques (bar chart, courbes, Gantt) étaient
jusqu'ici rendus en tableaux de données dans le PDF. Ce module fournit
maintenant à `document_to_full_html` un `chart_renderer` qui réutilise
le même canvas Qt que l'affichage à l'écran (`_BarChartCanvas`), le
rend hors-écran en image PNG (`QWidget.grab()`), et l'insère comme
`<img>` : le PDF affiche donc le graphique tel qu'il apparaît dans
l'app, pas ses données brutes. Traité graphique par graphique (bar
chart d'abord) pour limiter le risque à chaque étape ; les autres
types de graphiques retombent encore sur le tableau de données.
"""
from __future__ import annotations

import base64
from html import escape as _esc

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrinter

from blocks.bar_chart_block import BarChartBlock, sync_bars_from_gantt
from core.document_html_export import document_to_full_html
from ui.blocks.bar_chart_block_widget import _BarChartCanvas

_CHART_IMAGE_WIDTH = 640
_CHART_IMAGE_HEIGHT = 280


def _pixmap_to_data_uri(pixmap) -> str:
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, "PNG")
    encoded = base64.b64encode(bytes(buffer.data())).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _render_bar_chart_image(document, block: BarChartBlock) -> str | None:
    """Rend un BarChartBlock en image PNG (repli `None` : tableau de
    données géré par `core.document_html_export`, ex. graphique vide)."""
    bars = sync_bars_from_gantt(document, block)
    if not bars:
        return None
    canvas = _BarChartCanvas()
    canvas.set_data(bars, block.y_axis_label)
    canvas.resize(_CHART_IMAGE_WIDTH, _CHART_IMAGE_HEIGHT)
    data_uri = _pixmap_to_data_uri(canvas.grab())
    return f'<p><b>{_esc(block.title)}</b></p><img src="{data_uri}" />'


def _chart_renderer(document, block) -> str | None:
    """PATCH 78 — dispatch par type de bloc graphique. Les types pas
    encore traités (courbes, Gantt) renvoient `None` : repli au tableau
    de données existant, à traiter dans une prochaine étape."""
    if isinstance(block, BarChartBlock):
        return _render_bar_chart_image(document, block)
    return None


def export_document_to_pdf(document, filepath: str) -> None:
    """Génère un PDF du document courant à `filepath`."""
    # PATCH 63 — utilise le HTML complet (avec le CSS de mise en forme :
    # espacements, bordures de tableaux, ...) au lieu du seul fragment,
    # sinon QTextDocument affiche tout sans aucune de ces règles.
    html = document_to_full_html(document, chart_renderer=_chart_renderer)

    text_document = QTextDocument()
    text_document.setHtml(html)

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setPageSize(QPageSize(QPageSize.A4))
    printer.setPageOrientation(QPageLayout.Portrait)
    printer.setOutputFileName(filepath)

    text_document.print_(printer)
