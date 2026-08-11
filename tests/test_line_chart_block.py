from __future__ import annotations

from blocks.dependency_gantt_block import DependencyGanttBlock
from blocks.line_chart_block import (
    SLOPE_MODE_CONSTANT,
    SLOPE_MODE_EFFICIENCY,
    LineChartBlock,
    compute_line_series,
    resolve_series_slope,
)
from blocks.registry import block_from_dict
from blocks.table_block import COLUMN_TYPE_MULTI_SELECT, COLUMN_TYPE_NUMBER, COLUMN_TYPE_TEXT, TableBlock
from core.document import Document


def test_constant_slope_series():
    doc = Document()
    block = LineChartBlock(x_max=10)
    block.add_series(name="Idéal", mode=SLOPE_MODE_CONSTANT, slope=1.0)
    doc.add_block(block)

    series = compute_line_series(doc, block)
    assert len(series) == 1
    assert series[0]["x0"] == 0.0 and series[0]["y0"] == 0.0
    assert series[0]["x1"] == 10.0 and series[0]["y1"] == 10.0


def test_efficiency_slope_series_tracks_dependency_gantt():
    doc = Document()
    table = TableBlock()
    label_col = table.add_column("Sous-tâches", col_type=COLUMN_TYPE_TEXT)
    duration_col = table.add_column("Durée", col_type=COLUMN_TYPE_NUMBER)
    dep_col = table.add_column("Dépendances", col_type=COLUMN_TYPE_MULTI_SELECT)
    table.add_row(values={label_col["id"]: "A", duration_col["id"]: "8", dep_col["id"]: []})
    doc.add_block(table)

    gantt = DependencyGanttBlock(
        table_block_id=table.id, label_column_id=label_col["id"], duration_column_id=duration_col["id"]
    )
    doc.add_block(gantt)

    chart = LineChartBlock(x_max=10)
    chart.add_series(name="Vélocité réelle", mode=SLOPE_MODE_EFFICIENCY, source_block_id=gantt.id)
    doc.add_block(chart)

    # Aucun retard : ratio = 8 / (8 + 0) = 1.0
    series = compute_line_series(doc, chart)
    assert series[0]["slope"] == 1.0

    # 4 jours de retard : ratio = 8 / (8 + 4) = 0.666...
    gantt.set_delta(table.rows[0]["id"], 4)
    series = compute_line_series(doc, chart)
    assert abs(series[0]["slope"] - (8 / 12)) < 1e-9
    # PATCH 52 — la droite atteint toujours la même hauteur (y_scale =
    # x_max = 10), donc y1 reste 10 quelle que soit la pente ; c'est
    # l'abscisse x1 qui change (10 / pente).
    assert series[0]["y1"] == 10.0
    assert abs(series[0]["x1"] - (10 / (8 / 12))) < 1e-9


def test_efficiency_series_without_valid_source_defaults_to_zero():
    doc = Document()
    chart = LineChartBlock()
    chart.add_series(name="X", mode=SLOPE_MODE_EFFICIENCY, source_block_id="inconnu")
    doc.add_block(chart)

    series = compute_line_series(doc, chart)
    assert series[0]["slope"] == 0.0


def test_remove_and_rename_series():
    block = LineChartBlock()
    s = block.add_series(name="A")
    block.add_series(name="B")

    assert block.set_series_name(s["id"], "A renommée")
    assert block._find_series(s["id"])["name"] == "A renommée"
    assert block.remove_series(s["id"])
    assert len(block.series) == 1
    assert not block.remove_series("id-inconnu")


def test_different_slopes_end_at_same_height_different_x():
    """PATCH 52 — évite que les droites/étiquettes se superposent :
    toutes atteignent la même hauteur (y_scale = x_max), mais à des
    abscisses différentes selon leur pente."""
    doc = Document()
    block = LineChartBlock(x_max=10)
    block.add_series(name="Idéal", mode=SLOPE_MODE_CONSTANT, slope=1.0)
    block.add_series(name="Vélocité", mode=SLOPE_MODE_CONSTANT, slope=0.5)
    doc.add_block(block)

    series = compute_line_series(doc, block)
    assert series[0]["y1"] == series[1]["y1"] == 10.0
    assert series[0]["x1"] != series[1]["x1"]
    assert series[1]["x1"] == 20.0  # pente 0.5 : il faut x=20 pour atteindre y=10


def test_non_positive_slope_falls_back_to_flat_segment():
    doc = Document()
    block = LineChartBlock(x_max=10)
    block.add_series(name="Nulle", mode=SLOPE_MODE_CONSTANT, slope=0.0)
    doc.add_block(block)

    series = compute_line_series(doc, block)
    assert series[0]["x1"] == 10.0
    assert series[0]["y1"] == 0.0


def test_axis_labels_default_empty_and_are_settable():
    block = LineChartBlock()
    assert block.x_axis_label == ""
    assert block.y_axis_label == ""
    block.x_axis_label = "Temps"
    block.y_axis_label = "Avancement moyen"
    assert block.x_axis_label == "Temps"
    assert block.y_axis_label == "Avancement moyen"


def test_roundtrip_via_registry():
    block = LineChartBlock(title="Efficacité", x_axis_label="Temps", y_axis_label="Avancement moyen", x_max=20)
    block.add_series(name="Idéal", mode=SLOPE_MODE_CONSTANT, slope=1.0)
    block.add_series(name="Vélocité", mode=SLOPE_MODE_EFFICIENCY, source_block_id="gantt-1")

    rebuilt = block_from_dict(block.to_dict())
    assert isinstance(rebuilt, LineChartBlock)
    assert rebuilt.title == "Efficacité"
    assert rebuilt.x_axis_label == "Temps"
    assert rebuilt.y_axis_label == "Avancement moyen"
    assert rebuilt.x_max == 20
    assert len(rebuilt.series) == 2
    assert rebuilt.series[1]["source_block_id"] == "gantt-1"
