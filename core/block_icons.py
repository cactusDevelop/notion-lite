"""
Icône représentative d'un bloc (PATCH 34).

Fonction pure (indépendante de Qt) : associe à chaque type de bloc un
symbole Unicode, affiché à gauche de chaque bloc dans le document
(voir BlockContainer). Centralisé ici pour rester la seule source de
vérité, réutilisable aussi bien par l'UI que par d'éventuels exports
(PATCH 36-38).
"""
from __future__ import annotations

from blocks.bar_chart_block import BarChartBlock
from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.dependency_gantt_block import DependencyGanttBlock
from blocks.formula_block import FormulaBlock
from blocks.gantt_block import GanttBlock
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.line_chart_block import LineChartBlock
from blocks.linked_checklist_block import LinkedChecklistBlock
from blocks.list_block import ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import TableBlock
from blocks.text_block import TextBlock

_DEFAULT_ICON = "▫"

# Associe chaque type concret de bloc à un symbole représentatif.
# Utilise des tuples (type, symbole) plutôt qu'un dict indexé par
# classe pour préserver un ordre de vérification déterministe avec
# `isinstance` (utile car HeadingBlock hérite indirectement du même
# module que TextBlock sans en être une sous-classe : pas de risque
# de faux positif ici, mais garde la même logique que block_preview).
_ICON_RULES: list[tuple[type, str]] = [
    (HeadingBlock, "H"),
    (TextBlock, "¶"),
    (ChecklistBlock, "☑"),
    (LinkedChecklistBlock, "⇄"),
    (ListBlock, "•"),
    (TableBlock, "▦"),
    (SimpleTableBlock, "▤"),
    (GanttBlock, "📊"),
    (DependencyGanttBlock, "📈"),
    (LineChartBlock, "📉"),
    (BarChartBlock, "📶"),
    (FormulaBlock, "Σ"),
    (ImageBlock, "🖼"),
    (QuoteBlock, "❝"),
    (CodeBlock, "</>"),
    (SeparatorBlock, "―"),
]


def icon_for_block(block) -> str:
    """Symbole représentatif du type de `block` (ou une icône générique
    par défaut si le type n'est pas reconnu)."""
    for block_type, icon in _ICON_RULES:
        if isinstance(block, block_type):
            return icon
    return _DEFAULT_ICON
