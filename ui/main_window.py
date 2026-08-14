"""
Fenêtre principale de Méthodo OG.
"""
from __future__ import annotations

import base64
import json
import shutil
import uuid
from pathlib import Path

from PySide6.QtCore import QEvent, QModelIndex, QPoint, QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QColorDialog,
    QDialog,
    QDockWidget,
    QFileDialog,
    QFileSystemModel,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.formula_block import FormulaBlock
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.bar_chart_block import BarChartBlock
from blocks.dependency_gantt_block import DependencyGanttBlock
from blocks.line_chart_block import LineChartBlock
from blocks.gantt_block import GanttBlock
from blocks.linked_checklist_block import LinkedChecklistBlock
from blocks.list_block import ListBlock
from blocks.people_list_block import PeopleListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import TableBlock
from blocks.registry import block_from_dict
from blocks.text_block import TextBlock
from core.block_icons import icon_for_block
from core.block_preview import preview_for_block
from core.document import Document
from core.history import UndoHistory
from core.project_meta import ProjectMeta
from core.project_template import build_project_template
from core.version import __version__
from ui.blocks.block_container import BlockContainer
from ui.blocks.checklist_block_widget import ChecklistBlockWidget
from ui.blocks.code_block_widget import CodeBlockWidget
from ui.blocks.formula_block_widget import FormulaBlockWidget
from ui.blocks.bar_chart_block_widget import BarChartBlockWidget
from ui.blocks.dependency_gantt_block_widget import DependencyGanttBlockWidget
from ui.blocks.line_chart_block_widget import LineChartBlockWidget
from ui.blocks.gantt_block_widget import GanttBlockWidget
from ui.blocks.heading_block_widget import HeadingBlockWidget
from ui.blocks.image_block_widget import ImageBlockWidget
from ui.blocks.linked_checklist_block_widget import LinkedChecklistBlockWidget
from ui.blocks.list_block_widget import ListBlockWidget
from ui.blocks.people_list_block_widget import PeopleListBlockWidget
from ui.blocks.quote_block_widget import QuoteBlockWidget
from ui.blocks.separator_block_widget import SeparatorBlockWidget
from ui.blocks.simple_table_block_widget import SimpleTableBlockWidget
from ui.blocks.table_block_widget import TableBlockWidget
from ui.blocks.text_block_widget import TextBlockWidget
from ui.block_picker_dialog import BlockPickerDialog
from ui.blocks_area import BlocksArea
from ui.command_menu import CommandMenu
from ui.command_registry import get_commands
from ui.emoji_picker import EmojiPicker
from ui.export_pdf import export_document_to_pdf
from ui.i18n import LANGUAGES, get_language, set_language, tr
from ui.info_dialog import InfoDialog
from ui.people_manager_dialog import PeopleManagerDialog
from ui.search_dialog import SearchDialog
from ui.themes.theme import (
    THEME_DARK,
    THEME_LABELS,
    THEMES,
    apply_theme,
    current_theme,
    toggle_theme,
)
from ui.settings import (
    get_autosave_enabled,
    get_block_spacing,
    set_autosave_enabled,
    set_block_spacing,
)
from ui.toolbar import MainToolBar
from ui.welcome_dialog import WelcomeDialog

# Racine du projet (deux niveaux au-dessus de ce fichier : ui/main_window.py).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_INFO_ICON_PATH = str(_PROJECT_ROOT / "icon-info.svg")

# PATCH 52 — Identifiants QSettings utilisés pour mémoriser, entre deux
# lancements de l'application, le chemin du dernier document sauvegardé
# ou ouvert (voir _load_startup_document / _set_current_file), afin de
# rouvrir automatiquement la dernière session au démarrage.
_SETTINGS_ORG = "MethodoOG"
_SETTINGS_APP = "MethodoOG"
_SETTINGS_LAST_FILE_KEY = "last_file"
# PATCH 53 — dossier affiché dans l'explorateur de fichiers latéral,
# mémorisé entre deux lancements comme _SETTINGS_LAST_FILE_KEY.
_SETTINGS_LAST_FOLDER_KEY = "last_folder"
# PATCH 63 — liste des derniers projets ouverts/sauvegardés, affichée
# dans l'écran d'accueil (voir WelcomeDialog).
_SETTINGS_RECENT_FILES_KEY = "recent_files"
_MAX_RECENT_FILES = 8


def _get_recent_files() -> list[Path]:
    """PATCH 63 — Liste des projets récents encore présents sur le
    disque, du plus récent au plus ancien."""
    settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    raw = settings.value(_SETTINGS_RECENT_FILES_KEY, [])
    if isinstance(raw, str):
        raw = [raw] if raw else []
    return [path for path in (Path(p) for p in raw) if path.is_file()]


def _add_recent_file(path: Path) -> None:
    """PATCH 63 — Place `path` en tête des projets récents (sans doublon),
    en conservant au plus _MAX_RECENT_FILES entrées."""
    settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    existing = [str(p) for p in _get_recent_files() if p != path]
    updated = [str(path)] + existing
    settings.setValue(_SETTINGS_RECENT_FILES_KEY, updated[:_MAX_RECENT_FILES])


def _remove_recent_file(path: Path) -> None:
    """PATCH 68 — Retire `path` de la liste des projets récents (croix
    dans l'écran d'accueil), sans toucher au fichier sur le disque."""
    settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    existing = [str(p) for p in _get_recent_files() if p != path]
    settings.setValue(_SETTINGS_RECENT_FILES_KEY, existing)


def _load_startup_document() -> tuple[Document, Path | None]:
    """PATCH 52 — Reprend automatiquement la dernière session : recharge
    le dernier fichier sauvegardé/ouvert mémorisé (QSettings), si le
    fichier existe et reste lisible. Sinon (premier lancement, fichier
    déplacé/supprimé, ou invalide), repart du template par défaut."""
    settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    path_str = settings.value(_SETTINGS_LAST_FILE_KEY, "")
    if path_str:
        path = Path(path_str)
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                return Document.from_dict(raw), path
            except (OSError, ValueError, KeyError):
                pass
    return build_project_template(), None


# PATCH 27 — Intervalle (ms) du sondage qui regroupe les frappes rapides
# (édition de texte) en un seul point d'annulation ("undo" par pause,
# pas par caractère). Ctrl+Z force de toute façon un flush immédiat.
_UNDO_POLL_INTERVAL_MS = 600

