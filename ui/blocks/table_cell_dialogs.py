"""
Boîtes de dialogue d'édition pour les types de cellules avancés du
bloc Tableau (PATCH 15) : Personne, Liste multiple, Checklist, et
choix du type/nom/options à la création d'une colonne.

Isolées ici pour garder `table_block_widget.py` centré sur la grille.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from blocks.table_block import COLUMN_TYPE_LABELS, COLUMN_TYPE_SELECT, COLUMN_TYPE_MULTI_SELECT, COLUMN_TYPES


def ask_column_definition(
    parent, name: str = "", col_type: str = "text", options: list[str] | None = None
) -> tuple[str, str, list[str]] | None:
    """Dialogue de création/édition de colonne : nom, type, options.

    Retourne (name, col_type, options) ou None si annulé.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle("Colonne")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Nom :"))
    name_edit = QLineEdit(name, dialog)
    layout.addWidget(name_edit)

    layout.addWidget(QLabel("Type :"))
    type_combo = QComboBox(dialog)
    for type_key in COLUMN_TYPES:
        type_combo.addItem(COLUMN_TYPE_LABELS[type_key], type_key)
    type_combo.setCurrentIndex(max(0, COLUMN_TYPES.index(col_type) if col_type in COLUMN_TYPES else 0))
    layout.addWidget(type_combo)

    options_label = QLabel("Choix possibles (séparés par des virgules) :")
    options_edit = QLineEdit(", ".join(options or []), dialog)
    layout.addWidget(options_label)
    layout.addWidget(options_edit)

    def _sync_options_visibility() -> None:
        is_choice_type = type_combo.currentData() in (COLUMN_TYPE_SELECT, COLUMN_TYPE_MULTI_SELECT)
        options_label.setVisible(is_choice_type)
        options_edit.setVisible(is_choice_type)

    type_combo.currentIndexChanged.connect(_sync_options_visibility)
    _sync_options_visibility()

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec() != QDialog.Accepted:
        return None

    parsed_options = [part.strip() for part in options_edit.text().split(",") if part.strip()]
    return name_edit.text(), type_combo.currentData(), parsed_options


def edit_person_list(parent, current: list[str]) -> list[str] | None:
    """Dialogue d'édition de la colonne "Personne" : liste de noms libres."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Personnes")
    layout = QVBoxLayout(dialog)

    list_widget = QListWidget(dialog)
    list_widget.addItems(current)
    layout.addWidget(list_widget)

    add_row = QHBoxLayout()
    name_edit = QLineEdit(dialog)
    name_edit.setPlaceholderText("Nom...")
    add_row.addWidget(name_edit)

    def _add_name() -> None:
        text = name_edit.text().strip()
        if text:
            list_widget.addItem(QListWidgetItem(text))
            name_edit.clear()

    add_button = QPushButton("Ajouter", dialog)
    add_button.clicked.connect(_add_name)
    name_edit.returnPressed.connect(_add_name)
    add_row.addWidget(add_button)
    layout.addLayout(add_row)

    remove_button = QPushButton("Supprimer la sélection", dialog)
    remove_button.clicked.connect(lambda: [list_widget.takeItem(list_widget.row(i)) for i in list_widget.selectedItems()])
    layout.addWidget(remove_button)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec() != QDialog.Accepted:
        return None
    return [list_widget.item(i).text() for i in range(list_widget.count())]


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
