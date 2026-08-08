"""
Boîte de dialogue de recherche globale (PATCH 28).

Recherche en direct (à chaque frappe) sur tout le document via
`core.search.search_document`. Double-cliquer (ou Entrée) sur un
résultat ferme la boîte et fait défiler jusqu'au bloc correspondant.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from core.document import Document
from core.search import search_document


class SearchDialog(QDialog):
    """Fenêtre de recherche globale (texte, checklists, tableaux)."""

    def __init__(
        self,
        document: Document,
        on_result_activated: Optional[Callable[[str], None]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._document = document
        self._on_result_activated = on_result_activated

        self.setWindowTitle("Recherche globale")
        self.resize(480, 420)

        layout = QVBoxLayout(self)

        self._input = QLineEdit(self)
        self._input.setPlaceholderText("Rechercher dans le document...")
        self._input.textChanged.connect(self._on_query_changed)
        layout.addWidget(self._input)

        self._status_label = QLabel("", self)
        layout.addWidget(self._status_label)

        self._results_list = QListWidget(self)
        self._results_list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._results_list)

        self._input.setFocus()

    def _on_query_changed(self, query: str) -> None:
        self._results_list.clear()
        results = search_document(self._document, query)

        if not query.strip():
            self._status_label.setText("")
        elif not results:
            self._status_label.setText("Aucun résultat.")
        else:
            plural = "s" if len(results) > 1 else ""
            self._status_label.setText(f"{len(results)} résultat{plural}")

        for result in results:
            item = QListWidgetItem(f"[{result.location}] {result.snippet}")
            item.setData(Qt.UserRole, result.block_id)
            self._results_list.addItem(item)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        block_id = item.data(Qt.UserRole)
        if block_id is None:
            return
        if self._on_result_activated is not None:
            self._on_result_activated(block_id)
        self.accept()
