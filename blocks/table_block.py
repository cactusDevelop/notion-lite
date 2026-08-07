"""
Bloc Tableau — moteur (PATCH 14).

Un tableau est composé de colonnes (ordonnées) et de lignes
(ordonnées). Chaque ligne stocke ses valeurs dans un dictionnaire
{column_id: valeur}, ce qui permet d'ajouter/supprimer/déplacer une
colonne sans avoir à réindexer toutes les lignes.

Le typage des colonnes (PATCH 15) et les vues dérivées (Gantt,
PATCH 19) s'appuieront sur ce moteur sans le modifier.
"""
from __future__ import annotations

import uuid
from typing import Any

from core.block import Block

TABLE_BLOCK_TYPE = "table"


class TableBlock(Block):
    """Bloc tableau.

    Données (data) :
        columns: liste de {"id": str, "name": str}.
        rows: liste de {"id": str, "cells": {column_id: str}}.
    """

    def __init__(
        self,
        columns: list[dict[str, Any]] | None = None,
        rows: list[dict[str, Any]] | None = None,
        id: str | None = None,
    ) -> None:
        normalized_columns: list[dict[str, Any]] = [
            {**column, "id": column.get("id") or str(uuid.uuid4())}
            for column in (columns or [])
        ]
        column_ids = {column["id"] for column in normalized_columns}

        normalized_rows: list[dict[str, Any]] = []
        for row in rows or []:
            cells = {k: v for k, v in row.get("cells", {}).items() if k in column_ids}
            for column_id in column_ids:
                cells.setdefault(column_id, "")
            normalized_rows.append(
                {"id": row.get("id") or str(uuid.uuid4()), "cells": cells}
            )

        super().__init__(
            type=TABLE_BLOCK_TYPE,
            data={"columns": normalized_columns, "rows": normalized_rows},
            id=id or str(uuid.uuid4()),
        )

    @property
    def columns(self) -> list[dict[str, Any]]:
        return self.data.setdefault("columns", [])

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self.data.setdefault("rows", [])

    def _find_column(self, column_id: str) -> dict[str, Any] | None:
        for column in self.columns:
            if column.get("id") == column_id:
                return column
        return None

    def _find_row(self, row_id: str) -> dict[str, Any] | None:
        for row in self.rows:
            if row.get("id") == row_id:
                return row
        return None

    # -- Colonnes ----------------------------------------------------

    def add_column(self, name: str = "", index: int | None = None) -> dict[str, Any]:
        """Ajoute une colonne et une cellule vide correspondante à chaque ligne."""
        column = {"id": str(uuid.uuid4()), "name": name}
        if index is None:
            self.columns.append(column)
        else:
            self.columns.insert(index, column)
        for row in self.rows:
            row["cells"][column["id"]] = ""
        return column

    def remove_column(self, column_id: str) -> bool:
        column = self._find_column(column_id)
        if column is None:
            return False
        self.columns.remove(column)
        for row in self.rows:
            row["cells"].pop(column_id, None)
        return True

    def rename_column(self, column_id: str, name: str) -> bool:
        column = self._find_column(column_id)
        if column is None:
            return False
        column["name"] = name
        return True

    def move_column(self, column_id: str, new_index: int) -> bool:
        column = self._find_column(column_id)
        if column is None:
            return False
        self.columns.remove(column)
        new_index = max(0, min(new_index, len(self.columns)))
        self.columns.insert(new_index, column)
        return True

    # -- Lignes --------------------------------------------------------

    def add_row(self, values: dict[str, str] | None = None, index: int | None = None) -> dict[str, Any]:
        """Ajoute une ligne. `values` est indexé par id de colonne."""
        cells = {column["id"]: "" for column in self.columns}
        cells.update({k: v for k, v in (values or {}).items() if k in cells})
        row = {"id": str(uuid.uuid4()), "cells": cells}
        if index is None:
            self.rows.append(row)
        else:
            self.rows.insert(index, row)
        return row

    def remove_row(self, row_id: str) -> bool:
        row = self._find_row(row_id)
        if row is None:
            return False
        self.rows.remove(row)
        return True

    def move_row(self, row_id: str, new_index: int) -> bool:
        row = self._find_row(row_id)
        if row is None:
            return False
        self.rows.remove(row)
        new_index = max(0, min(new_index, len(self.rows)))
        self.rows.insert(new_index, row)
        return True

    def set_cell(self, row_id: str, column_id: str, value: str) -> bool:
        row = self._find_row(row_id)
        if row is None or self._find_column(column_id) is None:
            return False
        row["cells"][column_id] = value
        return True
