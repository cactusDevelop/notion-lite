"""
Barre d'outils principale.

PATCH 5 : actions de base (nouveau bloc, mise en forme simple).
PATCH 6 : mise en forme complète (barré, alignement, listes,
citation, code).
PATCH 80 : tous les libellés passent par `tr()` (voir ui.i18n) ; les
actions sont retraduites via `retranslate()` quand la langue change.

La toolbar fait partie du cadre de QMainWindow (pas de la zone de
contenu défilable) : tout ce qu'elle contient, y compris le bouton
d'information, reste donc fixe en haut, indépendamment du scroll.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QSizePolicy, QSpinBox, QToolBar, QWidget

from ui.i18n import tr

# (clé d'action, clé i18n du libellé). i18n_key=None -> séparateur.
_ACTIONS: list[tuple[str, Optional[str]]] = [
    ("new_block", "toolbar.new_block"),
    ("new_checklist", "toolbar.new_checklist"),
    ("new_image", "toolbar.new_image"),
    ("new_table", "toolbar.new_table"),
    ("new_simple_table", "toolbar.new_simple_table"),
    ("new_gantt", "toolbar.new_gantt"),
    ("new_separator", "toolbar.new_separator"),
    ("new_quote", "toolbar.new_quote"),
    ("new_code", "toolbar.new_code"),
    ("new_list", "toolbar.new_list"),
    ("sep1", None),
    ("bold", "toolbar.bold"),
    ("italic", "toolbar.italic"),
    ("underline", "toolbar.underline"),
    ("strikethrough", "toolbar.strikethrough"),
    ("sep2", None),
    ("align_left", "toolbar.align_left"),
    ("align_center", "toolbar.align_center"),
    ("align_right", "toolbar.align_right"),
    ("align_justify", "toolbar.align_justify"),
    ("sep3", None),
    ("bullet_list", "toolbar.bullet_list"),
    ("numbered_list", "toolbar.numbered_list"),
    ("quote", "toolbar.quote"),
    ("code", "toolbar.code"),
    ("sep4", None),
    ("color", "toolbar.color"),
    ("sep5", None),
    ("insert_link", "toolbar.insert_link"),
    ("insert_emoji", "toolbar.insert_emoji"),
]


class MainToolBar(QToolBar):
    """Barre d'outils exposant les actions de mise en forme de l'éditeur.

    Args:
        actions: dictionnaire {clé_action: callback sans argument},
            une entrée par clé listée dans _ACTIONS (hors séparateurs).
        on_size_changed: callback appelé avec la nouvelle taille en pt.
        on_info: callback appelé au clic sur l'icône d'information.
        info_icon_path: chemin vers l'icône (i) affichée à droite.
    """

    def __init__(
        self,
        actions: dict[str, Callable[[], None]],
        on_size_changed: Callable[[int], None],
        on_info: Callable[[], None],
        info_icon_path: str,
        parent=None,
    ) -> None:
        super().__init__(tr("toolbar.title"), parent)
        self.setMovable(False)

        self._actions_by_key: dict[str, QAction] = {}
        for key, i18n_key in _ACTIONS:
            if i18n_key is None:
                self.addSeparator()
                continue
            action = QAction(tr(i18n_key), self)
            action.triggered.connect(actions[key])
            self.addAction(action)
            self._actions_by_key[key] = action

        self._size_spin = QSpinBox(self)
        self._size_spin.setRange(8, 72)
        self._size_spin.setValue(14)
        self._size_spin.setSuffix(" pt")
        self._size_spin.valueChanged.connect(on_size_changed)
        self.addWidget(self._size_spin)

        # Pousse ce qui suit (l'icône d'info) tout à droite de la barre.
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)

        self._info_action = QAction(QIcon(info_icon_path), "", self)
        self._info_action.setToolTip(tr("toolbar.info_tooltip"))
        self._info_action.triggered.connect(on_info)
        self.addAction(self._info_action)

    def retranslate(self) -> None:
        """PATCH 80 — réapplique `tr()` aux libellés (changement de langue)."""
        self.setWindowTitle(tr("toolbar.title"))
        for key, i18n_key in _ACTIONS:
            if i18n_key is None:
                continue
            self._actions_by_key[key].setText(tr(i18n_key))
        self._info_action.setToolTip(tr("toolbar.info_tooltip"))
