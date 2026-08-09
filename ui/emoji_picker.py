"""
Popup sélecteur d'emojis (PATCH 35).

Fenêtre flottante sans bordure (Qt.Popup), même famille d'interaction
que le menu de commandes "/" (PATCH 25) : recherche filtrable,
sélection à la souris ou au clavier.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from core.emoji_data import search_emojis


class EmojiPicker(QWidget):
    """Popup filtrable listant les emojis (PATCH 35)."""

    emoji_selected = Signal(str)  # émet l'emoji choisi (ex. "😄")

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.Popup)
        self.setAttribute(Qt.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Rechercher un emoji (ex. smile)...")
        self._search.textChanged.connect(self._on_search_changed)
        self._search.returnPressed.connect(self._on_return_pressed)
        layout.addWidget(self._search)

        self._list = QListWidget(self)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

        self.setFixedSize(240, 260)
        self._populate("")
        self._search.setFocus()

    def _populate(self, query: str) -> None:
        self._list.clear()
        for emoji, shortcode, _category in search_emojis(query):
            item = QListWidgetItem(f"{emoji}  :{shortcode}:")
            item.setData(Qt.UserRole, emoji)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _on_search_changed(self, text: str) -> None:
        self._populate(text)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        self.emoji_selected.emit(item.data(Qt.UserRole))
        self.close()

    def _on_return_pressed(self) -> None:
        item = self._list.currentItem()
        if item is not None:
            self.emoji_selected.emit(item.data(Qt.UserRole))
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
