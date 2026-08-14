"""
Widget graphique du bloc "Effectif" (PATCH 52, revu PATCH 82/83).

Affiche les personnes de ce projet (Document.people, résolues depuis
le registre système partagé — voir core.people_registry) sous forme
d'étiquettes colorées, avec un champ texte permettant d'en ajouter une
nouvelle à chaque appui sur Entrée.

PATCH 83 :
- Corrige la croix de suppression des étiquettes, qui ne faisait rien
  (le signal `clicked(bool checked)` de Qt passait ce booléen à la
  place de l'identifiant attendu par le callback — voir _PersonChip).
- Ce widget s'abonne désormais aux changements du document
  (Document.add_people_listener) : toute personne ajoutée ailleurs
  (Gestionnaire de personnes, popup "Personne" d'un tableau...) y
  apparaît aussitôt, sans attendre un re-rendu complet du document.
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
        remove_button.setCursor(Qt.PointingHandCursor)
        remove_button.setStyleSheet("border: none;")
        # PATCH 83 — `clicked` émet un booléen `checked` : le premier
        # paramètre de la lambda doit l'absorber explicitement, sinon
        # Qt l'assigne à la place de `on_remove`, qui reçoit alors
        # `False`/`True` au lieu d'être appelé sans argument (idiome
        # déjà utilisé ailleurs dans l'app, ex. list_block_widget.py).
        remove_button.clicked.connect(lambda _checked=False: on_remove())
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

        # PATCH 83 — Vue toujours synchronisée : se met à jour dès que
        # le document notifie un changement de personnes, d'où qu'il
        # vienne (Gestionnaire de personnes, popup "Personne" d'un
        # tableau...), pas seulement via ce widget. Désabonnement à la
        # destruction pour ne pas garder de référence morte.
        self._document.add_people_listener(self._refresh)
        self.destroyed.connect(lambda: document.remove_people_listener(self._refresh))

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
        immédiat en chaîne. `_refresh` est déclenché automatiquement
        par `Document.add_person` via `add_people_listener` (PATCH 83).
        """
        name = self._input.text().strip()
        if not name:
            return
        self._document.add_person(name)
        self._input.clear()
        self._input.setFocus(Qt.OtherFocusReason)

    def _on_remove(self, person_id: str) -> None:
        """Détache la personne de ce projet. `_refresh` est déclenché
        automatiquement par `Document.remove_person` (PATCH 83)."""
        self._document.remove_person(person_id)
