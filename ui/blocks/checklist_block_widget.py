"""
Widget graphique du bloc Checklist.

Chaque élément est affiché comme une ligne : case à cocher + champ
de texte éditable + bouton de suppression. Toute modification est
immédiatement répercutée dans le ChecklistBlock associé, en utilisant
l'id de l'élément (et non sa position) comme référence stable.
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

    def __init__(
        self, item_id: str, text: str, checked: bool, owner: "ChecklistBlockWidget"
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

        # PATCH 11 : la checklist s'affiche toujours triée (non cochées
        # d'abord), y compris juste après un chargement de fichier.
        self._block.sort_by_status()
        for item in block.items:
            self._append_row(item)

        self._add_button = QPushButton("+ Ajouter un élément", self)
        self._add_button.clicked.connect(self._on_add_clicked)
        self._layout.addWidget(self._add_button)

    @property
    def block(self) -> ChecklistBlock:
        return self._block

    def _append_row(self, item: dict) -> _ChecklistItemRow:
        row = _ChecklistItemRow(
            item["id"], item.get("text", ""), item.get("checked", False), self
        )
        # Toujours insérée juste avant le bouton "+ Ajouter" (en dernier).
        self._layout.insertWidget(len(self._rows), row)
        self._rows.append(row)
        return row

    def _rebuild_rows(self, focus_item_id: str | None = None) -> None:
        """Reconstruit toutes les lignes dans l'ordre courant du bloc (PATCH 11).

        L'utilisateur ne déplace jamais une ligne manuellement : c'est
        toujours le tri du bloc qui pilote l'ordre affiché.
        """
        for row in self._rows:
            self._layout.removeWidget(row)
            row.deleteLater()
        self._rows = []

        focus_row: _ChecklistItemRow | None = None
        for item in self._block.items:
            row = self._append_row(item)
            if focus_item_id is not None and item["id"] == focus_item_id:
                focus_row = row
        if focus_row is not None:
            focus_row.line_edit.setFocus()

    def _on_add_clicked(self) -> None:
        item = self._block.add_item()
        row = self._append_row(item)
        row.line_edit.setFocus()

    def remove_row(self, row: "_ChecklistItemRow") -> None:
        self._block.remove_item(row.item_id)
        self._rows.remove(row)
        self._layout.removeWidget(row)
        row.deleteLater()

    def on_item_text_changed(self, row: "_ChecklistItemRow", text: str) -> None:
        self._block.set_item_text(row.item_id, text)

    def on_item_checked_changed(self, row: "_ChecklistItemRow", checked: bool) -> None:
        """Coche/décoche puis re-trie automatiquement (PATCH 11)."""
        self._block.set_item_checked(row.item_id, checked)
        self._block.sort_by_status()
        self._rebuild_rows(focus_item_id=row.item_id)
