"""
Fenêtre principale de Notion Lite.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QTextEdit,
    QWidget,
)

from blocks.checklist_block import ChecklistBlock
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.text_block import TextBlock
from core.document import Document
from ui.blocks.block_container import BlockContainer
from ui.blocks.checklist_block_widget import ChecklistBlockWidget
from ui.blocks.heading_block_widget import HeadingBlockWidget
from ui.blocks.image_block_widget import ImageBlockWidget
from ui.blocks.text_block_widget import TextBlockWidget
from ui.blocks_area import BlocksArea
from ui.info_dialog import InfoDialog
from ui.toolbar import MainToolBar

# Racine du projet (deux niveaux au-dessus de ce fichier : ui/main_window.py).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_INFO_ICON_PATH = str(_PROJECT_ROOT / "icon-info.svg")


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application.

    Affiche le document sous forme d'une colonne de blocs, expose une
    toolbar de mise en forme (PATCH 5 et 6), gère une expérience de
    curseur multi-blocs façon Notion (PATCH 7) et permet de réordonner
    n'importe quel bloc par glisser-déposer (PATCH 13).
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Notion Lite")
        self.resize(1000, 700)

        self._document = Document()
        self._active_text_widget: TextBlockWidget | None = None
        self._current_file: Path | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Prépare la toolbar, la zone de contenu et affiche le document."""
        toolbar = MainToolBar(
            actions={
                "new_block": lambda: self._add_text_block(),
                "new_checklist": self._add_checklist_block,
                "new_image": self._add_image_block,
                "bold": self._with_active(TextBlockWidget.toggle_bold),
                "italic": self._with_active(TextBlockWidget.toggle_italic),
                "underline": self._with_active(TextBlockWidget.toggle_underline),
                "strikethrough": self._with_active(TextBlockWidget.toggle_strikethrough),
                "align_left": self._with_active(lambda w: w.set_alignment(Qt.AlignLeft)),
                "align_center": self._with_active(lambda w: w.set_alignment(Qt.AlignCenter)),
                "align_right": self._with_active(lambda w: w.set_alignment(Qt.AlignRight)),
                "align_justify": self._with_active(lambda w: w.set_alignment(Qt.AlignJustify)),
                "bullet_list": self._with_active(TextBlockWidget.toggle_bullet_list),
                "numbered_list": self._with_active(TextBlockWidget.toggle_numbered_list),
                "quote": self._with_active(TextBlockWidget.toggle_quote),
                "code": self._with_active(TextBlockWidget.toggle_code),
                "color": self._apply_color,
            },
            on_size_changed=self._apply_size,
            on_info=self._show_info_dialog,
            info_icon_path=_INFO_ICON_PATH,
        )
        self.addToolBar(toolbar)
        self._setup_file_menu()

        central = BlocksArea(on_block_dropped=self._on_block_dropped)
        self._blocks_layout = central.blocks_layout
        self.setCentralWidget(central)

        # Document de démonstration pour valider les PATCH 3 et 4.
        self._document.add_block(HeadingBlock(level=1, content="Titre principal"))
        self._document.add_block(HeadingBlock(level=2, content="Sous-titre"))
        self._document.add_block(HeadingBlock(level=3, content="Petit titre"))
        self._document.add_block(
            TextBlock(content="Ceci est un bloc de texte modifiable.")
        )
        checklist_demo = ChecklistBlock()
        checklist_demo.add_item("Première tâche", checked=False)
        checklist_demo.add_item("Deuxième tâche", checked=True)
        self._document.add_block(checklist_demo)
        self._render_document(focus_last=True)

    def _setup_file_menu(self) -> None:
        """Menu Fichier : Nouveau / Ouvrir / Sauvegarder / Sauvegarder sous (PATCH 8)."""
        file_menu = self.menuBar().addMenu("&Fichier")

        new_action = QAction("Nouveau", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_document)
        file_menu.addAction(new_action)

        open_action = QAction("Ouvrir...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_document)
        file_menu.addAction(open_action)

        save_action = QAction("Sauvegarder", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_document)
        file_menu.addAction(save_action)

        save_as_action = QAction("Sauvegarder sous...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._save_document_as)
        file_menu.addAction(save_as_action)

    # -- Mise en forme (PATCH 5 / 6) -------------------------------------

    def _with_active(self, method):
        """Enveloppe une méthode de TextBlockWidget pour l'appliquer
        au bloc texte actuellement focus, s'il y en a un."""

        def handler() -> None:
            if self._active_text_widget is not None:
                method(self._active_text_widget)

        return handler

    def _on_text_widget_focused(self, widget: TextBlockWidget) -> None:
        self._active_text_widget = widget

    def _apply_color(self) -> None:
        if self._active_text_widget is None:
            return
        color = QColorDialog.getColor(QColor("black"), self, "Choisir une couleur")
        if color.isValid():
            self._active_text_widget.set_text_color(color)

    def _apply_size(self, size: int) -> None:
        if self._active_text_widget is not None:
            self._active_text_widget.set_font_size(size)

    def _show_info_dialog(self) -> None:
        """Ouvre la popup listant les explications et choix de design."""
        InfoDialog(self).exec()

    # -- Rendu générique des blocs / drag & drop (PATCH 8, 13) ------------

    def _create_content_widget_for_block(self, block) -> QWidget:
        """Crée le widget métier adapté au type d'un bloc (sans poignée)."""
        if isinstance(block, TextBlock):
            return self._create_text_widget(block)
        if isinstance(block, HeadingBlock):
            return HeadingBlockWidget(block)
        if isinstance(block, ChecklistBlock):
            return ChecklistBlockWidget(block)
        if isinstance(block, ImageBlock):
            return ImageBlockWidget(
                block,
                on_move_up=lambda block_id=block.id: self._move_block(block_id, -1),
                on_move_down=lambda block_id=block.id: self._move_block(block_id, 1),
                on_delete=lambda block_id=block.id: self._delete_block(block_id),
            )
        raise ValueError(f"Type de bloc non pris en charge à l'affichage : {block.type}")

    def _wrap(self, content: QWidget, block_id: str) -> BlockContainer:
        """PATCH 13 — Ajoute la poignée de glisser-déposer à un widget de bloc."""
        return BlockContainer(content, block_id)

    def _find_container(self, content_widget: QWidget) -> tuple[int, BlockContainer | None]:
        """Retrouve (index dans le layout, BlockContainer) d'un widget de contenu."""
        for i in range(self._blocks_layout.count()):
            item = self._blocks_layout.itemAt(i)
            widget = item.widget() if item else None
            if isinstance(widget, BlockContainer) and widget.content is content_widget:
                return i, widget
        return -1, None

    def _layout_index_of_content(self, content_widget: QWidget) -> int:
        return self._find_container(content_widget)[0]

    def _content_widget_at(self, layout_index: int) -> QWidget | None:
        item = self._blocks_layout.itemAt(layout_index)
        widget = item.widget() if item else None
        return widget.content if isinstance(widget, BlockContainer) else None

    def _render_document(self, focus_last: bool = False) -> None:
        """(Re)construit entièrement l'affichage à partir de self._document."""
        self._active_text_widget = None
        while self._blocks_layout.count():
            item = self._blocks_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        last_content: QWidget | None = None
        for block in self._document.blocks:
            last_content = self._create_content_widget_for_block(block)
            self._blocks_layout.addWidget(self._wrap(last_content, block.id))

        if focus_last and last_content is not None:
            last_content.setFocus()

    def _on_block_dropped(self, block_id: str, target_index: int) -> None:
        """PATCH 13 — Réordonne le document après un glisser-déposer."""
        current_index = next(
            (i for i, b in enumerate(self._document.blocks) if b.id == block_id), None
        )
        if current_index is None:
            return
        if target_index > current_index:
            target_index -= 1  # le bloc quitte sa position avant d'être réinséré
        if target_index == current_index:
            return
        self._document.move_block(block_id, target_index)
        self._render_document()

    # -- Sauvegarde / chargement (PATCH 8) --------------------------------

    def _set_current_file(self, path: Path | None) -> None:
        self._current_file = path
        self.setWindowTitle("Notion Lite" + (f" — {path.name}" if path else ""))

    def _new_document(self) -> None:
        """PATCH 8 — Nouveau : repart d'un document vide."""
        self._document = Document()
        self._set_current_file(None)
        self._render_document()

    def _open_document(self) -> None:
        """PATCH 8 — Ouvrir : charge un document depuis un fichier JSON."""
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un document", "", "Notion Lite (*.json)"
        )
        if not path_str:
            return

        try:
            raw = json.loads(Path(path_str).read_text(encoding="utf-8"))
            document = Document.from_dict(raw)
        except (OSError, ValueError, KeyError) as exc:
            QMessageBox.critical(
                self, "Erreur d'ouverture", f"Impossible d'ouvrir le fichier :\n{exc}"
            )
            return

        self._document = document
        self._set_current_file(Path(path_str))
        self._render_document()

    def _write_document(self, path: Path) -> None:
        try:
            path.write_text(
                json.dumps(self._document.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            QMessageBox.critical(
                self, "Erreur de sauvegarde", f"Impossible d'enregistrer le fichier :\n{exc}"
            )
            return
        self._set_current_file(path)

    def _save_document(self) -> None:
        """PATCH 8 — Sauvegarder : réutilise le fichier courant, sinon demande où."""
        if self._current_file is None:
            self._save_document_as()
            return
        self._write_document(self._current_file)

    def _save_document_as(self) -> None:
        """PATCH 8 — Sauvegarder sous : demande toujours un nouveau fichier."""
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder sous", "", "Notion Lite (*.json)"
        )
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix != ".json":
            path = path.with_suffix(".json")
        self._write_document(path)

    # -- Gestion des blocs texte -----------------------------------------

    def _create_text_widget(self, block: TextBlock) -> TextBlockWidget:
        """Crée un TextBlockWidget entièrement connecté."""
        widget = TextBlockWidget(block)
        widget.focused.connect(self._on_text_widget_focused)
        widget.split_requested.connect(self._on_split_requested)
        widget.merge_requested.connect(self._on_merge_requested)
        widget.delete_requested.connect(self._on_delete_requested)
        return widget

    def _add_text_block(self, content: str = "") -> None:
        """Ajoute un nouveau bloc texte au document et à l'affichage."""
        block = TextBlock(content=content)
        self._document.add_block(block)

        widget = self._create_text_widget(block)
        self._blocks_layout.addWidget(self._wrap(widget, block.id))
        widget.setFocus()

    def _add_checklist_block(self) -> None:
        """Ajoute un nouveau bloc checklist (PATCH 10), avec un premier élément vide."""
        block = ChecklistBlock()
        block.add_item()
        self._document.add_block(block)

        widget = ChecklistBlockWidget(block)
        self._blocks_layout.addWidget(self._wrap(widget, block.id))

    def _add_image_block(self) -> None:
        """PATCH 12 — Insère une image choisie sur le disque, en fin de document."""
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Insérer une image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            QMessageBox.critical(
                self, "Erreur d'insertion", f"Impossible de lire l'image :\n{exc}"
            )
            return

        block = ImageBlock(
            image_base64=base64.b64encode(raw_bytes).decode("ascii"),
            image_format=path.suffix.lstrip(".").lower() or "png",
        )
        self._document.add_block(block)
        content = self._create_content_widget_for_block(block)
        self._blocks_layout.addWidget(self._wrap(content, block.id))

    def _move_block(self, block_id: str, delta: int) -> None:
        """PATCH 12 — Déplace un bloc (image, checklist, ...) d'une position."""
        index = next(
            (i for i, b in enumerate(self._document.blocks) if b.id == block_id), None
        )
        if index is None:
            return
        self._document.move_block(block_id, index + delta)
        self._render_document()

    def _delete_block(self, block_id: str) -> None:
        """PATCH 12 — Supprime un bloc (image, ...) du document."""
        self._document.remove_block(block_id)
        self._render_document()

    @staticmethod
    def _focus_widget_at_end(widget: QWidget) -> None:
        """Donne le focus à un widget de bloc et place le curseur à la fin."""
        widget.setFocus()
        if isinstance(widget, QTextEdit):
            cursor = widget.textCursor()
            cursor.movePosition(QTextCursor.End)
            widget.setTextCursor(cursor)
        elif isinstance(widget, QLineEdit):
            widget.end(False)

    # -- Gestion du curseur multi-blocs (PATCH 7) -------------------------

    def _on_split_requested(self, widget: TextBlockWidget, before: str, after: str) -> None:
        """Sépare un bloc en deux à la position du curseur."""
        widget.setPlainText(before)

        new_block = TextBlock(content=after)
        doc_index = self._document.blocks.index(widget.block)
        self._document.add_block(new_block, index=doc_index + 1)

        layout_index = self._layout_index_of_content(widget)
        new_widget = self._create_text_widget(new_block)
        self._blocks_layout.insertWidget(layout_index + 1, self._wrap(new_widget, new_block.id))

        new_widget.setFocus()
        cursor = new_widget.textCursor()
        cursor.movePosition(QTextCursor.Start)
        new_widget.setTextCursor(cursor)

    def _on_merge_requested(self, widget: TextBlockWidget) -> None:
        """Fusionne un bloc texte non vide avec le bloc texte précédent."""
        layout_index = self._layout_index_of_content(widget)
        if layout_index <= 0:
            return

        previous_widget = self._content_widget_at(layout_index - 1)
        if not isinstance(previous_widget, TextBlockWidget):
            return  # fusion uniquement entre deux blocs texte pour l'instant

        merge_position = len(previous_widget.toPlainText())
        previous_widget.setPlainText(previous_widget.toPlainText() + widget.toPlainText())

        self._remove_text_block(widget)

        previous_widget.setFocus()
        cursor = previous_widget.textCursor()
        cursor.setPosition(merge_position)
        previous_widget.setTextCursor(cursor)

    def _on_delete_requested(self, widget: TextBlockWidget) -> None:
        """Supprime un bloc texte vide et redonne le focus au précédent."""
        layout_index = self._layout_index_of_content(widget)
        if layout_index <= 0:
            return

        previous_widget = self._content_widget_at(layout_index - 1)

        self._remove_text_block(widget)

        if previous_widget is not None:
            self._focus_widget_at_end(previous_widget)

    def _remove_text_block(self, widget: TextBlockWidget) -> None:
        """Retire un bloc texte du document et de l'affichage."""
        self._document.remove_block(widget.block.id)
        _, container = self._find_container(widget)
        if container is not None:
            self._blocks_layout.removeWidget(container)
            container.deleteLater()
        if self._active_text_widget is widget:
            self._active_text_widget = None
