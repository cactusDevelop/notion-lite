"""
Bloc Tableau simple (PATCH 24).

Contrairement au bloc Tableau du PATCH 14 (colonnes typées, id
stables par colonne/ligne, pensé comme une mini base de données), ce
bloc est une grille de texte légère et purement positionnelle : une
liste de lignes, chaque ligne étant une liste de chaînes de même
longueur. Aucun typage, aucune option, aucune id par cellule —
volontairement indépendant du moteur du PATCH 14.

Adapté à un simple tableau de mise en page (ex. copier/coller un
petit tableau markdown), pas à une base de données.
"""
from __future__ import annotations

import uuid

from core.block import Block

SIMPLE_TABLE_BLOCK_TYPE = "simple_table"


def _rectangularize(rows: list[list[str]]) -> list[list[str]]:
    """Complète les lignes trop courtes avec des cellules vides pour
    garantir une grille rectangulaire (nombre de colonnes uniforme)."""
    width = max((len(row) for row in rows), default=0)
    return [list(row) + [""] * (width - len(row)) for row in rows]


class SimpleTableBlock(Block):
    """Grille de texte simple.

    Données (data) :
        rows: liste de lignes, chaque ligne étant une liste de
            chaînes (une par colonne). Toutes les lignes ont la même
            longueur (garanti par `_rectangularize`).
    """

    def __init__(
        self,
        rows: list[list[str]] | None = None,
        row_count: int = 2,
        column_count: int = 2,
        id: str | None = None,
    ) -> None:
        if rows is None:
            rows = [["" for _ in range(column_count)] for _ in range(row_count)]
        super().__init__(
            type=SIMPLE_TABLE_BLOCK_TYPE,
            data={"rows": _rectangularize(rows)},
            id=id or str(uuid.uuid4()),
        )

    @property
    def rows(self) -> list[list[str]]:
        return self.data.setdefault("rows", [])

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.rows[0]) if self.rows else 0

    def get_cell(self, row_index: int, column_index: int) -> str:
        return self.rows[row_index][column_index]

    def set_cell(self, row_index: int, column_index: int, text: str) -> bool:
        if not (0 <= row_index < self.row_count and 0 <= column_index < self.column_count):
            return False
        self.rows[row_index][column_index] = text
        return True

    def add_row(self, index: int | None = None) -> None:
        new_row = ["" for _ in range(self.column_count)]
        if index is None:
            self.rows.append(new_row)
        else:
            self.rows.insert(max(0, min(index, self.row_count)), new_row)

    def remove_row(self, index: int) -> bool:
        if not (0 <= index < self.row_count):
            return False
        del self.rows[index]
        return True

    def add_column(self, index: int | None = None) -> None:
        col_index = self.column_count if index is None else max(0, min(index, self.column_count))
        for row in self.rows:
            row.insert(col_index, "")

    def remove_column(self, index: int) -> bool:
        if not (0 <= index < self.column_count):
            return False
        for row in self.rows:
            del row[index]
        return True
