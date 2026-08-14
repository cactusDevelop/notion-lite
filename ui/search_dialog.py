"""
Boîte de dialogue de recherche et remplacement (PATCH 28 / PATCH 29).

Recherche en direct (à chaque frappe) sur tout le document via
`core.search.search_document`. Double-cliquer (ou Entrée) sur un
résultat ferme la boîte et fait défiler jusqu'au bloc correspondant.

« Tout remplacer » (PATCH 29) délègue à `core.replace.replace_all` et
notifie la fenêtre principale pour qu'elle rafraîchisse l'affichage ;
l'action reste annulable comme toute autre (historique générique du
PATCH 27, basé sur des snapshots du document).
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from core.document import Document
from core.replace import replace_all
from core.search import search_document
from ui.i18n import tr


class SearchDialog(QDialog):
    """Fenêtre de recherche et remplacement globaux."""

    def __init__(
        self,
        document: Document,
        on_result_activated: Optional[Callable[[str], None]] = None,
        on_document_changed: Optional[Callable[[], None]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._document = document
        self._on_result_activated = on_result_activated
        self._on_document_changed = on_document_changed

        self.setWindowTitle(tr("search.title"))
        self.resize(480, 460)

        layout = QVBoxLayout(self)

        self._input = QLineEdit(self)
        self._input.setPlaceholderText(tr("search.placeholder"))
        self._input.textChanged.connect(self._on_query_changed)
        layout.addWidget(self._input)

        replace_row = QHBoxLayout()
        self._replacement_input = QLineEdit(self)
        self._replacement_input.setPlaceholderText(tr("search.replace_placeholder"))
        replace_row.addWidget(self._replacement_input, 1)

        self._replace_all_button = QPushButton(tr("search.replace_all"), self)
        self._replace_all_button.clicked.connect(self._on_replace_all_clicked)
        replace_row.addWidget(self._replace_all_button)
        layout.addLayout(replace_row)

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
            self._status_label.setText(tr("search.no_results"))
        else:
            key = "search.result" if len(results) == 1 else "search.results"
            self._status_label.setText(f"{len(results)} {tr(key)}")

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

    def _on_replace_all_clicked(self) -> None:
        """PATCH 29 — Remplace toutes les occurrences de la recherche."""
        query = self._input.text()
        replacement = self._replacement_input.text()
        count = replace_all(self._document, query, replacement)

        if count == 0:
            self._status_label.setText(tr("search.no_replacement"))
            return

        if self._on_document_changed is not None:
            self._on_document_changed()

        self._status_label.setText(
            tr("search.replacement_done_one" if count == 1 else "search.replacement_done_many").format(count=count)
        )
        self._on_query_changed(self._input.text())
