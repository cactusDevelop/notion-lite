"""
Boîtes de dialogue d'édition pour les types de cellules avancés du
bloc Tableau (PATCH 15) : Personne, Liste multiple, Checklist, et
choix du type/nom/options à la création d'une colonne.

Isolées ici pour garder `table_block_widget.py` centré sur la grille.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from blocks.table_block import (
    COLUMN_TYPE_DATE,
    COLUMN_TYPE_LABELS,
    COLUMN_TYPE_NUMBER,
    COLUMN_TYPE_SELECT,
    COLUMN_TYPE_MULTI_SELECT,
    COLUMN_TYPES,
)
from ui.no_scroll_combo_box import NoScrollComboBox


def ask_column_definition(
    parent,
    name: str = "",
    col_type: str = "text",
    options: list[str] | None = None,
    date_range: bool = False,
    unit: str = "",
) -> tuple[str, str, list[str], bool, str] | None:
    """Dialogue de création/édition de colonne : nom, type, options, plage, unité.

    `unit` (PATCH 56) n'est pertinente que pour une colonne "Nombre" —
    affichée dans l'en-tête ("j", "€", "%", ...) à la place du type.

    Retourne (name, col_type, options, date_range, unit) ou None si annulé.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle("Colonne")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Nom :"))
    name_edit = QLineEdit(name, dialog)
    layout.addWidget(name_edit)

    layout.addWidget(QLabel("Type :"))
    type_combo = NoScrollComboBox(dialog)
    for type_key in COLUMN_TYPES:
        type_combo.addItem(COLUMN_TYPE_LABELS[type_key], type_key)
    type_combo.setCurrentIndex(max(0, COLUMN_TYPES.index(col_type) if col_type in COLUMN_TYPES else 0))
    layout.addWidget(type_combo)

    options_label = QLabel("Choix possibles (séparés par des virgules) :")
    options_edit = QLineEdit(", ".join(options or []), dialog)
    layout.addWidget(options_label)
    layout.addWidget(options_edit)

    range_checkbox = QCheckBox("Plage de dates (début / fin)", dialog)
    range_checkbox.setChecked(date_range)
    layout.addWidget(range_checkbox)

    unit_label = QLabel("Unité affichée dans l'en-tête (ex : j, €, %) :")
    unit_edit = QLineEdit(unit, dialog)
    layout.addWidget(unit_label)
    layout.addWidget(unit_edit)

    def _sync_visibility() -> None:
        current_type = type_combo.currentData()
        is_choice_type = current_type in (COLUMN_TYPE_SELECT, COLUMN_TYPE_MULTI_SELECT)
        options_label.setVisible(is_choice_type)
        options_edit.setVisible(is_choice_type)
        range_checkbox.setVisible(current_type == COLUMN_TYPE_DATE)
        is_number_type = current_type == COLUMN_TYPE_NUMBER
        unit_label.setVisible(is_number_type)
        unit_edit.setVisible(is_number_type)

    type_combo.currentIndexChanged.connect(_sync_visibility)
    _sync_visibility()

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec() != QDialog.Accepted:
        return None

    parsed_options = [part.strip() for part in options_edit.text().split(",") if part.strip()]
    return (
        name_edit.text(),
        type_combo.currentData(),
        parsed_options,
        range_checkbox.isChecked(),
        unit_edit.text().strip(),
    )


def edit_person_list(parent, document, selected_ids: list[str]) -> list[str] | None:
    """Dialogue d'édition d'une cellule "Personne" (PATCH 16).

    Coche les personnes du registre partagé de `document` à assigner à
    cette cellule. Permet aussi de créer une nouvelle personne à la
    volée (elle rejoint alors le registre partagé, réutilisable dans
    toutes les autres cellules "Personne" du document).
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle("Personnes assignées")
    layout = QVBoxLayout(dialog)

    list_widget = QListWidget(dialog)

    def _populate() -> None:
        list_widget.clear()
        for person in document.people:
            item = QListWidgetItem(person["name"])
            item.setData(Qt.UserRole, person["id"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if person["id"] in selected_ids else Qt.Unchecked)
            item.setForeground(QColor(person.get("color", "#000000")))
            list_widget.addItem(item)

    _populate()
    layout.addWidget(list_widget)

    add_row = QHBoxLayout()
    name_edit = QLineEdit(dialog)
    name_edit.setPlaceholderText("Nouvelle personne...")
    add_row.addWidget(name_edit)

    def _add_person() -> None:
        text = name_edit.text().strip()
        if not text:
            return
        person = document.add_person(text)
        selected_ids.append(person["id"])
        name_edit.clear()
        _populate()

    add_button = QPushButton("Ajouter", dialog)
    add_button.clicked.connect(_add_person)
    name_edit.returnPressed.connect(_add_person)
    add_row.addWidget(add_button)
    layout.addLayout(add_row)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec() != QDialog.Accepted:
        return None
    return [
        list_widget.item(i).data(Qt.UserRole)
        for i in range(list_widget.count())
        if list_widget.item(i).checkState() == Qt.Checked
    ]


def edit_multi_select(parent, options: list[str], selected: list[str]) -> list[str] | None:
    """Dialogue de sélection multiple parmi les choix de la colonne."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Choix multiples")
    layout = QVBoxLayout(dialog)

    if not options:
        layout.addWidget(QLabel("Aucun choix défini pour cette colonne."))

    checkboxes: list[QCheckBox] = []
    for option in options:
        checkbox = QCheckBox(option, dialog)
        checkbox.setChecked(option in selected)
        layout.addWidget(checkbox)
        checkboxes.append(checkbox)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec() != QDialog.Accepted:
        return None
    return [checkbox.text() for checkbox in checkboxes if checkbox.isChecked()]


def edit_checklist_cell(parent, items: list[dict]) -> list[dict] | None:
    """Dialogue d'édition d'une mini-checklist stockée dans une cellule."""
    import uuid

    dialog = QDialog(parent)
    dialog.setWindowTitle("Checklist")
    layout = QVBoxLayout(dialog)

    rows_container = QVBoxLayout()
    layout.addLayout(rows_container)

    working_items = [dict(item) for item in items]
    row_widgets: list[tuple[QWidget, QCheckBox, QLineEdit]] = []

    def _rebuild_rows() -> None:
        while rows_container.count():
            item = rows_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        row_widgets.clear()
        for entry in working_items:
            row_widget = QWidget(dialog)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            checkbox = QCheckBox(row_widget)
            checkbox.setChecked(entry.get("checked", False))
            line_edit = QLineEdit(entry.get("text", ""), row_widget)
            remove_btn = QPushButton("×", row_widget)
            remove_btn.setFixedWidth(24)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(line_edit, 1)
            row_layout.addWidget(remove_btn)
            rows_container.addWidget(row_widget)
            row_widgets.append((row_widget, checkbox, line_edit))
            remove_btn.clicked.connect(lambda _, e=entry: (working_items.remove(e), _rebuild_rows()))

    _rebuild_rows()

    add_button = QPushButton("+ Ajouter un élément", dialog)

    def _add_item() -> None:
        working_items.append({"id": str(uuid.uuid4()), "text": "", "checked": False})
        _rebuild_rows()

    add_button.clicked.connect(_add_item)
    layout.addWidget(add_button)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec() != QDialog.Accepted:
        return None

    result = []
    for entry, (_, checkbox, line_edit) in zip(working_items, row_widgets):
        result.append({"id": entry["id"], "text": line_edit.text(), "checked": checkbox.isChecked()})
    return result
