"""
PATCH 66 — Écran d'accueil affiché au démarrage, façon VS Code /
JetBrains : créer un nouveau projet (nom + emplacement, comme un vrai
IDE), ouvrir un projet existant, ou reprendre l'un des projets récents
(affichés par dossier projet, pas par fichier).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.version import __version__

# PATCH 66 — Caractères interdits dans un nom de dossier sur Windows /
# macOS / Linux ; retirés du nom de projet saisi.
_INVALID_NAME_CHARS = re.compile(r'[\\/:*?"<>|]')


class NewProjectDialog(QDialog):
    """PATCH 66 — Sous-dialogue "Nouveau projet" façon PyCharm/VS Code :
    un nom de projet + un emplacement parent, avec aperçu du dossier
    final qui sera créé (emplacement/nom)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouveau projet")
        self.setModal(True)
        self.setMinimumWidth(420)

        self.project_path: Optional[Path] = None
        self._location = Path.home()

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Mon projet")
        self._name_edit.textChanged.connect(self._update_preview)
        form.addRow("Nom du projet", self._name_edit)

        location_row = QHBoxLayout()
        self._location_edit = QLineEdit(str(self._location))
        self._location_edit.setReadOnly(True)
        location_row.addWidget(self._location_edit)
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self._browse_location)
        location_row.addWidget(browse_button)
        location_widget = QWidget()
        location_widget.setLayout(location_row)
        form.addRow("Emplacement", location_widget)
        layout.addLayout(form)

        self._preview_label = QLabel()
        self._preview_label.setStyleSheet("color: gray;")
        self._preview_label.setWordWrap(True)
        layout.addWidget(self._preview_label)
        self._update_preview()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_location(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Emplacement du projet", str(self._location))
        if folder:
            self._location = Path(folder)
            self._location_edit.setText(str(self._location))
            self._update_preview()

    def _sanitized_name(self) -> str:
        return _INVALID_NAME_CHARS.sub("", self._name_edit.text().strip()).strip()

    def _update_preview(self) -> None:
        name = self._sanitized_name() or "<nom du projet>"
        self._preview_label.setText(f"Sera créé dans : {self._location / name}")

    def _on_accept(self) -> None:
        name = self._sanitized_name()
        if not name:
            QMessageBox.warning(self, "Nom manquant", "Merci de donner un nom au projet.")
            return
        target = self._location / name
        if target.exists():
            QMessageBox.warning(
                self,
                "Dossier existant",
                f"Un dossier « {name} » existe déjà à cet emplacement.\n"
                "Choisis un autre nom ou un autre emplacement.",
            )
            return
        self.project_path = target
        self.accept()


class WelcomeDialog(QDialog):
    """Popup modale de démarrage.

    Après `exec()`, si `result() == QDialog.Accepted`, le choix de
    l'utilisateur est disponible via `result_action` (l'une des
    constantes ACTION_*), `result_folder` (dossier du projet, pour
    ACTION_NEW_TEMPLATE / ACTION_NEW_BLANK) et `result_path` (fichier à
    ouvrir, pour ACTION_OPEN).
    """

    ACTION_NEW_TEMPLATE = "new_template"
    ACTION_NEW_BLANK = "new_blank"
    ACTION_OPEN = "open"

    def __init__(self, recent_files: list[Path], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Bienvenue dans Notion Lite")
        self.setModal(True)
        self.setMinimumSize(640, 420)

        self.result_action: Optional[str] = None
        self.result_path: Optional[Path] = None
        # PATCH 65/66 — Dossier de projet (nouveau ou récent) ; sert de
        # racine à l'explorateur de fichiers (façon IDE).
        self.result_folder: Optional[Path] = None

        root = QHBoxLayout(self)

        # -- Colonne gauche : identité + actions rapides -----------------
        left = QVBoxLayout()
        title = QLabel("Notion Lite")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        left.addWidget(title)
        subtitle = QLabel(f"version {__version__}")
        subtitle.setStyleSheet("color: gray;")
        left.addWidget(subtitle)
        left.addSpacing(24)

        new_template_button = QPushButton("＋  Nouveau projet (Modèle OG)")
        new_template_button.setDefault(True)
        new_template_button.clicked.connect(self._choose_new_template)
        left.addWidget(new_template_button)

        new_blank_button = QPushButton("＋  Nouveau document vide")
        new_blank_button.clicked.connect(self._choose_new_blank)
        left.addWidget(new_blank_button)

        open_button = QPushButton("📂  Ouvrir un projet...")
        open_button.clicked.connect(self._choose_open)
        left.addWidget(open_button)

        left.addStretch()
        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setFixedWidth(240)
        root.addWidget(left_widget)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        root.addWidget(separator)

        # -- Colonne droite : projets récents -----------------------------
        right = QVBoxLayout()
        right.addWidget(QLabel("Projets récents"))

        self._recent_list = QListWidget()
        self._recent_list.setAlternatingRowColors(True)
        if recent_files:
            for path in recent_files:
                # PATCH 66 — Un "projet" est un dossier (celui qui contient
                # le fichier .json) : c'est ce dossier qu'on affiche et
                # qu'on rouvrira en racine de l'explorateur, pas le nom
                # interne du fichier.
                project_folder = path.parent
                item = QListWidgetItem(project_folder.name)
                item.setToolTip(str(project_folder))
                item.setData(Qt.UserRole, str(path))
                self._recent_list.addItem(item)
        else:
            placeholder = QListWidgetItem("(aucun projet récent)")
            placeholder.setFlags(Qt.ItemIsEnabled)
            self._recent_list.addItem(placeholder)
        self._recent_list.itemDoubleClicked.connect(self._activate_recent_item)
        right.addWidget(self._recent_list)

        root.addLayout(right)

    # -- Choix de l'utilisateur -------------------------------------------

    def _choose_new_template(self) -> None:
        folder = self._create_project_folder()
        if folder is None:
            return
        self.result_action = self.ACTION_NEW_TEMPLATE
        self.result_folder = folder
        self.accept()

    def _choose_new_blank(self) -> None:
        folder = self._create_project_folder()
        if folder is None:
            return
        self.result_action = self.ACTION_NEW_BLANK
        self.result_folder = folder
        self.accept()

    def _create_project_folder(self) -> Optional[Path]:
        """PATCH 66 — Demande un nom + un emplacement (façon IDE), crée
        le dossier projet correspondant. Retourne None si l'utilisateur
        annule (la popup d'accueil reste ouverte)."""
        dialog = NewProjectDialog(self)
        if dialog.exec() != QDialog.Accepted or dialog.project_path is None:
            return None
        try:
            dialog.project_path.mkdir(parents=True)
        except OSError as exc:
            QMessageBox.critical(
                self, "Erreur", f"Impossible de créer le dossier du projet :\n{exc}"
            )
            return None
        return dialog.project_path

    def _choose_open(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(self, "Ouvrir un projet", "", "Notion Lite (*.json)")
        if not path_str:
            return
        self.result_action = self.ACTION_OPEN
        self.result_path = Path(path_str)
        self.accept()

    def _activate_recent_item(self, item: QListWidgetItem) -> None:
        path_str = item.data(Qt.UserRole)
        if not path_str:
            return
        self.result_action = self.ACTION_OPEN
        self.result_path = Path(path_str)
        self.accept()
