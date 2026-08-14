"""
Widget graphique du bloc "Effectif" (PATCH 52).

Affiche le registre partagé de personnes du document (Document.people)
sous forme d'étiquettes colorées, avec un champ texte permettant d'en
ajouter une nouvelle à chaque appui sur Entrée. Comme ce registre est
le même que celui utilisé par le Gestionnaire de personnes (Édition >
Gestionnaire de personnes), toute modification de part ou d'autre
reste toujours synchronisée : il n'y a qu'une seule source de vérité
(Document.people), ce widget n'en est qu'une vue.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.document import Document
from blocks.people_list_block import PeopleListBlock
from ui.i18n import tr


class _PersonChip(QWidget):
    """Étiquette colorée représentant une personne, avec suppression rapide."""

    def __init__(self, name: str, color: str, on_remove, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 4, 2)
        layout.setSpacing(4)
        self.setObjectName("personChip")
        self.setStyleSheet(
            f"#personChip {{ background-color: {color}22; border: 1px solid {color}; "
            "border-radius: 10px; }"
        )

        label = QLabel(name, self)
        label.setStyleSheet(f"color: {color}; font-weight: 600; border: none;")
        layout.addWidget(label)

        remove_button = QToolButton(self)
        remove_button.setText("×")
        remove_button.setToolTip(tr("people_list.remove_tooltip"))
        remove_button.setStyleSheet("border: none;")
        remove_button.clicked.connect(on_remove)
        layout.addWidget(remove_button)


class PeopleListBlockWidget(QWidget):
    """Représentation graphique éditable du bloc Effectif."""

    def __init__(self, block: PeopleListBlock, document: Document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._chips_row = QHBoxLayout()
        self._chips_row.setSpacing(6)
        self._chips_row.addStretch(1)
        self._layout.addLayout(self._chips_row)

        self._input = QLineEdit(self)
        self._input.setPlaceholderText(tr("people_list.add_placeholder"))
        self._input.returnPressed.connect(self._on_return_pressed)
        self._layout.addWidget(self._input)

        self._refresh()

    @property
    def block(self) -> PeopleListBlock:
        return self._block

    def _refresh(self) -> None:
        """Reconstruit les étiquettes à partir du registre partagé
        (source de vérité unique : Document.people)."""
        while self._chips_row.count() > 1:  # garde le stretch final
            item = self._chips_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for person in self._document.people:
            chip = _PersonChip(
                person["name"],
                person.get("color", "#000000"),
                on_remove=lambda person_id=person["id"]: self._on_remove(person_id),
                parent=self,
            )
            self._chips_row.insertWidget(self._chips_row.count() - 1, chip)

    def _on_return_pressed(self) -> None:
        """PATCH 52 — Entrée dans le champ ajoute la personne au
        registre partagé du document, visible aussitôt ici et dans le
        Gestionnaire de personnes, et vide le champ pour un ajout
        immédiat en chaîne."""
        name = self._input.text().strip()
        if not name:
            return
        self._document.add_person(name)
        self._input.clear()
        self._refresh()
        self._input.setFocus(Qt.OtherFocusReason)

    def _on_remove(self, person_id: str) -> None:
        self._document.remove_person(person_id)
        self._refresh()
