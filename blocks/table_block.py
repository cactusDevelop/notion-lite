"""
Bloc Tableau — moteur (PATCH 14) + colonnes typées (PATCH 15).

Un tableau est composé de colonnes (ordonnées) et de lignes
(ordonnées). Chaque ligne stocke ses valeurs dans un dictionnaire
{column_id: valeur}, ce qui permet d'ajouter/supprimer/déplacer une
colonne sans avoir à réindexer toutes les lignes.

Chaque colonne possède un type fixe (PATCH 15) qui détermine la
forme de la valeur stockée dans les cellules correspondantes :
    - text / number : chaîne de caractères.
    - date : chaîne ISO "AAAA-MM-JJ" (ou "").
    - duration : {"amount": int, "unit": "heures"|"jours"|"semaines"}.
    - boolean : bool.
    - person : liste de noms (str).
    - select : chaîne parmi column["options"] (ou "").
    - multi_select : liste de chaînes parmi column["options"].
    - checklist : liste de {"id": str, "text": str, "checked": bool}.

Les vues dérivées (Gantt, PATCH 19) et les gestionnaires dédiés
(Personne PATCH 16, Durée PATCH 17) s'appuieront sur ce typage sans
changer la structure de base posée ici.
"""
from __future__ import annotations

import uuid
from typing import Any

from core.block import Block

TABLE_BLOCK_TYPE = "table"

COLUMN_TYPE_TEXT = "text"
COLUMN_TYPE_NUMBER = "number"
COLUMN_TYPE_DATE = "date"
COLUMN_TYPE_DURATION = "duration"
COLUMN_TYPE_BOOLEAN = "boolean"
COLUMN_TYPE_PERSON = "person"
COLUMN_TYPE_SELECT = "select"
COLUMN_TYPE_MULTI_SELECT = "multi_select"
COLUMN_TYPE_CHECKLIST = "checklist"

COLUMN_TYPES: list[str] = [
    COLUMN_TYPE_TEXT,
    COLUMN_TYPE_NUMBER,
    COLUMN_TYPE_DATE,
    COLUMN_TYPE_DURATION,
    COLUMN_TYPE_BOOLEAN,
    COLUMN_TYPE_PERSON,
    COLUMN_TYPE_SELECT,
    COLUMN_TYPE_MULTI_SELECT,
    COLUMN_TYPE_CHECKLIST,
]

COLUMN_TYPE_LABELS: dict[str, str] = {
    COLUMN_TYPE_TEXT: "Texte",
    COLUMN_TYPE_NUMBER: "Nombre",
    COLUMN_TYPE_DATE: "Date",
    COLUMN_TYPE_DURATION: "Durée",
    COLUMN_TYPE_BOOLEAN: "Booléen",
    COLUMN_TYPE_PERSON: "Personne",
    COLUMN_TYPE_SELECT: "Liste",
    COLUMN_TYPE_MULTI_SELECT: "Liste multiple",
    COLUMN_TYPE_CHECKLIST: "Checklist",
}

DURATION_UNITS: list[str] = ["heures", "jours", "semaines"]


def default_value_for_type(col_type: str) -> Any:
    """Valeur par défaut d'une cellule neuve, selon le type de sa colonne."""
    if col_type == COLUMN_TYPE_BOOLEAN:
        return False
    if col_type == COLUMN_TYPE_DURATION:
        return {"amount": 0, "unit": DURATION_UNITS[1]}
    if col_type in (COLUMN_TYPE_PERSON, COLUMN_TYPE_MULTI_SELECT, COLUMN_TYPE_CHECKLIST):
        return []
    return ""


