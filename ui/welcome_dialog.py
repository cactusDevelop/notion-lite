"""
PATCH 63 — Écran d'accueil affiché au démarrage, façon VS Code /
JetBrains : créer un nouveau projet (template ou vide), ouvrir un
projet existant, ou reprendre l'un des projets récents.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.version import __version__


class WelcomeDialog(QDialog):
    """Popup modale de démarrage.

    Après `exec()`, si `result() == QDialog.Accepted`, le choix de
    l'utilisateur est disponible via `result_action` (l'une des
    constantes ACTION_*) et, pour ACTION_OPEN, `result_path`.
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
                item = QListWidgetItem(path.name)
                item.setToolTip(str(path))
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
        self.result_action = self.ACTION_NEW_TEMPLATE
        self.accept()

    def _choose_new_blank(self) -> None:
        self.result_action = self.ACTION_NEW_BLANK
        self.accept()

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
