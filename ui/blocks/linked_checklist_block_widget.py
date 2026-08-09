"""
Widget graphique du bloc "Checklists liées" (PATCH 44).

Deux panneaux ("À faire" / "Faites") dans un QSplitter horizontal
(séparateur ajustable, position mémorisée dans le bloc). Cocher un
élément dans un panneau le déplace immédiatement dans l'autre.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from blocks.linked_checklist_block import LinkedChecklistBlock

_SPLITTER_TOTAL = 1000


class _LinkedItemRow(QWidget):
    """Une ligne : case à cocher + texte + suppression."""

    def __init__(
        self, item_id: str, text: str, checked: bool, owner: "LinkedChecklistBlockWidget"
    ) -> None:
        super().__init__(owner)
        self._owner = owner
        self.item_id = item_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox = QCheckBox(self)
        self.checkbox.setChecked(checked)
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

        self.line_edit = QLineEdit(self)
        self.line_edit.setText(text)
        self.line_edit.setPlaceholderText("Élément...")
        self.line_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.line_edit, 1)

        remove_button = QToolButton(self)
        remove_button.setText("×")
        remove_button.setToolTip("Supprimer cet élément")
        remove_button.clicked.connect(lambda: self._owner.remove_row(self))
        layout.addWidget(remove_button)

    def _on_toggled(self, checked: bool) -> None:
        self._owner.on_item_checked_changed(self, checked)

    def _on_text_changed(self, text: str) -> None:
        self._owner.on_item_text_changed(self, text)


class _ChecklistColumn(QWidget):
    """Un panneau (gauche ou droite) : titre, lignes, bouton d'ajout optionnel."""

    def __init__(self, title: str, show_add_button: bool, owner: "LinkedChecklistBlockWidget") -> None:
        super().__init__(owner)
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(4, 0, 4, 0)
        self.layout_.addWidget(QLabel(f"<b>{title}</b>", self))
        self.rows: list[_LinkedItemRow] = []
        self.add_button: QPushButton | None = None
        if show_add_button:
            self.add_button = QPushButton("+ Ajouter", self)
            self.add_button.clicked.connect(owner._on_add_clicked)
            self.layout_.addWidget(self.add_button)

    def add_row(self, row: _LinkedItemRow) -> None:
        # Insérée juste avant le bouton d'ajout s'il existe, sinon en fin.
        index = len(self.rows) + 1
        self.layout_.insertWidget(index, row)
        self.rows.append(row)

    def clear_rows(self) -> None:
        for row in self.rows:
            self.layout_.removeWidget(row)
            row.deleteLater()
        self.rows = []


class LinkedChecklistBlockWidget(QWidget):
    """Représentation graphique éditable d'un LinkedChecklistBlock."""

    def __init__(self, block: LinkedChecklistBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Horizontal, self)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.splitterMoved.connect(self._on_splitter_moved)

        self._todo_column = _ChecklistColumn("À faire", show_add_button=True, owner=self)
        self._done_column = _ChecklistColumn("Faites", show_add_button=False, owner=self)
        self._splitter.addWidget(self._todo_column)
        self._splitter.addWidget(self._done_column)

        outer.addWidget(self._splitter)

        self._rebuild()
        left = int(_SPLITTER_TOTAL * self._block.split)
        self._splitter.setSizes([left, _SPLITTER_TOTAL - left])

    @property
    def block(self) -> LinkedChecklistBlock:
        return self._block

    def _rebuild(self, focus_item_id: str | None = None) -> None:
        self._todo_column.clear_rows()
        self._done_column.clear_rows()
        focus_row: _LinkedItemRow | None = None
        for item in self._block.items:
            column = self._done_column if item.get("checked") else self._todo_column
            row = _LinkedItemRow(item["id"], item.get("text", ""), item.get("checked", False), self)
            column.add_row(row)
            if focus_item_id is not None and item["id"] == focus_item_id:
                focus_row = row
        if focus_row is not None:
            focus_row.line_edit.setFocus()

    def _on_add_clicked(self) -> None:
        item = self._block.add_item()
        self._rebuild(focus_item_id=item["id"])

    def remove_row(self, row: _LinkedItemRow) -> None:
        self._block.remove_item(row.item_id)
        self._rebuild()

    def on_item_text_changed(self, row: _LinkedItemRow, text: str) -> None:
        self._block.set_item_text(row.item_id, text)

    def on_item_checked_changed(self, row: _LinkedItemRow, checked: bool) -> None:
        """Coche/décoche puis reconstruit : l'élément change de panneau."""
        self._block.set_item_checked(row.item_id, checked)
        self._rebuild(focus_item_id=row.item_id)

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        sizes = self._splitter.sizes()
        total = sum(sizes) or 1
        self._block.split = sizes[0] / total