def _normalize_value_for_type(col_type: str, value: Any) -> Any:
    """Ramène une valeur potentiellement invalide/absente à une forme
    cohérente avec le type de la colonne (utilisé au chargement)."""
    if col_type == COLUMN_TYPE_BOOLEAN:
        return bool(value)
    if col_type == COLUMN_TYPE_DURATION:
        if isinstance(value, dict):
            unit = value.get("unit") if value.get("unit") in DURATION_UNITS else DURATION_UNITS[1]
            try:
                amount = int(value.get("amount", 0))
            except (TypeError, ValueError):
                amount = 0
            return {"amount": amount, "unit": unit}
        return default_value_for_type(col_type)
    if col_type in (COLUMN_TYPE_PERSON, COLUMN_TYPE_MULTI_SELECT):
        return list(value) if isinstance(value, list) else []
    if col_type == COLUMN_TYPE_CHECKLIST:
        items = value if isinstance(value, list) else []
        return [
            {
                "id": item.get("id") or str(uuid.uuid4()),
                "text": item.get("text", ""),
                "checked": bool(item.get("checked", False)),
            }
            for item in items
            if isinstance(item, dict)
        ]
    return value if value is not None else ""


class TableBlock(Block):
    """Bloc tableau.

    Données (data) :
        columns: liste de {"id": str, "name": str, "type": str, "options": list[str]}.
        rows: liste de {"id": str, "cells": {column_id: valeur}}.
    """

    def __init__(
        self,
        columns: list[dict[str, Any]] | None = None,
        rows: list[dict[str, Any]] | None = None,
        id: str | None = None,
    ) -> None:
        normalized_columns: list[dict[str, Any]] = []
        for column in columns or []:
            col_type = column.get("type") if column.get("type") in COLUMN_TYPES else COLUMN_TYPE_TEXT
            normalized_columns.append(
                {
                    "id": column.get("id") or str(uuid.uuid4()),
                    "name": column.get("name", ""),
                    "type": col_type,
                    "options": list(column.get("options", [])),
                }
            )
        columns_by_id = {column["id"]: column for column in normalized_columns}

        normalized_rows: list[dict[str, Any]] = []
        for row in rows or []:
            raw_cells = row.get("cells", {})
            cells = {
                column_id: _normalize_value_for_type(column["type"], raw_cells.get(column_id))
                for column_id, column in columns_by_id.items()
            }
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

    def add_column(
        self,
        name: str = "",
        col_type: str = COLUMN_TYPE_TEXT,
        options: list[str] | None = None,
        index: int | None = None,
    ) -> dict[str, Any]:
        """Ajoute une colonne typée et une cellule par défaut à chaque ligne."""
        if col_type not in COLUMN_TYPES:
            col_type = COLUMN_TYPE_TEXT
        column = {
            "id": str(uuid.uuid4()),
            "name": name,
            "type": col_type,
            "options": list(options or []),
        }
        if index is None:
            self.columns.append(column)
        else:
            self.columns.insert(index, column)
        for row in self.rows:
            row["cells"][column["id"]] = default_value_for_type(col_type)
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

    def set_column_options(self, column_id: str, options: list[str]) -> bool:
        """Définit les choix possibles d'une colonne "Liste"/"Liste multiple".

        Les cellules "select" dont la valeur n'est plus dans les choix
        sont réinitialisées ; pour "multi_select", seules les valeurs
        encore valides sont conservées.
        """
        column = self._find_column(column_id)
        if column is None:
            return False
        column["options"] = list(options)
        if column["type"] == COLUMN_TYPE_SELECT:
            for row in self.rows:
                if row["cells"].get(column_id) not in column["options"]:
                    row["cells"][column_id] = ""
        elif column["type"] == COLUMN_TYPE_MULTI_SELECT:
            for row in self.rows:
                current = row["cells"].get(column_id) or []
                row["cells"][column_id] = [v for v in current if v in column["options"]]
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

    def add_row(self, values: dict[str, Any] | None = None, index: int | None = None) -> dict[str, Any]:
        """Ajoute une ligne. `values` est indexé par id de colonne."""
        cells = {column["id"]: default_value_for_type(column["type"]) for column in self.columns}
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

    def get_cell(self, row_id: str, column_id: str) -> Any:
        row = self._find_row(row_id)
        if row is None:
            return None
        return row["cells"].get(column_id)

    def set_cell(self, row_id: str, column_id: str, value: Any) -> bool:
        row = self._find_row(row_id)
        column = self._find_column(column_id)
        if row is None or column is None:
            return False
        row["cells"][column_id] = _normalize_value_for_type(column["type"], value)
        return True
