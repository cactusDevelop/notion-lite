"""
Gestionnaire de personnes (PATCH 16).

Fenêtre listant toutes les personnes du registre partagé du document,
avec ajout, renommage et suppression. La suppression purge aussi
toutes les références à cette personne dans les colonnes "Personne"
des blocs Tableau (voir Document.remove_person).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.document import Document
from ui.i18n import tr


class PeopleManagerDialog(QDialog):
    """Boîte de dialogue de gestion du registre de personnes du document."""

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self._document = document
        self.setWindowTitle(tr("people.title"))
        self.resize(360, 400)

        layout = QVBoxLayout(self)

        self._list = QListWidget(self)
        layout.addWidget(self._list)

        add_row = QHBoxLayout()
        add_button = QPushButton(tr("people.add"), self)
        add_button.clicked.connect(self._on_add)
        add_row.addWidget(add_button)

        rename_button = QPushButton(tr("people.rename"), self)
        rename_button.clicked.connect(self._on_rename)
        add_row.addWidget(rename_button)

        color_button = QPushButton(tr("people.color"), self)
        color_button.clicked.connect(self._on_change_color)
        add_row.addWidget(color_button)

        remove_button = QPushButton(tr("people.remove"), self)
        remove_button.clicked.connect(self._on_remove)
        add_row.addWidget(remove_button)
        layout.addLayout(add_row)

        close_button = QPushButton(tr("people.close"), self)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self._refresh()

    def _refresh(self) -> None:
        self._list.clear()
        for person in self._document.people:
            item = QListWidgetItem(person["name"])
            item.setData(Qt.UserRole, person["id"])
            item.setForeground(QColor(person.get("color", "#000000")))
            self._list.addItem(item)

    def _current_person_id(self) -> str | None:
        item = self._list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _on_add(self) -> None:
        name, ok = QInputDialog.getText(self, tr("people.new_person"), tr("people.name_label"))
        if ok and name.strip():
            self._document.add_person(name.strip())
            self._refresh()

    def _on_rename(self) -> None:
        person_id = self._current_person_id()
        if person_id is None:
            return
        person = self._document.find_person(person_id)
        name, ok = QInputDialog.getText(
            self, tr("people.rename_person"), tr("people.name_label"), text=person["name"] if person else ""
        )
        if ok and name.strip():
            self._document.rename_person(person_id, name.strip())
            self._refresh()

    def _on_change_color(self) -> None:
        person_id = self._current_person_id()
        if person_id is None:
            return
        person = self._document.find_person(person_id)
        current = QColor(person.get("color", "#000000")) if person else QColor("black")
        color = QColorDialog.getColor(current, self, tr("people.pick_color"))
        if color.isValid():
            self._document.set_person_color(person_id, color.name())
            self._refresh()

    def _on_remove(self) -> None:
        person_id = self._current_person_id()
        if person_id is None:
            return
        person = self._document.find_person(person_id)
        confirm = QMessageBox.question(
            self,
            tr("people.remove_title"),
            tr("people.remove_confirm").format(name=person["name"] if person else ""),
        )
        if confirm == QMessageBox.Yes:
            self._document.remove_person(person_id)
            self._refresh()
