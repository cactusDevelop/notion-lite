"""
Widget graphique du bloc Checklist.

Chaque élément est affiché comme une ligne : case à cocher + champ
de texte éditable + bouton de suppression. Toute modification est
immédiatement répercutée dans le ChecklistBlock associé.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from blocks.checklist_block import ChecklistBlock


class _ChecklistItemRow(QWidget):
    """Une ligne de la checklist : case à cocher + texte + suppression."""

    def __init__(self, text: str, checked: bool, owner: "ChecklistBlockWidget") -> None:
        super().__init__(owner)
        self._owner = owner

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox = QCheckBox(self)
        self.checkbox.setChecked(checked)
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

        self.line_edit = QLineEdit(self)
        self.line_edit.setText(text)
        self.line_edit.setPlaceholderText("Élément de la liste...")
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


class ChecklistBlockWidget(QWidget):
    """Représentation graphique éditable d'un ChecklistBlock."""

    def __init__(self, block: ChecklistBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._rows: list[_ChecklistItemRow] = []

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        for item in block.items:
            self._append_row(item.get("text", ""), item.get("checked", False))

        self._add_button = QPushButton("+ Ajouter un élément", self)
        self._add_button.clicked.connect(self._on_add_clicked)
        self._layout.addWidget(self._add_button)

    @property
    def block(self) -> ChecklistBlock:
        return self._block

    def _append_row(self, text: str, checked: bool) -> _ChecklistItemRow:
        row = _ChecklistItemRow(text, checked, self)
        # Toujours insérée juste avant le bouton "+ Ajouter" (en dernier).
        self._layout.insertWidget(len(self._rows), row)
        self._rows.append(row)
        return row

    def _on_add_clicked(self) -> None:
        self._block.add_item()
        row = self._append_row("", False)
        row.line_edit.setFocus()

    def remove_row(self, row: "_ChecklistItemRow") -> None:
        index = self._rows.index(row)
        self._block.remove_item(index)
        self._rows.pop(index)
        self._layout.removeWidget(row)
        row.deleteLater()

    def on_item_text_changed(self, row: "_ChecklistItemRow", text: str) -> None:
        self._block.set_item_text(self._rows.index(row), text)

    def on_item_checked_changed(self, row: "_ChecklistItemRow", checked: bool) -> None:
        self._block.set_item_checked(self._rows.index(row), checked)
