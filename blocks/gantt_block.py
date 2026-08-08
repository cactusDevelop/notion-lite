"""
Bloc Gantt (PATCH 19).

Le bloc Gantt ne stocke AUCUNE donnée de projet : il conserve
uniquement une référence (id du bloc Tableau visé, id de la colonne
utilisée comme libellé, id de la colonne Date utilisée pour les
barres). Toute lecture recalcule les barres à partir de l'état actuel
du Document ; une modification du tableau est donc reflétée sans
aucune synchronisation manuelle, puisqu'il n'y a rien à synchroniser.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from blocks.table_block import COLUMN_TYPE_DATE, COLUMN_TYPE_TEXT, TableBlock
from core.block import Block

GANTT_BLOCK_TYPE = "gantt"


class GanttBlock(Block):
    """Bloc Gantt : simple référence vers un TableBlock et ses colonnes.

    Données (data) :
        table_block_id: id du TableBlock source (ou None si non configuré).
        label_column_id: id de la colonne utilisée comme libellé de ligne.
        date_column_id: id de la colonne Date utilisée pour les barres.
    """

    def __init__(
        self,
        table_block_id: Optional[str] = None,
        label_column_id: Optional[str] = None,
        date_column_id: Optional[str] = None,
        id: str | None = None,
    ) -> None:
        super().__init__(
            type=GANTT_BLOCK_TYPE,
            data={
                "table_block_id": table_block_id,
                "label_column_id": label_column_id,
                "date_column_id": date_column_id,
            },
            id=id or str(uuid.uuid4()),
        )

    @property
    def table_block_id(self) -> Optional[str]:
        return self.data.get("table_block_id")

    @property
    def label_column_id(self) -> Optional[str]:
        return self.data.get("label_column_id")

    @property
    def date_column_id(self) -> Optional[str]:
        return self.data.get("date_column_id")

    def set_source(
        self,
        table_block_id: Optional[str],
        label_column_id: Optional[str] = None,
        date_column_id: Optional[str] = None,
    ) -> None:
        """Configure (ou reconfigure) la source du Gantt."""
        self.data["table_block_id"] = table_block_id
        self.data["label_column_id"] = label_column_id
        self.data["date_column_id"] = date_column_id


def find_source_table(document, gantt_block: GanttBlock) -> Optional[TableBlock]:
    """Retrouve le TableBlock référencé par le Gantt dans le document courant."""
    if gantt_block.table_block_id is None:
        return None
    block = document.find_block(gantt_block.table_block_id)
    return block if isinstance(block, TableBlock) else None


def available_date_columns(table: TableBlock) -> list[dict[str, Any]]:
    """Colonnes "Date" utilisables comme source de barres du Gantt."""
    return [column for column in table.columns if column["type"] == COLUMN_TYPE_DATE]


def _default_label_column(table: TableBlock) -> Optional[dict[str, Any]]:
    for column in table.columns:
        if column["type"] == COLUMN_TYPE_TEXT:
            return column
    return table.columns[0] if table.columns else None


def compute_gantt_rows(document, gantt_block: GanttBlock) -> list[dict[str, Any]]:
    """Recalcule les lignes du Gantt à partir de l'état actuel du document.

    Ne lit ni ne modifie aucune donnée propre au GanttBlock : tout vient
    du TableBlock référencé, relu à chaque appel (PATCH 19).

    Retourne une liste de {"row_id", "label", "start", "end"} ("start"/
    "end" sont des chaînes ISO "AAAA-MM-JJ", ou None si non renseignées).
    """
    table = find_source_table(document, gantt_block)
    if table is None:
        return []

    label_column = table._find_column(gantt_block.label_column_id) if gantt_block.label_column_id else None
    if label_column is None:
        label_column = _default_label_column(table)

    date_column = table._find_column(gantt_block.date_column_id) if gantt_block.date_column_id else None
    if date_column is None or date_column["type"] != COLUMN_TYPE_DATE:
        return []

    rows: list[dict[str, Any]] = []
    for row in table.rows:
        label = str(row["cells"].get(label_column["id"], "")) if label_column else ""
        date_value = row["cells"].get(date_column["id"])
        if date_column.get("range"):
            start = (date_value or {}).get("start") or None
            end = (date_value or {}).get("end") or None
        else:
            start = date_value or None
            end = start
        rows.append({"row_id": row["id"], "label": label, "start": start, "end": end})
    return rows
