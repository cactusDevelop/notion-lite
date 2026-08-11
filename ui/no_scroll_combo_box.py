"""
PATCH 56 — QComboBox qui ignore la molette de la souris.

Par défaut, Qt change la valeur sélectionnée d'un QComboBox fermé
lorsque la molette est actionnée au-dessus de lui, ce qui est source
d'erreurs de saisie quand on fait défiler une page ou un tableau
contenant des menus déroulants (la valeur change sans intention).
`NoScrollComboBox` désactive ce comportement : la molette au-dessus
du widget n'a aucun effet et l'événement est transmis au parent (pour
que le scroll de la page/du tableau fonctionne normalement), sans
jamais changer l'élément sélectionné.

À utiliser à la place de `QComboBox` partout où l'application crée un
menu déroulant.
"""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox


class NoScrollComboBox(QComboBox):
    """QComboBox dont la molette ne modifie jamais la sélection."""

    def wheelEvent(self, event) -> None:  # noqa: N802
        event.ignore()
