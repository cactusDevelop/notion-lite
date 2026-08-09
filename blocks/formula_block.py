"""
Bloc "Résultat calculé" (PATCH 45).

Comme GanttBlock, ne stocke AUCUNE donnée de projet : uniquement une
référence (id du TableBlock visé, id d'une colonne "Nombre" et d'une
colonne "Booléen" de ce tableau) et un libellé. Le résultat affiché
(somme de la colonne "Nombre" pour les lignes où la colonne
"Booléen" est cochée, sur somme totale de la colonne "Nombre") est
entièrement recalculé à chaque lecture, à partir de l'état courant
du Document.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from blocks.table_block import COLUMN_TYPE_BOOLEAN, COLUMN_TYPE_NUMBER, TableBlock
from core.block import Block

FORMULA_BLOCK_TYPE = "formula"

_DEFAULT_LABEL = "Résultat: "


class FormulaBlock(Block):
    """Bloc de résultat calculé : référence vers un TableBlock + 2 colonnes.

    Données (data) :
        table_block_id: id du TableBlock source (ou None si non configuré).
        number_column_id: id de la colonne "Nombre" à sommer.
        boolean_column_id: id de la colonne "Booléen" utilisée comme filtre.
        label: texte affiché avant le résultat (ex: "Résultat: ").
    """

    def __init__(
        self,
        table_block_id: Optional[str] = None,
        number_column_id: Optional[str] = None,
        boolean_column_id: Optional[str] = None,
        label: str = _DEFAULT_LABEL,
        id: str | None = None,
    ) -> None:
        super().__init__(
            type=FORMULA_BLOCK_TYPE,
            data={
                "table_block_id": table_block_id,
                "number_column_id": number_column_id,
                "boolean_column_id": boolean_column_id,
                "label": label,
            },
            id=id or str(uuid.uuid4()),
        )

    @property
    def table_block_id(self) -> Optional[str]:
        return self.data.get("table_block_id")

    @property
    def number_column_id(self) -> Optional[str]:
        return self.data.get("number_column_id")

    @property
    def boolean_column_id(self) -> Optional[str]:
        return self.data.get("boolean_column_id")

    @property
    def label(self) -> str:
        return self.data.get("label", _DEFAULT_LABEL)

    @label.setter
    def label(self, value: str) -> None:
        self.data["label"] = value

    def set_source(
        self,
        table_block_id: Optional[str],
        number_column_id: Optional[str] = None,
        boolean_column_id: Optional[str] = None,
    ) -> None:
        """Configure (ou reconfigure) la source du calcul."""
        self.data["table_block_id"] = table_block_id
        self.data["number_column_id"] = number_column_id
        self.data["boolean_column_id"] = boolean_column_id


def find_source_table(document, formula_block: FormulaBlock) -> Optional[TableBlock]:
    """Retrouve le TableBlock référencé par le calcul dans le document courant."""
    if formula_block.table_block_id is None:
        return None
    block = document.find_block(formula_block.table_block_id)
    return block if isinstance(block, TableBlock) else None


def available_number_columns(table: TableBlock) -> list[dict[str, Any]]:
    return [column for column in table.columns if column["type"] == COLUMN_TYPE_NUMBER]


def available_boolean_columns(table: TableBlock) -> list[dict[str, Any]]:
    return [column for column in table.columns if column["type"] == COLUMN_TYPE_BOOLEAN]


def _to_number(value: Any) -> float:
    try:
        return float(str(value).replace(",", ".").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def compute_formula_result(document, formula_block: FormulaBlock) -> Optional[tuple[float, float]]:
    """Recalcule (somme_cochée, somme_totale) à partir de l'état actuel du
    document, ou None si la source n'est pas (ou plus) valide.

    Ne lit ni ne modifie aucune donnée propre au FormulaBlock : tout
    vient du TableBlock référencé, relu à chaque appel (même principe
    que compute_gantt_rows pour le bloc Gantt).
    """
    table = find_source_table(document, formula_block)
    if table is None:
        return None

    number_column = table._find_column(formula_block.number_column_id) if formula_block.number_column_id else None
    if number_column is None or number_column["type"] != COLUMN_TYPE_NUMBER:
        return None

    boolean_column = table._find_column(formula_block.boolean_column_id) if formula_block.boolean_column_id else None
    if boolean_column is None or boolean_column["type"] != COLUMN_TYPE_BOOLEAN:
        return None

    total = 0.0
    checked_total = 0.0
    for row in table.rows:
        value = _to_number(row["cells"].get(number_column["id"]))
        total += value
        if row["cells"].get(boolean_column["id"]):
            checked_total += value
    return checked_total, total


def _format_number(value: float) -> str:
    """Affiche les entiers sans décimale (ex: 12 plutôt que 12.0)."""
    if value == int(value):
        return str(int(value))
    return str(value)


def format_formula_text(formula_block: FormulaBlock, result: Optional[tuple[float, float]]) -> str:
    if result is None:
        return f"{formula_block.label}(source non configurée)"
    checked_total, total = result
    return f"{formula_block.label}{_format_number(checked_total)} / {_format_number(total)}"
