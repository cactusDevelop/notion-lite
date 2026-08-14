"""
Sélecteur de bloc (PATCH 30).

Boîte de dialogue listant tous les blocs du document (aperçu via
`core.block_preview.preview_for_block`) pour choisir la cible d'un
lien interne. Le bloc source est exclu de la liste (se lier à
soi-même n'a pas de sens).
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QVBoxLayout

from core.block_preview import preview_for_block
from core.document import Document

# Réutilise les libellés lisibles du menu "/" (PATCH 25) plutôt que
# de les dupliquer.
from ui.command_registry import get_commands
from ui.i18n import tr

def _type_labels() -> dict[str, str]:
    return {command["id"]: command["label"] for command in get_commands()}


class BlockPickerDialog(QDialog):
    """Fenêtre de choix d'un bloc du document (pour un lien interne)."""

    def __init__(
        self,
        document: Document,
        exclude_block_id: Optional[str] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._document = document
        self.selected_block_id: Optional[str] = None

        self.setWindowTitle(tr("block_picker.title"))
        self.resize(440, 400)

        layout = QVBoxLayout(self)

        self._list = QListWidget(self)
        self._list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._list)

        for block in document.blocks:
            if block.id == exclude_block_id:
                continue
            type_label = _type_labels().get(block.type, block.type)
            item = QListWidgetItem(f"[{type_label}] {preview_for_block(block)}")
            item.setData(Qt.UserRole, block.id)
            self._list.addItem(item)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        self.selected_block_id = item.data(Qt.UserRole)
        self.accept()