# PATCH 26 — Cibles de conversion proposées dans le menu contextuel :
# uniquement les blocs à contenu texte simple (voir _create_content_widget_for_block).
def _convert_targets() -> list[tuple[str, str]]:
    return [
        ("text", tr("context.convert.text")),
        ("heading1", tr("context.convert.heading1")),
        ("heading2", tr("context.convert.heading2")),
        ("heading3", tr("context.convert.heading3")),
        ("quote", tr("context.convert.quote")),
        ("code", tr("context.convert.code")),
    ]


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application.

    Affiche le document sous forme d'une colonne de blocs, expose une
    toolbar de mise en forme (PATCH 5 et 6), gère une expérience de
    curseur multi-blocs façon Notion (PATCH 7) et permet de réordonner
    n'importe quel bloc par glisser-déposer (PATCH 13).
    """

    # PATCH 66 — Largeur du panneau "Fichiers" (QDockWidget).
    _EXPLORER_PANEL_WIDTH = 260

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(f"Méthodo OG {__version__}")
        self.resize(1000, 700)

        # PATCH 65 — voir plus bas ; initialisé avant _run_welcome_dialog
        # car celle-ci peut le renseigner (nouveau projet).
        self._explorer_startup_folder: Path | None = None

        # PATCH 63 — écran d'accueil (façon VS Code / JetBrains) : demande
        # de créer ou d'ouvrir un projet avant d'afficher la fenêtre
        # principale, avec un raccourci vers les projets récents.
        self._document, restored_path = self._run_welcome_dialog()
        self._active_text_widget: TextBlockWidget | None = None
        # PATCH 67 — Dernier bloc "actif" (cliqué ou édité), quel que soit
        # son type ; sert à insérer un nouveau bloc juste après lui.
        self._active_block_id: str | None = None
        # PATCH 68 — Ensemble des id de titres/sous-titres actuellement
        # réduits (flèche ▸), voir _toggle_heading_collapse.
        self._collapsed_headings: set[str] = set()
        self._current_file: Path | None = None
        # PATCH 82 — métadonnées système du projet courant (nom "métier",
        # indépendant du nom de fichier .json — voir core.project_meta).
        self._current_project_meta: ProjectMeta | None = None
        # PATCH 65 — Dossier projet imposé pour cette session (choisi à
        # l'écran d'accueil ou déduit du fichier ouvert), qui devient la
        # racine verrouillée de l'explorateur de fichiers.
        if self._explorer_startup_folder is None and restored_path is not None:
            self._explorer_startup_folder = restored_path.parent

        self._setup_ui()
        if restored_path is not None:
            self._set_current_file(restored_path)
        # PATCH 52 — référence servant à détecter des modifications non
        # sauvegardées à la fermeture (voir closeEvent).
        self._last_saved_snapshot = self._document_snapshot()

    def _run_welcome_dialog(self) -> tuple[Document, Path | None]:
        """PATCH 63 — Affiche l'écran d'accueil et traduit le choix de
        l'utilisateur en document initial + chemin associé."""
        app = QApplication.instance()
        if app is not None and app.platformName() == "offscreen":
            # Plateforme "offscreen" (tests automatisés / CI) : personne
            # ne peut cliquer sur une popup modale, on saute donc
            # directement à la reprise de session habituelle (PATCH 52)
            # pour ne jamais bloquer l'exécution des tests.
            return _load_startup_document()

        dialog = WelcomeDialog(_get_recent_files(), self, on_remove_recent=_remove_recent_file)
        if dialog.exec() != QDialog.Accepted:
            # Fenêtre fermée sans choix (croix / Échap) : on ne bloque
            # jamais le lancement, on reprend l'ancien comportement
            # (reprise de la dernière session, PATCH 52).
            return _load_startup_document()

        if dialog.result_action == WelcomeDialog.ACTION_NEW_BLANK:
            self._explorer_startup_folder = dialog.result_folder
            document = Document()
            return document, self._create_initial_project_file(
                dialog.result_folder, document, dialog.result_project_name
            )

        if dialog.result_action == WelcomeDialog.ACTION_OPEN and dialog.result_path is not None:
            try:
                raw = json.loads(dialog.result_path.read_text(encoding="utf-8"))
                return Document.from_dict(raw), dialog.result_path
            except (OSError, ValueError, KeyError) as exc:
                QMessageBox.critical(
                    self, tr("error.open_title"), f"{tr('error.open_text')}\n{exc}"
                )
                return build_project_template(), None

        # ACTION_NEW_TEMPLATE, ou repli par défaut.
        self._explorer_startup_folder = dialog.result_folder
        document = build_project_template()
        return document, self._create_template_project_files(
            dialog.result_folder, document, dialog.result_project_name
        )

    def _create_initial_project_file(
        self, folder: Path | None, document: Document, project_name: str | None = None
    ) -> Path | None:
        """PATCH 66 — Écrit tout de suite le document initial dans le
        dossier projet fraîchement créé, afin qu'il apparaisse
        immédiatement dans l'explorateur et les projets récents, comme
        le ferait un IDE à la création d'un projet.

        PATCH 82 — Le nom "métier" du projet (`project_name`, tel que
        saisi à l'écran d'accueil) n'est plus déduit du nom du fichier
        .json : il est écrit dans le fichier système séparé
        ".methodo-project.json" (voir core.project_meta), pour rester
        indépendant si le fichier ou le dossier est renommé ensuite.
        """
        if folder is None:
            return None
        path = folder / f"{folder.name}.json"
        try:
            path.write_text(
                json.dumps(document.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            QMessageBox.critical(
                self, tr("error.generic_title"), f"{tr('error.create_project_file')}\n{exc}"
            )
            return None
        ProjectMeta.create(project_name or folder.name).save(path)
        return path

    def _create_template_project_files(
        self, folder: Path | None, document: Document, project_name: str | None = None
    ) -> Path | None:
        """PATCH 85 — "Nouveau projet (Modèle OG)" ne doit pas se
        limiter à un unique fichier gabarit posé à la racine : un
        projet démarre toujours avec (au moins) deux dossiers clients.
        Le gabarit "Modèle OG" est initialisé dans "client 1" ; "client
        2" est créé vide, prêt à accueillir un second dossier client.
        """
        if folder is None:
            return None
        client1_dir = folder / "client 1"
        client2_dir = folder / "client 2"
        try:
            client1_dir.mkdir(parents=True)
            client2_dir.mkdir(parents=True)
        except OSError as exc:
            QMessageBox.critical(
                self, tr("error.generic_title"), f"{tr('error.create_project_file')}\n{exc}"
            )
            return None
        path = client1_dir / f"{client1_dir.name}.json"
        try:
            path.write_text(
                json.dumps(document.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            QMessageBox.critical(
                self, tr("error.generic_title"), f"{tr('error.create_project_file')}\n{exc}"
            )
            return None
        ProjectMeta.create(project_name or folder.name).save(path)
        return path

    def _setup_ui(self) -> None:
        """Prépare la toolbar, la zone de contenu et affiche le document."""
        toolbar = MainToolBar(
            actions={
                "new_block": lambda: self._add_text_block(),
                "new_checklist": self._add_checklist_block,
                "new_image": self._add_image_block,
                "new_table": self._add_table_block,
                "new_simple_table": self._add_simple_table_block,
                "new_gantt": self._add_gantt_block,
                "new_separator": self._add_separator_block,
                "new_quote": self._add_quote_block,
                "new_code": self._add_code_block,
                "new_list": self._add_list_block,
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
                "insert_link": self._insert_internal_link,
                "insert_emoji": self._show_emoji_picker,
            },
            on_size_changed=self._apply_size,
            on_info=self._show_info_dialog,
            info_icon_path=_INFO_ICON_PATH,
        )
        self._toolbar = toolbar
        self.addToolBar(toolbar)
        self._setup_file_explorer_dock()
        self._setup_file_menu()

        central = BlocksArea(
            on_block_dropped=self._on_block_dropped,
            on_empty_context_menu=self._show_empty_context_menu,
        )
        self._blocks_layout = central.blocks_layout
        # PATCH 66 — La fenêtre est lancée en showMaximized() (main.py) :
        # resize() n'a donc AUCUN effet visible une fois maximisée (une
        # fenêtre maximisée ignore les appels resize()). La largeur totale
        # est donc toujours celle de l'écran, panneau "Fichiers" ouvert ou
        # non ; il ne faut PAS essayer d'agrandir la fenêtre. Il faut plutôt
        # empêcher la zone de blocs de réclamer plus de largeur que ce que
        # le dock lui laisse : Ignored sur l'axe horizontal indique à la
        # QScrollArea de ne jamais tenir compte de la largeur minimale
        # réclamée par les blocs (tableaux, Gantt...) pour dimensionner le
        # widget, qui est alors toujours exactement casé dans la largeur
        # visible (viewport) → plus jamais de scrollbar horizontale, quel
        # que soit l'état du panneau.
        central.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        # PATCH 28 : zone de défilement, nécessaire pour pouvoir amener
        # un résultat de recherche à l'écran (`_scroll_to_block`).
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(central)
        self.setCentralWidget(self._scroll_area)

        # PATCH 48 — le document initial vient désormais du template
        # "Modèle OG" (Opportunity Governance, voir __init__), plus besoin de contenu de démo ici.
        self._render_document(focus_last=True)

        # -- Undo/Redo (PATCH 27) ------------------------------------
        self._undo_history = UndoHistory(self._document_snapshot())
        self._undo_timer = QTimer(self)
        self._undo_timer.setInterval(_UNDO_POLL_INTERVAL_MS)
        self._undo_timer.timeout.connect(self._poll_undo_snapshot)
        self._undo_timer.start()
        # Intercepte Ctrl+Z/Ctrl+Y avant que QTextEdit/QLineEdit ne les
        # traitent eux-mêmes (undo natif local, non désiré ici).
        QApplication.instance().installEventFilter(self)

    def _setup_file_menu(self) -> None:
        """Menu Fichier : Nouveau / Ouvrir / Sauvegarder / Sauvegarder sous (PATCH 8).

        PATCH 79 — chaque libellé de la barre de menu passe par `tr()`
        (voir ui.i18n) ; les objets QMenu/QAction concernés sont gardés
        en attribut pour être retraduits par `_retranslate_menu()` si
        la langue change en cours de session (voir le sous-menu
        "Langue" ajouté au menu Affichage).
        """
        self._file_menu = self.menuBar().addMenu(tr("menu.file"))

        self._templates_menu = self._file_menu.addMenu(tr("menu.file.templates"))
        self._og_template_action = QAction(tr("menu.file.template_og"), self)
        self._og_template_action.setShortcut(QKeySequence.New)
        self._og_template_action.triggered.connect(self._new_document)
        self._templates_menu.addAction(self._og_template_action)

        self._new_blank_action = QAction(tr("menu.file.new_blank"), self)
        self._new_blank_action.triggered.connect(self._new_blank_document)
        self._file_menu.addAction(self._new_blank_action)

        self._open_action = QAction(tr("menu.file.open"), self)
        self._open_action.setShortcut(QKeySequence.Open)
        self._open_action.triggered.connect(self._open_document)
        self._file_menu.addAction(self._open_action)

        self._save_action = QAction(tr("menu.file.save"), self)
        self._save_action.setShortcut(QKeySequence.Save)
        self._save_action.triggered.connect(self._save_document)
        self._file_menu.addAction(self._save_action)

        self._save_as_action = QAction(tr("menu.file.save_as"), self)
        self._save_as_action.setShortcut(QKeySequence.SaveAs)
        self._save_as_action.triggered.connect(self._save_document_as)
        self._file_menu.addAction(self._save_as_action)

        self._export_pdf_action = QAction(tr("menu.file.export_pdf"), self)
        self._export_pdf_action.triggered.connect(self._export_pdf)
        self._file_menu.addAction(self._export_pdf_action)

        self._file_menu.addSeparator()
        self._rename_project_action = QAction(tr("menu.file.rename_project"), self)
        self._rename_project_action.triggered.connect(self._rename_project)
        self._file_menu.addAction(self._rename_project_action)

        self._edit_menu = self.menuBar().addMenu(tr("menu.edit"))

        self._undo_action = QAction(tr("menu.edit.undo"), self)
        self._undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self._undo_action.triggered.connect(self._undo)
        self._edit_menu.addAction(self._undo_action)

        self._redo_action = QAction(tr("menu.edit.redo"), self)
        self._redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        self._redo_action.triggered.connect(self._redo)
        self._edit_menu.addAction(self._redo_action)

        self._edit_menu.addSeparator()
        self._search_action = QAction(tr("menu.edit.search"), self)
        self._search_action.setShortcut(QKeySequence("Ctrl+F"))
        self._search_action.triggered.connect(self._show_search_dialog)
        self._edit_menu.addAction(self._search_action)

        self._replace_action = QAction(tr("menu.edit.replace"), self)
        self._replace_action.setShortcut(QKeySequence("Ctrl+H"))
        self._replace_action.triggered.connect(self._show_search_dialog)
        self._edit_menu.addAction(self._replace_action)

        self._edit_menu.addSeparator()
        self._people_manager_action = QAction(tr("menu.edit.people_manager"), self)
        self._people_manager_action.triggered.connect(self._show_people_manager_dialog)
        self._edit_menu.addAction(self._people_manager_action)

        self._view_menu = self.menuBar().addMenu(tr("menu.view"))
        self._dark_mode_action = QAction(tr("menu.view.dark_mode"), self)
        self._dark_mode_action.setCheckable(True)
        self._dark_mode_action.setChecked(current_theme(QApplication.instance()) == THEME_DARK)
        self._dark_mode_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self._dark_mode_action.triggered.connect(self._toggle_dark_mode)
        self._view_menu.addAction(self._dark_mode_action)

        self._theme_menu = self._view_menu.addMenu(tr("menu.view.theme"))
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        self._theme_actions: dict[str, QAction] = {}
        for theme_name in THEMES:
            action = QAction(THEME_LABELS[theme_name], self)
            action.setCheckable(True)
            action.setChecked(current_theme(QApplication.instance()) == theme_name)
            action.triggered.connect(lambda _, t=theme_name: self._set_theme(t))
            theme_group.addAction(action)
            self._theme_menu.addAction(action)
            self._theme_actions[theme_name] = action

        # PATCH 79 — sous-menu "Langue" : pour l'instant Français (défaut
        # historique de l'app) et English seulement (voir ui.i18n).
        self._language_menu = self._view_menu.addMenu(tr("menu.view.language"))
        language_group = QActionGroup(self)
        language_group.setExclusive(True)
        self._language_actions: dict[str, QAction] = {}
        for language_code, language_label in LANGUAGES.items():
            action = QAction(language_label, self)
            action.setCheckable(True)
            action.setChecked(get_language() == language_code)
            action.triggered.connect(lambda _, lang=language_code: self._set_language(lang))
            language_group.addAction(action)
            self._language_menu.addAction(action)
            self._language_actions[language_code] = action

        self._view_menu.addSeparator()
        self._block_spacing_action = QAction(tr("menu.view.block_spacing"), self)
        self._block_spacing_action.setCheckable(True)
        self._block_spacing_action.setChecked(get_block_spacing())
        self._block_spacing_action.triggered.connect(self._toggle_block_spacing)
        self._view_menu.addAction(self._block_spacing_action)

        self._autosave_action = QAction(tr("menu.view.autosave"), self)
        self._autosave_action.setCheckable(True)
        self._autosave_action.setChecked(get_autosave_enabled())
        self._autosave_action.triggered.connect(self._toggle_autosave)
        self._view_menu.addAction(self._autosave_action)

        self._view_menu.addSeparator()
        self._explorer_action = QAction(tr("menu.view.explorer"), self)
        self._explorer_action.setCheckable(True)
        self._explorer_action.setChecked(True)
        self._explorer_action.triggered.connect(self._toggle_explorer_dock)
        self._view_menu.addAction(self._explorer_action)
        # PATCH 67 — Le dock a aussi sa propre croix de fermeture (titlebar),
        # qui ne passe pas par _toggle_explorer_dock : on resynchronise la
        # case cochée du menu sur l'état réel de visibilité du dock, quelle
        # que soit la façon dont il a été fermé/rouvert.
        self._explorer_dock.visibilityChanged.connect(self._explorer_action.setChecked)

    def _set_language(self, language: str) -> None:
        """PATCH 79 — change la langue de l'interface et retraduit
        immédiatement la barre de menu (voir `_retranslate_menu`)."""
        set_language(language)
        for language_code, action in self._language_actions.items():
            action.setChecked(language_code == language)
        self._retranslate_menu()

    def _retranslate_menu(self) -> None:
        """PATCH 79 — réapplique `tr()` à tous les libellés de la barre
        de menu (voir `_setup_file_menu`) après un changement de
        langue. Le reste de l'interface (barre d'outils, blocs,
        dialogues) n'est pas encore traduit."""
        self._file_menu.setTitle(tr("menu.file"))
        self._templates_menu.setTitle(tr("menu.file.templates"))
        self._og_template_action.setText(tr("menu.file.template_og"))
        self._new_blank_action.setText(tr("menu.file.new_blank"))
        self._open_action.setText(tr("menu.file.open"))
        self._save_action.setText(tr("menu.file.save"))
        self._save_as_action.setText(tr("menu.file.save_as"))
        self._export_pdf_action.setText(tr("menu.file.export_pdf"))
        self._rename_project_action.setText(tr("menu.file.rename_project"))

        self._edit_menu.setTitle(tr("menu.edit"))
        self._undo_action.setText(tr("menu.edit.undo"))
        self._redo_action.setText(tr("menu.edit.redo"))
        self._search_action.setText(tr("menu.edit.search"))
        self._replace_action.setText(tr("menu.edit.replace"))
        self._people_manager_action.setText(tr("menu.edit.people_manager"))

        self._view_menu.setTitle(tr("menu.view"))
        self._dark_mode_action.setText(tr("menu.view.dark_mode"))
        self._theme_menu.setTitle(tr("menu.view.theme"))
        self._language_menu.setTitle(tr("menu.view.language"))
        self._block_spacing_action.setText(tr("menu.view.block_spacing"))
        self._autosave_action.setText(tr("menu.view.autosave"))
        self._explorer_action.setText(tr("menu.view.explorer"))
        self._toolbar.retranslate()

    def _toggle_explorer_dock(self, visible: bool) -> None:
        """PATCH 66 — Affiche/masque le panneau "Fichiers". La zone de
        blocs (policy Ignored, voir _setup_ui) s'adapte toute seule à la
        largeur restante : pas besoin de toucher à la taille de la
        fenêtre (et un resize() serait de toute façon sans effet, la
        fenêtre étant lancée maximisée — voir main.py)."""
        self._explorer_dock.setVisible(visible)

    def _setup_file_explorer_dock(self) -> None:
        """PATCH 53 — Panneau latéral façon IDE : arborescence d'un
        dossier choisi par l'utilisateur, double-clic sur un ".json"
        pour l'ouvrir comme document Méthodo OG.

        PATCH 81 — rapproché des explorateurs de fichiers des IDE
        courants (VS Code, PyCharm...) : toute l'arborescence est
        visible (plus seulement les ".json"), et un clic droit permet
        de créer un fichier/dossier, renommer (aussi via F2) ou
        supprimer (aussi via la touche Suppr), avec renommage immédiat
        à la création comme le font ces IDE.
        """
        self._explorer_dock = QDockWidget(tr("explorer.title"), self)
        self._explorer_dock.setObjectName("file_explorer_dock")

        container = QWidget(self._explorer_dock)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QHBoxLayout()
        self._explorer_path_label = QLineEdit()
        self._explorer_path_label.setReadOnly(True)
        self._explorer_path_label.setPlaceholderText(tr("explorer.no_folder"))
        header.addWidget(self._explorer_path_label)
        choose_folder_button = QPushButton(tr("explorer.choose_folder"))
        choose_folder_button.clicked.connect(self._choose_explorer_folder)
        header.addWidget(choose_folder_button)
        layout.addLayout(header)

        self._explorer_model = QFileSystemModel(self)
        # PATCH 81 — toute l'arborescence est affichée (plus de filtre
        # sur les ".json") : un vrai panneau de projet, pas une liste
        # de documents. Seul l'ouverture au double-clic reste limitée
        # aux ".json" (_on_explorer_item_activated).

        self._explorer_tree = QTreeView(container)
        self._explorer_tree.setModel(self._explorer_model)
        self._explorer_tree.setHeaderHidden(True)
        # PATCH 85 — Sélection multiple façon IDE : Shift étend la
        # sélection à tous les éléments consécutifs entre l'ancre et le
        # clic, Ctrl ajoute/retire un élément un par un (comportement
        # natif de Qt en ExtendedSelection, SingleSelection par défaut
        # ne le permettait pas).
        self._explorer_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for column in (1, 2, 3):
            self._explorer_tree.hideColumn(column)
        self._explorer_tree.doubleClicked.connect(self._on_explorer_item_activated)
        # PATCH 81 — F2/menu déclenchent l'édition manuellement (voir
        # _explorer_rename) : pas d'édition sur simple/double-clic, qui
        # servent déjà à sélectionner/ouvrir.
        self._explorer_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._explorer_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._explorer_tree.customContextMenuRequested.connect(self._show_explorer_context_menu)
        # PATCH 81 — F2 (renommer) et Suppr (supprimer), comme les IDE.
        rename_shortcut = QAction(self._explorer_tree)
        rename_shortcut.setShortcut(QKeySequence(Qt.Key_F2))
        rename_shortcut.setShortcutContext(Qt.WidgetShortcut)
        rename_shortcut.triggered.connect(lambda: self._explorer_rename(self._explorer_tree.currentIndex()))
        self._explorer_tree.addAction(rename_shortcut)
        delete_shortcut = QAction(self._explorer_tree)
        delete_shortcut.setShortcut(QKeySequence(Qt.Key_Delete))
        delete_shortcut.setShortcutContext(Qt.WidgetShortcut)
        delete_shortcut.triggered.connect(lambda: self._explorer_delete(self._explorer_tree.currentIndex()))
        self._explorer_tree.addAction(delete_shortcut)
        layout.addWidget(self._explorer_tree)

        self._explorer_dock.setWidget(container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._explorer_dock)
        # PATCH 66 — Largeur confortable et stable pour le panneau.
        self.resizeDocks([self._explorer_dock], [self._EXPLORER_PANEL_WIDTH], Qt.Horizontal)

        settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        if self._explorer_startup_folder is not None:
            # PATCH 65 — Dossier du projet choisi à l'écran d'accueil (ou
            # déduit du fichier ouvert) : prioritaire, il devient la
            # racine verrouillée de l'explorateur pour cette session.
            self._set_explorer_root(self._explorer_startup_folder)
            return

        last_folder = settings.value(_SETTINGS_LAST_FOLDER_KEY, "")
        if last_folder and Path(last_folder).is_dir():
            self._set_explorer_root(Path(last_folder))
        else:
            # PATCH 54 — Sans dossier mémorisé, on n'affiche jamais tout
            # le poste : on se replie sur le dossier utilisateur, comme
            # le ferait un IDE tant qu'aucun projet n'est ouvert.
            self._set_explorer_root(Path.home())

    def _choose_explorer_folder(self) -> None:
        """PATCH 53 — Sélectionne le dossier affiché dans l'explorateur."""
        folder = QFileDialog.getExistingDirectory(self, tr("explorer.choose_folder_dialog"))
        if not folder:
            return
        self._set_explorer_root(Path(folder))

    def _set_explorer_root(self, folder: Path) -> None:
        self._explorer_model.setRootPath(str(folder))
        self._explorer_tree.setRootIndex(self._explorer_model.index(str(folder)))
        self._explorer_path_label.setText(str(folder))
        settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        settings.setValue(_SETTINGS_LAST_FOLDER_KEY, str(folder))

    def _on_explorer_item_activated(self, index) -> None:
        """PATCH 53 — Double-clic dans l'explorateur : ouvre le fichier
        ".json" sélectionné comme document courant."""
        path = Path(self._explorer_model.filePath(index))
        if path.is_dir() or path.suffix != ".json":
            return
        self._load_document_from_path(path)

    # -- Explorateur : créer / renommer / supprimer (PATCH 81) -----------

    def _explorer_target_dir(self, index: QModelIndex) -> Path:
        """Dossier dans lequel agir : celui de l'élément cliqué s'il
        s'agit d'un dossier, son parent s'il s'agit d'un fichier, sinon
        (clic dans le vide) la racine actuelle de l'explorateur."""
        if not index.isValid():
            return Path(self._explorer_model.rootPath())
        path = Path(self._explorer_model.filePath(index))
        return path if path.is_dir() else path.parent

    def _show_explorer_context_menu(self, pos: QPoint) -> None:
        index = self._explorer_tree.indexAt(pos)

        menu = QMenu(self._explorer_tree)
        new_file_action = menu.addAction(tr("explorer.new_file"))
        new_folder_action = menu.addAction(tr("explorer.new_folder"))
        rename_action = None
        delete_action = None
        if index.isValid():
            menu.addSeparator()
            rename_action = menu.addAction(tr("explorer.rename"))
            delete_action = menu.addAction(tr("explorer.delete"))

        action = menu.exec(self._explorer_tree.viewport().mapToGlobal(pos))
        if action is None:
            return
        if action is new_file_action:
            self._explorer_create(index, is_folder=False)
        elif action is new_folder_action:
            self._explorer_create(index, is_folder=True)
        elif action is rename_action:
            self._explorer_rename(index)
        elif action is delete_action:
            self._explorer_delete(index)

    def _explorer_create(self, index: QModelIndex, is_folder: bool) -> None:
        """PATCH 81 — Crée un fichier ou dossier, façon IDE : nom par
        défaut unique, puis renommage immédiat proposé à l'utilisateur."""
        target_dir = self._explorer_target_dir(index)
        base_name = tr("explorer.new_folder_name") if is_folder else tr("explorer.new_file_name")
        candidate = target_dir / base_name if is_folder else target_dir / f"{base_name}.json"
        counter = 1
        while candidate.exists():
            if is_folder:
                candidate = target_dir / f"{base_name} ({counter})"
            else:
                candidate = target_dir / f"{base_name} ({counter}).json"
            counter += 1

        try:
            if is_folder:
                candidate.mkdir(parents=True)
            else:
                candidate.write_text(
                    json.dumps(Document().to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except OSError as exc:
            QMessageBox.critical(
                self, tr("explorer.create_error_title"), f"{tr('explorer.create_error_text')}\n{exc}"
            )
            return

        self._explorer_edit_when_ready(candidate)

    def _explorer_rename(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        self._explorer_tree.setCurrentIndex(index)
        self._explorer_tree.edit(index)

    def _explorer_edit_when_ready(self, path: Path) -> None:
        """PATCH 81 — QFileSystemModel indexe le système de fichiers de
        façon asynchrone : on retente jusqu'à ce que le nouvel élément
        soit visible, puis on le sélectionne et on lance son édition
        (nom pré-sélectionné) pour qu'il puisse être renommé aussitôt."""
        index = self._explorer_model.index(str(path))
        if not index.isValid():
            QTimer.singleShot(50, lambda: self._explorer_edit_when_ready(path))
            return
        self._explorer_tree.setCurrentIndex(index)
        self._explorer_tree.scrollTo(index)
        self._explorer_tree.edit(index)

    def _explorer_delete(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        path = Path(self._explorer_model.filePath(index))
        confirm = QMessageBox.question(
            self,
            tr("explorer.delete_title"),
            tr("explorer.delete_confirm").format(name=path.name),
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            QMessageBox.critical(
                self, tr("explorer.delete_error_title"), f"{tr('explorer.delete_error_text')}\n{exc}"
            )

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
        self._active_block_id = widget.block.id

    def _on_block_activated(self, block_id: str) -> None:
        """PATCH 67 — Un bloc (de n'importe quel type) vient d'être
        cliqué : il devient le point d'insertion pour le prochain bloc
        créé via la toolbar ou le menu contextuel."""
        self._active_block_id = block_id

    def _apply_color(self) -> None:
        if self._active_text_widget is None:
            return
        color = QColorDialog.getColor(QColor("black"), self, "Choisir une couleur")
        if color.isValid():
            self._active_text_widget.set_text_color(color)

    def _insert_internal_link(self) -> None:
        """PATCH 30 — Insère, dans le bloc texte actif, un lien vers un
        autre bloc du document (Ctrl+Clic dessus pour y naviguer)."""
        if self._active_text_widget is None:
            return
        source_block_id = self._active_text_widget.block.id
        picker = BlockPickerDialog(self._document, exclude_block_id=source_block_id, parent=self)
        picker.exec()
        if picker.selected_block_id is None:
            return

        target = next(
            (b for b in self._document.blocks if b.id == picker.selected_block_id), None
        )
        if target is None:
            return
        label = preview_for_block(target)
        self._active_text_widget.insert_internal_link(picker.selected_block_id, label)

    def _show_emoji_picker(self) -> None:
        """PATCH 35 — Ouvre le sélecteur d'emoji, insère au curseur du
        bloc texte actif."""
        if self._active_text_widget is None:
            return
        widget = self._active_text_widget
        picker = EmojiPicker(self)
        picker.emoji_selected.connect(widget.insert_emoji)
        cursor_rect = widget.cursorRect()
        anchor = widget.mapToGlobal(cursor_rect.bottomLeft())
        picker.move(anchor)
        picker.show()

    def _apply_size(self, size: int) -> None:
        if self._active_text_widget is not None:
            self._active_text_widget.set_font_size(size)

    def _show_info_dialog(self) -> None:
        """Ouvre la popup listant les explications et choix de design."""
        InfoDialog(self).exec()

    # -- Recherche globale (PATCH 28) --------------------------------------

    def _show_search_dialog(self) -> None:
        """CTRL+F/CTRL+H — Recherche (et remplacement, PATCH 29) globaux."""
        SearchDialog(
            self._document,
            on_result_activated=self._scroll_to_block,
            on_document_changed=self._render_document,
            parent=self,
        ).exec()

    def _scroll_to_block(self, block_id: str) -> None:
        """Fait défiler jusqu'au bloc et le met en surbrillance brièvement."""
        for i in range(self._blocks_layout.count()):
            item = self._blocks_layout.itemAt(i)
            widget = item.widget() if item else None
            if isinstance(widget, BlockContainer) and widget.block_id == block_id:
                self._scroll_area.ensureWidgetVisible(widget)
                widget.content.setFocus()
                return

    # -- Mode sombre (PATCH 32) ---------------------------------------------

    def _toggle_dark_mode(self) -> None:
        new_theme = toggle_theme(QApplication.instance())
        self._dark_mode_action.setChecked(new_theme == THEME_DARK)
        self._sync_theme_menu(new_theme)

    def _toggle_block_spacing(self) -> None:
        """PATCH 51 — bascule l'espacement supplémentaire au-dessus des
        titres/sous-titres, tableaux et graphiques, et redessine le
        document pour l'appliquer."""
        set_block_spacing(self._block_spacing_action.isChecked())
        self._render_document()

    def _toggle_autosave(self) -> None:
        set_autosave_enabled(self._autosave_action.isChecked())

    def _set_theme(self, theme_name: str) -> None:
        """PATCH 33 — Applique un thème choisi dans le sous-menu "Thème"."""
        apply_theme(QApplication.instance(), theme_name)
        self._dark_mode_action.setChecked(theme_name == THEME_DARK)
        self._sync_theme_menu(theme_name)

    def _sync_theme_menu(self, theme_name: str) -> None:
        action = self._theme_actions.get(theme_name)
        if action is not None:
            action.setChecked(True)

    # -- Undo / Redo (PATCH 27) --------------------------------------------

    def _document_snapshot(self) -> str:
        """Sérialise l'état courant du document (indépendant, réutilise
        le format de sauvegarde JSON du PATCH 8/9)."""
        return json.dumps(self._document.to_dict(), sort_keys=True)

    def _poll_undo_snapshot(self) -> None:
        """Sondage périodique : regroupe les frappes rapides d'une même
        pause en un seul point d'annulation."""
        if self._undo_history.check(self._document_snapshot()):
            self._maybe_autosave()

    def _maybe_autosave(self) -> None:
        """PATCH 51 — Sauvegarde automatique : dès qu'un document a été
        sauvegardé une première fois (self._current_file défini), toute
        modification ultérieure détectée par le sondage undo (donc déjà
        "posée" un court instant, pas frappe par frappe) réécrit
        silencieusement le même fichier, si l'option est activée
        (activée par défaut, réglable dans le menu Affichage)."""
        if not get_autosave_enabled() or self._current_file is None:
            return
        self._write_document(self._current_file)

    def _restore_snapshot(self, raw_snapshot: str) -> None:
        self._document = Document.from_dict(json.loads(raw_snapshot))
        self._render_document()

    def _undo(self) -> None:
        """CTRL+Z — Annule la dernière action (toute action est
        annulable : ajout, suppression, déplacement, conversion,
        édition de texte, de checklist, de tableau, ...)."""
        snapshot = self._undo_history.undo(self._document_snapshot())
        if snapshot is not None:
            self._restore_snapshot(snapshot)

    def _redo(self) -> None:
        """CTRL+Y — Rétablit la dernière action annulée."""
        snapshot = self._undo_history.redo()
        if snapshot is not None:
            self._restore_snapshot(snapshot)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        """Intercepte Ctrl+Z/Ctrl+Y avant les widgets d'édition natifs
        (QTextEdit/QLineEdit ont sinon leur propre undo local)."""
        if event.type() == QEvent.KeyPress and event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self._undo()
                return True
            if event.key() == Qt.Key_Y:
                self._redo()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event) -> None:  # noqa: N802
        """PATCH 52 — À la fermeture, propose de sauvegarder si des
        modifications n'ont pas été enregistrées depuis la dernière
        sauvegarde/ouverture (comparaison de snapshots, même mécanisme
        que l'undo). Annuler la boîte de dialogue annule la fermeture."""
        if self._document_snapshot() == self._last_saved_snapshot:
            event.accept()
            return

        response = QMessageBox.question(
            self,
            tr("unsaved.title"),
            tr("unsaved.text"),
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if response == QMessageBox.Cancel:
            event.ignore()
            return
        if response == QMessageBox.Save:
            self._save_document()
            # "Sauvegarder sous" peut avoir été annulé par l'utilisateur :
            # dans ce cas rien n'a été écrit, on n'autorise pas la fermeture.
            if self._document_snapshot() != self._last_saved_snapshot:
                event.ignore()
                return
        event.accept()

    # -- Rendu générique des blocs / drag & drop (PATCH 8, 13) ------------

    def _create_content_widget_for_block(self, block) -> QWidget:
        """Crée le widget métier adapté au type d'un bloc (sans poignée)."""
        if isinstance(block, TextBlock):
            return self._create_text_widget(block)
        if isinstance(block, HeadingBlock):
            return HeadingBlockWidget(block)
        if isinstance(block, ChecklistBlock):
            return ChecklistBlockWidget(block)
        if isinstance(block, LinkedChecklistBlock):
            return LinkedChecklistBlockWidget(block)
        if isinstance(block, PeopleListBlock):
            return PeopleListBlockWidget(block, self._document)
        if isinstance(block, TableBlock):
            return TableBlockWidget(block, self._document)
        if isinstance(block, SimpleTableBlock):
            return SimpleTableBlockWidget(block)
        if isinstance(block, GanttBlock):
            return GanttBlockWidget(block, self._document)
        if isinstance(block, DependencyGanttBlock):
            return DependencyGanttBlockWidget(block, self._document)
        if isinstance(block, LineChartBlock):
            return LineChartBlockWidget(block, self._document)
        if isinstance(block, BarChartBlock):
            return BarChartBlockWidget(block, self._document)
        if isinstance(block, FormulaBlock):
            return FormulaBlockWidget(block, self._document)
        if isinstance(block, SeparatorBlock):
            return SeparatorBlockWidget(block)
        if isinstance(block, QuoteBlock):
            return QuoteBlockWidget(block)
        if isinstance(block, CodeBlock):
            return CodeBlockWidget(block)
        if isinstance(block, ListBlock):
            return ListBlockWidget(block)
        if isinstance(block, ImageBlock):
            return ImageBlockWidget(
                block,
                on_move_up=lambda block_id=block.id: self._move_block(block_id, -1),
                on_move_down=lambda block_id=block.id: self._move_block(block_id, 1),
                on_delete=lambda block_id=block.id: self._delete_block(block_id),
            )
        raise ValueError(f"Type de bloc non pris en charge à l'affichage : {block.type}")

    # PATCH 51 — types de blocs devant "respirer" (marge au-dessus) quand
    # l'option d'espacement est activée : titres, tableaux et graphiques.
    _SPACED_BLOCK_TYPES = (
        HeadingBlock,
        TableBlock,
        SimpleTableBlock,
        GanttBlock,
        DependencyGanttBlock,
        LineChartBlock,
        BarChartBlock,
    )
    _EXTRA_TOP_MARGIN_PX = 22

    def _wrap(self, content: QWidget, block_id: str) -> BlockContainer:
        """PATCH 13 — Ajoute la poignée de glisser-déposer à un widget de
        bloc, PATCH 34 — ainsi que son icône de type, PATCH 51 — et
        l'espacement optionnel au-dessus des titres/tableaux/graphiques."""
        block = self._document.find_block(block_id)
        extra_top_margin = 0
        if get_block_spacing() and isinstance(block, self._SPACED_BLOCK_TYPES):
            extra_top_margin = self._EXTRA_TOP_MARGIN_PX
        # PATCH 68 — Titres/sous-titres : flèche de repli/dépli.
        on_toggle_collapse = None
        collapsed = False
        if isinstance(block, HeadingBlock):
            on_toggle_collapse = self._toggle_heading_collapse
            collapsed = block.id in self._collapsed_headings
        return BlockContainer(
            content,
            block_id,
            on_context_menu_requested=self._show_block_context_menu,
            on_activated=self._on_block_activated,
            icon=icon_for_block(block) if block is not None else "",
            extra_top_margin=extra_top_margin,
            on_toggle_collapse=on_toggle_collapse,
            collapsed=collapsed,
        )

    def _toggle_heading_collapse(self, block_id: str) -> None:
        """PATCH 69 — Réduit/développe (façon plan Word) tous les blocs
        situés après ce titre/sous-titre, jusqu'au prochain titre de
        même niveau ou plus prioritaire (ex. Titre 1 s'arrête au
        prochain Titre 1, en cachant au passage les Titre 2/3 imbriqués)."""
        if block_id in self._collapsed_headings:
            self._collapsed_headings.discard(block_id)
        else:
            self._collapsed_headings.add(block_id)
        layout_index = self._layout_index_of_block(block_id)
        if layout_index != -1:
            item = self._blocks_layout.itemAt(layout_index)
            container = item.widget() if item else None
            if isinstance(container, BlockContainer):
                container.set_collapsed(block_id in self._collapsed_headings)
        self._apply_collapse_state()

    def _apply_collapse_state(self) -> None:
        """PATCH 69 — Applique l'état de repli courant, façon plan Word :
        réduire un titre de niveau N cache tout ce qui suit (y compris
        les sous-titres de niveau > N) jusqu'au prochain titre de niveau
        <= N (même priorité ou supérieure), pas juste "le prochain
        titre". `hide_levels` est une pile croissante des niveaux des
        titres réduits pas encore "refermés" par un titre de priorité
        égale ou supérieure ; le contenu est caché tant qu'elle n'est
        pas vide."""
        hide_levels: list[int] = []
        for i, block in enumerate(self._document.blocks):
            item = self._blocks_layout.itemAt(i)
            container = item.widget() if item else None
            if container is None:
                continue
            if isinstance(block, HeadingBlock):
                while hide_levels and block.level <= hide_levels[-1]:
                    hide_levels.pop()
                container.setVisible(not hide_levels)
                if block.id in self._collapsed_headings:
                    hide_levels.append(block.level)
                continue
            container.setVisible(not hide_levels)

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

    def _layout_index_of_block(self, block_id: str) -> int:
        """PATCH 67 — Position dans le layout du BlockContainer portant
        cet identifiant de bloc (-1 si introuvable)."""
        for i in range(self._blocks_layout.count()):
            item = self._blocks_layout.itemAt(i)
            widget = item.widget() if item else None
            if isinstance(widget, BlockContainer) and widget.block_id == block_id:
                return i
        return -1

    def _insertion_point(self) -> tuple[int, int]:
        """PATCH 67 — Où insérer un nouveau bloc créé depuis la toolbar,
        le menu "/" en zone vide ou le menu contextuel "zone vide" :
        juste après le bloc actif (dernier bloc cliqué/édité), quel que
        soit son type — ou en fin de document si aucun bloc n'est actif."""
        if self._active_block_id is not None:
            doc_index = next(
                (i for i, b in enumerate(self._document.blocks) if b.id == self._active_block_id),
                None,
            )
            layout_index = self._layout_index_of_block(self._active_block_id)
            if doc_index is not None and layout_index != -1:
                return doc_index + 1, layout_index + 1
        return len(self._document.blocks), self._blocks_layout.count()

    def _insert_new_block(self, block, widget: QWidget) -> None:
        """PATCH 67 — Insère un bloc + son widget au point d'insertion
        courant, et en fait le nouveau bloc actif (pour que des créations
        successives s'enchaînent dans l'ordre, plutôt que de toutes se
        replacer juste après l'ancien bloc actif)."""
        doc_index, layout_index = self._insertion_point()
        self._document.add_block(block, index=doc_index)
        self._blocks_layout.insertWidget(layout_index, self._wrap(widget, block.id))
        self._active_block_id = block.id

    def _render_document(self, focus_last: bool = False) -> None:
        """(Re)construit entièrement l'affichage à partir de self._document."""
        self._active_text_widget = None
        self._active_block_id = None
        while self._blocks_layout.count():
            item = self._blocks_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        last_content: QWidget | None = None
        for block in self._document.blocks:
            last_content = self._create_content_widget_for_block(block)
            self._blocks_layout.addWidget(self._wrap(last_content, block.id))

        self._apply_collapse_state()

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

    # -- Menu contextuel (PATCH 26) ----------------------------------------

    def _show_block_context_menu(self, block_id: str, global_pos: QPoint) -> None:
        """Clic droit complet sur un bloc : dupliquer, supprimer,
        déplacer, convertir."""
        index = next(
            (i for i, b in enumerate(self._document.blocks) if b.id == block_id), None
        )
        if index is None:
            return
        block = self._document.blocks[index]

        menu = QMenu(self)
        duplicate_action = menu.addAction(tr("context.duplicate"))
        delete_action = menu.addAction(tr("context.delete"))
        menu.addSeparator()

        favorite_label = tr("context.remove_favorite") if self._document.is_favorite(block_id) else tr("context.add_favorite")
        favorite_action = menu.addAction(favorite_label)
        menu.addSeparator()

        move_up_action = menu.addAction(tr("context.move_up"))
        move_up_action.setEnabled(index > 0)
        move_down_action = menu.addAction(tr("context.move_down"))
        move_down_action.setEnabled(index < len(self._document.blocks) - 1)

        convert_actions: dict[QAction, str] = {}
        if hasattr(block, "content"):
            # Conversion uniquement entre blocs à contenu texte simple.
            menu.addSeparator()
            convert_menu = menu.addMenu(tr("context.convert_to"))
            for target_id, label in _convert_targets():
                action = convert_menu.addAction(label)
                action.setEnabled(block.type != target_id)
                convert_actions[action] = target_id

        chosen = menu.exec(global_pos)
        if chosen is None:
            return
        if chosen is duplicate_action:
            self._duplicate_block(block_id)
        elif chosen is delete_action:
            self._delete_block(block_id)
        elif chosen is favorite_action:
            self._document.toggle_favorite(block_id)
        elif chosen is move_up_action:
            self._move_block(block_id, -1)
        elif chosen is move_down_action:
            self._move_block(block_id, 1)
        elif chosen in convert_actions:
            self._convert_block(block_id, convert_actions[chosen])

    def _show_empty_context_menu(self, global_pos: QPoint) -> None:
        """Clic droit sur une zone vide : propose d'ajouter un bloc en fin
        de document (mêmes cibles que le menu "/")."""
        menu = QMenu(self)
        actions: dict[QAction, str] = {}
        for command in get_commands():
            action = menu.addAction(command["label"])
            actions[action] = command["id"]

        chosen = menu.exec(global_pos)
        if chosen is None:
            return
        self._append_block_from_command(actions[chosen])

    def _duplicate_block(self, block_id: str) -> None:
        """PATCH 26 — Duplique un bloc et l'insère juste après l'original."""
        index = next(
            (i for i, b in enumerate(self._document.blocks) if b.id == block_id), None
        )
        if index is None:
            return
        raw = self._document.blocks[index].to_dict()
        raw["id"] = str(uuid.uuid4())
        duplicate = block_from_dict(raw)
        self._document.add_block(duplicate, index=index + 1)
        self._render_document()

    def _convert_block(self, block_id: str, target_id: str) -> None:
        """PATCH 26 — Remplace un bloc par un autre type, contenu conservé."""
        factory = self._block_factory(target_id)
        if factory is None:
            return
        index = next(
            (i for i, b in enumerate(self._document.blocks) if b.id == block_id), None
        )
        if index is None:
            return

        old_block = self._document.blocks[index]
        new_block = factory()
        if hasattr(new_block, "content"):
            new_block.content = getattr(old_block, "content", "")

        self._document.remove_block(block_id)
        self._document.add_block(new_block, index=index)
        self._render_document()

    def _append_block_from_command(self, command_id: str) -> None:
        """PATCH 26 — Ajoute en fin de document le bloc associé à `command_id`."""
        if command_id == "image":
            self._add_image_block()
            return

        factory = self._block_factory(command_id)
        if factory is None:
            return
        block = factory()
        self._document.add_block(block)
        widget = self._create_content_widget_for_block(block)
        self._blocks_layout.addWidget(self._wrap(widget, block.id))

    def _block_factory(self, command_id: str):
        """Fabrique de bloc partagée entre le menu "/" (PATCH 25) et le
        menu contextuel (PATCH 26)."""
        return {
            "text": lambda: TextBlock(),
            "heading1": lambda: HeadingBlock(level=1),
            "heading2": lambda: HeadingBlock(level=2),
            "heading3": lambda: HeadingBlock(level=3),
            "checklist": lambda: ChecklistBlock(),
            "linked_checklist": lambda: LinkedChecklistBlock(),
            "table": self._new_default_table_block,
            "simple_table": lambda: SimpleTableBlock(),
            "gantt": lambda: GanttBlock(),
            "dependency_gantt": lambda: DependencyGanttBlock(),
            "line_chart": lambda: LineChartBlock(),
            "bar_chart": lambda: BarChartBlock(),
            "formula": lambda: FormulaBlock(),
            "separator": lambda: SeparatorBlock(),
            "quote": lambda: QuoteBlock(),
            "code": lambda: CodeBlock(),
            "list": self._new_default_list_block,
        }.get(command_id)

    # -- Sauvegarde / chargement (PATCH 8) --------------------------------

    def _set_current_file(self, path: Path | None) -> None:
        self._current_file = path
        self._current_project_meta = ProjectMeta.load_or_create(path) if path is not None else None
        self._update_window_title()
        # PATCH 52 — mémorise (ou oublie) le fichier courant pour la
        # reprise de session au prochain lancement.
        settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        if path is not None:
            settings.setValue(_SETTINGS_LAST_FILE_KEY, str(path))
            # PATCH 63 — alimente la liste "Projets récents" de l'écran
            # d'accueil.
            _add_recent_file(path)
        else:
            settings.remove(_SETTINGS_LAST_FILE_KEY)

    def _update_window_title(self) -> None:
        """PATCH 82 — Le titre de fenêtre affiche le nom "métier" du
        projet (fichier système .methodo-project.json), plus jamais le
        nom du fichier .json de stockage."""
        title = f"Méthodo OG {__version__}"
        if self._current_project_meta is not None:
            title += f" — {self._current_project_meta.name}"
        self.setWindowTitle(title)

    def _rename_project(self) -> None:
        """PATCH 82 — Renomme le projet courant (nom "métier" seulement :
        le fichier .json et son emplacement ne bougent pas)."""
        if self._current_file is None or self._current_project_meta is None:
            QMessageBox.information(
                self, tr("project.rename_title"), tr("project.rename_no_project")
            )
            return
        name, ok = QInputDialog.getText(
            self,
            tr("project.rename_title"),
            tr("project.rename_label"),
            text=self._current_project_meta.name,
        )
        if ok and name.strip():
            self._current_project_meta.rename(self._current_file, name.strip())
            self._update_window_title()

    def _show_people_manager_dialog(self) -> None:
        """PATCH 82 — Ouvre le Gestionnaire de personnes (jusqu'ici
        accessible nulle part dans l'interface)."""
        dialog = PeopleManagerDialog(self._document, self)
        dialog.exec()
        self._render_document()

    def _new_document(self) -> None:
        """PATCH 48 — Nouveau : repart du template "Modèle OG" (Opportunity Governance)."""
        self._document = build_project_template()
        self._set_current_file(None)
        self._render_document()
        self._last_saved_snapshot = self._document_snapshot()

    def _new_blank_document(self) -> None:
        """PATCH 8 — Nouveau document vide (sans template)."""
        self._document = Document()
        self._set_current_file(None)
        self._render_document()
        self._last_saved_snapshot = self._document_snapshot()

    def _open_document(self) -> None:
        """PATCH 8 — Ouvrir : charge un document depuis un fichier JSON."""
        path_str, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.open_document"), "", "Méthodo OG (*.json)"
        )
        if not path_str:
            return
        self._load_document_from_path(Path(path_str))

    def _load_document_from_path(self, path: Path) -> None:
        """PATCH 53 — Charge un document JSON depuis un chemin donné,
        que ce soit via "Ouvrir..." ou un double-clic dans l'explorateur."""
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            document = Document.from_dict(raw)
        except (OSError, ValueError, KeyError) as exc:
            QMessageBox.critical(
                self, tr("error.open_title"), f"{tr('error.open_text')}\n{exc}"
            )
            return

        self._document = document
        self._set_current_file(path)
        self._render_document()
        self._last_saved_snapshot = self._document_snapshot()

    def _write_document(self, path: Path) -> None:
        try:
            path.write_text(
                json.dumps(self._document.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            QMessageBox.critical(
                self, tr("error.save_title"), f"{tr('error.save_text')}\n{exc}"
            )
            return
        self._set_current_file(path)
        self._last_saved_snapshot = self._document_snapshot()

    def _save_document(self) -> None:
        """PATCH 8 — Sauvegarder : réutilise le fichier courant, sinon demande où."""
        if self._current_file is None:
            self._save_document_as()
            return
        self._write_document(self._current_file)

    def _save_document_as(self) -> None:
        """PATCH 8 — Sauvegarder sous : demande toujours un nouveau fichier."""
        path_str, _ = QFileDialog.getSaveFileName(
            self, tr("dialog.save_as"), "", "Méthodo OG (*.json)"
        )
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix != ".json":
            path = path.with_suffix(".json")
        self._write_document(path)

    def _export_pdf(self) -> None:
        """PATCH 36 — Exporte le document courant en PDF."""
        path_str, _ = QFileDialog.getSaveFileName(self, tr("dialog.export_pdf"), "", "PDF (*.pdf)")
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix != ".pdf":
            path = path.with_suffix(".pdf")
        export_document_to_pdf(self._document, str(path))

    # -- Gestion des blocs texte -----------------------------------------

    def _create_text_widget(self, block: TextBlock) -> TextBlockWidget:
        """Crée un TextBlockWidget entièrement connecté."""
        widget = TextBlockWidget(block)
        widget.focused.connect(self._on_text_widget_focused)
        widget.split_requested.connect(self._on_split_requested)
        widget.merge_requested.connect(self._on_merge_requested)
        widget.delete_requested.connect(self._on_delete_requested)
        widget.command_requested.connect(self._on_command_requested)
        widget.link_activated.connect(self._scroll_to_block)
        return widget

    def _add_text_block(self, content: str = "") -> None:
        """Ajoute un nouveau bloc texte au document et à l'affichage,
        juste après le bloc actif (PATCH 67)."""
        block = TextBlock(content=content)
        widget = self._create_text_widget(block)
        self._insert_new_block(block, widget)
        widget.setFocus()

    def _add_checklist_block(self) -> None:
        """Ajoute un nouveau bloc checklist (PATCH 10), avec un premier
        élément vide, juste après le bloc actif (PATCH 67)."""
        block = ChecklistBlock()
        block.add_item()
        widget = ChecklistBlockWidget(block)
        self._insert_new_block(block, widget)

    def _add_simple_table_block(self) -> None:
        """PATCH 24 — Ajoute un tableau simple (grille de texte 2×2),
        juste après le bloc actif (PATCH 67)."""
        block = SimpleTableBlock()
        widget = SimpleTableBlockWidget(block)
        self._insert_new_block(block, widget)

    def _add_table_block(self) -> None:
        """PATCH 14 — Ajoute un nouveau bloc tableau (2 colonnes, 1 ligne),
        juste après le bloc actif (PATCH 67)."""
        block = TableBlock()
        block.add_column(name="Colonne 1")
        block.add_column(name="Colonne 2")
        block.add_row()
        widget = TableBlockWidget(block, self._document)
        self._insert_new_block(block, widget)

    def _add_list_block(self) -> None:
        """PATCH 23 — Ajoute un bloc liste (une puce vide), juste après
        le bloc actif (PATCH 67)."""
        block = ListBlock()
        block.add_item("")
        widget = ListBlockWidget(block)
        self._insert_new_block(block, widget)

    def _add_code_block(self) -> None:
        """PATCH 22 — Ajoute un bloc de code (police monospace), juste
        après le bloc actif (PATCH 67)."""
        block = CodeBlock()
        widget = CodeBlockWidget(block)
        self._insert_new_block(block, widget)

    def _add_quote_block(self) -> None:
        """PATCH 21 — Ajoute un bloc citation, juste après le bloc actif
        (PATCH 67)."""
        block = QuoteBlock()
        widget = QuoteBlockWidget(block)
        self._insert_new_block(block, widget)

    def _add_separator_block(self) -> None:
        """PATCH 20 — Ajoute un séparateur (ligne horizontale), juste
        après le bloc actif (PATCH 67)."""
        block = SeparatorBlock()
        widget = SeparatorBlockWidget(block)
        self._insert_new_block(block, widget)

    def _add_gantt_block(self) -> None:
        """PATCH 19 — Ajoute un bloc Gantt vide (à configurer via ses
        sélecteurs), juste après le bloc actif (PATCH 67)."""
        block = GanttBlock()
        widget = GanttBlockWidget(block, self._document)
        self._insert_new_block(block, widget)

    def _add_image_block(self) -> None:
        """PATCH 12 — Insère une image choisie sur le disque, juste après
        le bloc actif (PATCH 67)."""
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            tr("dialog.insert_image"),
            "",
            f"{tr('dialog.images_filter')} (*.png *.jpg *.jpeg *.gif *.bmp *.webp)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            QMessageBox.critical(
                self, tr("error.insert_title"), f"{tr('error.insert_text')}\n{exc}"
            )
            return

        block = ImageBlock(
            image_base64=base64.b64encode(raw_bytes).decode("ascii"),
            image_format=path.suffix.lstrip(".").lower() or "png",
        )
        content = self._create_content_widget_for_block(block)
        self._insert_new_block(block, content)

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

    # -- Menu de commandes "/" (PATCH 25) ----------------------------------

    def _on_command_requested(self, widget: TextBlockWidget) -> None:
        """Ouvre le menu "/" ancré sous le curseur du bloc texte vide."""
        menu = CommandMenu(self)
        menu.command_selected.connect(lambda command_id, w=widget: self._run_command(w, command_id))
        cursor_rect = widget.cursorRect()
        anchor = widget.mapToGlobal(cursor_rect.bottomLeft())
        menu.move(anchor)
        menu.show()

    def _run_command(self, widget: TextBlockWidget, command_id: str) -> None:
        """Remplace le bloc texte (contenant juste "/") par le bloc choisi."""
        if command_id == "image":
            # L'insertion d'image passe par un sélecteur de fichier ;
            # on se contente de vider le "/" puis de laisser le flux
            # habituel ajouter l'image (en fin de document).
            widget.setPlainText("")
            self._add_image_block()
            return

        factory = self._block_factory(command_id)
        if factory is None:
            return

        new_block = factory()
        doc_index = self._document.blocks.index(widget.block)
        layout_index = self._layout_index_of_content(widget)

        self._document.remove_block(widget.block.id)
        self._document.add_block(new_block, index=doc_index)

        _, old_container = self._find_container(widget)
        if old_container is not None:
            self._blocks_layout.removeWidget(old_container)
            old_container.deleteLater()

        if isinstance(new_block, TextBlock):
            new_widget = self._create_text_widget(new_block)
        else:
            new_widget = self._create_content_widget_for_block(new_block)
        self._blocks_layout.insertWidget(layout_index, self._wrap(new_widget, new_block.id))
        new_widget.setFocus()

    def _new_default_table_block(self) -> TableBlock:
        block = TableBlock()
        block.add_column(name="Colonne 1")
        block.add_column(name="Colonne 2")
        block.add_row()
        return block

    def _new_default_list_block(self) -> ListBlock:
        block = ListBlock()
        block.add_item("")
        return block