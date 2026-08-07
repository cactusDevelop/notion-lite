"""
Barre d'outils principale.

PATCH 5 : actions de base (nouveau bloc, mise en forme simple).
PATCH 6 : mise en forme complète (barré, alignement, listes,
citation, code).
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QSpinBox, QToolBar

# (clé d'action, libellé affiché). label=None -> séparateur.
_ACTIONS: list[tuple[str, Optional[str]]] = [
    ("new_block", "Nouveau bloc"),
    ("sep1", None),
    ("bold", "Gras"),
    ("italic", "Italique"),
    ("underline", "Souligné"),
    ("strikethrough", "Barré"),
    ("sep2", None),
    ("align_left", "Aligner à gauche"),
    ("align_center", "Centrer"),
    ("align_right", "Aligner à droite"),
    ("align_justify", "Justifier"),
    ("sep3", None),
    ("bullet_list", "Liste à puces"),
    ("numbered_list", "Liste numérotée"),
    ("quote", "Citation"),
    ("code", "Code"),
    ("sep4", None),
    ("color", "Couleur"),
]


class MainToolBar(QToolBar):
    """Barre d'outils exposant les actions de mise en forme de l'éditeur.

    Args:
        actions: dictionnaire {clé_action: callback sans argument},
            une entrée par clé listée dans _ACTIONS (hors séparateurs).
        on_size_changed: callback appelé avec la nouvelle taille en pt.
    """

    def __init__(
        self,
        actions: dict[str, Callable[[], None]],
        on_size_changed: Callable[[int], None],
        parent=None,
    ) -> None:
        super().__init__("Barre d'outils", parent)
        self.setMovable(False)

        for key, label in _ACTIONS:
            if label is None:
                self.addSeparator()
                continue
            action = QAction(label, self)
            action.triggered.connect(actions[key])
            self.addAction(action)

        self._size_spin = QSpinBox(self)
        self._size_spin.setRange(8, 72)
        self._size_spin.setValue(14)
        self._size_spin.setSuffix(" pt")
        self._size_spin.valueChanged.connect(on_size_changed)
        self.addWidget(self._size_spin)
