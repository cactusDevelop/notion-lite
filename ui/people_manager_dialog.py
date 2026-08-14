"""
Gestionnaire de personnes (PATCH 16, revu PATCH 82).

Fenêtre listant les personnes de CE projet (Document.people, résolues
depuis le registre système partagé — voir core.people_registry), avec
ajout, renommage, changement de couleur et retrait.

Depuis le PATCH 82, une personne existe indépendamment de tout projet
(fichier système partagé, réutilisable d'un projet à l'autre) :
- "Ajouter..." crée (ou réutilise si le nom existe déjà) une personne
  dans le registre partagé et l'associe à ce projet.
- "Lier une personne existante..." associe à ce projet une personne
  déjà créée depuis un autre projet, sans la dupliquer.
- "Retirer du projet" détache la personne de ce projet (et purge ses
  références dans les tableaux) SANS la supprimer du registre partagé :
  elle reste disponible ailleurs.
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
    """Boîte de dialogue de gestion des personnes de ce projet."""

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self._document = document
        self.setWindowTitle(tr("people.title"))
        self.resize(360, 420)

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

        link_button = QPushButton(tr("people.link_existing"), self)
        link_button.clicked.connect(self._on_link_existing)
        layout.addWidget(link_button)

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

    def _on_link_existing(self) -> None:
        """PATCH 82 — Associe à ce projet une personne déjà connue du
        registre système partagé (créée depuis un autre projet), au
        lieu d'en recréer une, potentiellement en double."""
        already_linked = {p["id"] for p in self._document.people}
        candidates = [
            person
            for person in self._document.people_registry.people
            if person["id"] not in already_linked
        ]
        if not candidates:
            QMessageBox.information(
                self, tr("people.link_existing_title"), tr("people.link_existing_empty")
            )
            return
        names = [person["name"] for person in candidates]
        name, ok = QInputDialog.getItem(
            self, tr("people.link_existing_title"), tr("people.name_label"), names, editable=False
        )
        if ok and name:
            person = next(p for p in candidates if p["name"] == name)
            self._document.link_person(person["id"])
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

