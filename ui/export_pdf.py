"""
Export PDF (PATCH 36).

Réutilise `core.document_html_export.document_to_html` (rendu HTML
pur du document), l'injecte dans un QTextDocument, puis l'imprime
dans un fichier PDF via QPrinter — la même approche que l'aperçu
avant impression natif de Qt, donc fiable et sans dépendance externe.
"""
from __future__ import annotations

from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrinter

from core.document_html_export import document_to_full_html


def export_document_to_pdf(document, filepath: str) -> None:
    """Génère un PDF du document courant à `filepath`."""
    # PATCH 63 — utilise le HTML complet (avec le CSS de mise en forme :
    # espacements, bordures de tableaux, ...) au lieu du seul fragment,
    # sinon QTextDocument affiche tout sans aucune de ces règles.
    html = document_to_full_html(document)

    text_document = QTextDocument()
    text_document.setHtml(html)

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setPageSize(QPageSize(QPageSize.A4))
    printer.setPageOrientation(QPageLayout.Portrait)
    printer.setOutputFileName(filepath)

    text_document.print_(printer)
