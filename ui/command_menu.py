"""
Popup du menu de commandes "/" (PATCH 25).

Fenêtre flottante sans bordure (Qt.Popup) listant les commandes
disponibles, filtrables en tapant après le "/". Se ferme sur
sélection, Échap, ou perte de focus.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from ui.command_registry import filter_commands


class CommandMenu(QWidget):
    """Popup filtrable listant les commandes "/" (PATCH 25)."""

    command_selected = Signal(str)  # émet l'id de la commande choisie

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.Popup)
        self.setAttribute(Qt.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Rechercher une commande...")
        self._search.textChanged.connect(self._on_search_changed)
        self._search.returnPressed.connect(self._on_return_pressed)
        layout.addWidget(self._search)

        self._list = QListWidget(self)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

        self.setFixedSize(220, 220)
        self._populate("")
        self._search.setFocus()

    def _populate(self, query: str) -> None:
        self._list.clear()
        for command in filter_commands(query):
            item = QListWidgetItem(f"/{command['label']}")
            item.setData(Qt.UserRole, command["id"])
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _on_search_changed(self, text: str) -> None:
        self._populate(text)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        self.command_selected.emit(item.data(Qt.UserRole))
        self.close()

    def _on_return_pressed(self) -> None:
        item = self._list.currentItem()
        if item is not None:
            self.command_selected.emit(item.data(Qt.UserRole))
        self.close()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        if event.key() in (Qt.Key_Down, Qt.Key_Up):
            row = self._list.currentRow()
            delta = 1 if event.key() == Qt.Key_Down else -1
            new_row = max(0, min(row + delta, self._list.count() - 1))
            self._list.setCurrentRow(new_row)
            return
        super().keyPressEvent(event)
