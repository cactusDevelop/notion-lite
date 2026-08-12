"""
Widget graphique du bloc "Courbes" (PATCH 47, révisé PATCH 52, PATCH 58).

PATCH 52 :
    - Titre et noms d'axes éditables directement au clic (comme un
      titre), sans préfixe "Titre :" / "Axe X :" — un champ vide
      affiche un texte de substitution ("Titre", "Axe X", "Axe Y").
    - Le graphique n'est plus limité à un carré fixe : la hauteur
      reste "carrée" (échelle de référence de la droite "idéal"),
      mais la largeur s'élargit pour que les droites de pentes
      différentes se terminent à des abscisses différentes (voir
      compute_line_series), formant un rectangle plutôt qu'un carré.
    - Les étiquettes de série sont placées à droite de la fin de
      chaque droite (jamais au-dessus), avec un anti-chevauchement
      simple qui les décale verticalement si elles se recouvrent.

PATCH 58 : noms d'axes repositionnés à l'instar du graphique "Delta de
budget" (bâtonnets) — l'axe Y est dessiné à la verticale, le long de
l'axe des ordonnées du graphique (au lieu d'un champ de texte
horizontal au-dessus, qui ne ressemblait pas à un nom d'axe), et le
nom de l'axe X est centré sous le graphique plutôt qu'aligné à gauche
sur toute la largeur du bloc. Les deux restent éditables au clic,
comme avant.
"""
from __future__ import annotations

from PySide6.QtCore import QRect, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from blocks.dependency_gantt_block import DependencyGanttBlock
from blocks.line_chart_block import (
    SLOPE_MODE_CONSTANT,
    SLOPE_MODE_EFFICIENCY,
    LineChartBlock,
    compute_line_series,
)
from ui.no_scroll_combo_box import NoScrollComboBox

_REFRESH_INTERVAL_MS = 500
_MARGIN = 30
_PLOT_HEIGHT = 220
_LABEL_GUTTER = 140
_LABEL_WIDTH = 130
_LABEL_HEIGHT = 16
# PATCH 58 — place réservée à gauche pour le nom de l'axe Y vertical
# (à l'instar de _MARGIN utilisée par le graphique "Delta de budget"),
# et sous le graphique pour le nom de l'axe X centré.
_Y_AXIS_GUTTER = 22
_X_AXIS_GUTTER = 20

_TITLE_STYLE = "QLineEdit { border: none; background: transparent; font-weight: bold; font-size: 15pt; }"
_AXIS_STYLE = "QLineEdit { border: none; background: transparent; color: #666666; }"


class _LineChartCanvas(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._series: list[dict] = []
        self._x_axis_label = ""
        self._y_axis_label = ""
        self.setFixedSize(_PLOT_HEIGHT + 2 * _MARGIN, _PLOT_HEIGHT + 2 * _MARGIN)

    def set_series(self, series: list[dict]) -> None:
        self._series = series
        y_scale = max((s["y1"] for s in series), default=1.0) or 1.0
        max_x1 = max((s["x1"] for s in series), default=1.0) or 1.0
        # PATCH 52 — largeur proportionnelle à l'abscisse la plus lointaine
        # (jamais moins que la hauteur, qui reste la référence "carrée").
        plot_w = max(_PLOT_HEIGHT, _PLOT_HEIGHT * (max_x1 / y_scale))
        width = int(_MARGIN * 2 + plot_w + _LABEL_GUTTER)
        height = _PLOT_HEIGHT + 2 * _MARGIN
        self.setFixedSize(width, height)
        self.update()

    def set_axis_labels(self, x_axis_label: str, y_axis_label: str) -> None:
        """PATCH 58 — noms d'axes dessinés directement sur le graphique
        (voir paintEvent), à l'instar du graphique "Delta de budget"."""
        self._x_axis_label = x_axis_label
        self._y_axis_label = y_axis_label
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        h = self.height()
        plot_w = self.width() - 2 * _MARGIN - _LABEL_GUTTER
        plot_h = _PLOT_HEIGHT
        # PATCH 58 — couleur de texte alignée sur le thème (voir le même
        # correctif sur le graphique "Delta de budget").
        default_pen = QPen(self.palette().color(QPalette.WindowText))

        y_scale = max((s["y1"] for s in self._series), default=1.0) or 1.0
        max_x1 = max((s["x1"] for s in self._series), default=1.0) or 1.0

        def to_px(x: float, y: float) -> tuple[int, int]:
            px = _MARGIN + int(x / max_x1 * plot_w)
            py = h - _MARGIN - int(y / y_scale * plot_h)
            return px, py

        # Axes.
        painter.setPen(QPen(QColor("#888888"), 1))
        painter.drawLine(_MARGIN, h - _MARGIN, _MARGIN + plot_w, h - _MARGIN)
        painter.drawLine(_MARGIN, h - _MARGIN, _MARGIN, _MARGIN)

        # PATCH 58 — nom de l'axe Y à la verticale, le long de l'axe des
        # ordonnées (même technique que le graphique "Delta de budget" :
        # translation au centre de l'axe puis rotation de -90°).
        if self._y_axis_label:
            painter.save()
            painter.setPen(default_pen)
            painter.translate(_Y_AXIS_GUTTER, _MARGIN + plot_h / 2)
            painter.rotate(-90)
            painter.drawText(-plot_h / 2, 0, plot_h, 16, Qt.AlignCenter, self._y_axis_label)
            painter.restore()

        # PATCH 58 — nom de l'axe X centré sous le graphique (sous l'axe
        # des abscisses, et non plus aligné à gauche sur toute la
        # largeur du bloc).
        if self._x_axis_label:
            painter.setPen(default_pen)
            painter.drawText(
                _MARGIN, h - _X_AXIS_GUTTER, plot_w, 16, Qt.AlignCenter, self._x_axis_label
            )

        placed_label_rects: list[QRect] = []
        for s in self._series:
            pen = QPen(QColor(s["color"]), 2)
            painter.setPen(pen)
            x0, y0 = to_px(s["x0"], s["y0"])
            x1, y1 = to_px(s["x1"], s["y1"])
            painter.drawLine(x0, y0, x1, y1)
            self._draw_label(painter, x1, y1, s["name"], QColor(s["color"]), placed_label_rects)

        painter.end()

    def _draw_label(
        self, painter: QPainter, x1: int, y1: int, text: str, color: QColor, placed: list[QRect]
    ) -> None:
        """PATCH 52 — étiquette à droite de la fin de la droite (jamais
        au-dessus ni tronquée), décalée verticalement si elle
        chevaucherait une étiquette déjà placée."""
        rect = QRect(x1 + 8, y1 - _LABEL_HEIGHT // 2, _LABEL_WIDTH, _LABEL_HEIGHT)
        moved = True
        while moved:
            moved = False
            for other in placed:
                if rect.intersects(other):
                    rect.moveTop(other.bottom() + 2)
                    moved = True
        placed.append(QRect(rect))
        painter.setPen(QPen(color))
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, text)


class _TitleLikeLineEdit(QLineEdit):
    """Champ éditable façon "titre" (PATCH 52) : pas de préfixe visible,
    texte de substitution quand vide, style discret sans bordure."""

    def __init__(self, text: str, placeholder: str, style: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setPlaceholderText(placeholder)
        self.setFrame(False)
        self.setStyleSheet(style)


class LineChartBlockWidget(QWidget):
    """Widget d'un LineChartBlock : titre, axes, échelle, séries éditables, courbes."""

    def __init__(self, block: LineChartBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        self._title_edit = _TitleLikeLineEdit(block.title, "Titre", _TITLE_STYLE, self)
        self._title_edit.textChanged.connect(self._on_title_changed)
        header.addWidget(self._title_edit, 1)
        # PATCH 58 — nom de l'axe Y déplacé dans l'en-tête, à côté du
        # titre (comme le graphique "Delta de budget") : le champ ici ne
        # sert plus qu'à la saisie, l'affichage réel est désormais
        # dessiné à la verticale sur le graphique (voir _LineChartCanvas).
        self._y_axis_edit = _TitleLikeLineEdit(block.y_axis_label, "Axe Y", _AXIS_STYLE, self)
        self._y_axis_edit.textChanged.connect(self._on_y_axis_changed)
        header.addWidget(self._y_axis_edit, 1)
        header.addWidget(QLabel("Échelle :", self))
        self._x_max_spin = QDoubleSpinBox(self)
        self._x_max_spin.setRange(0.01, 100000)
        self._x_max_spin.setValue(block.x_max)
        self._x_max_spin.valueChanged.connect(self._on_x_max_changed)
        header.addWidget(self._x_max_spin)
        layout.addLayout(header)

        self._canvas = _LineChartCanvas(self)
        layout.addWidget(self._canvas, 0, Qt.AlignLeft)

        # PATCH 58 — nom de l'axe X : champ de saisie centré (pas étiré
        # sur toute la largeur du bloc), l'affichage réel étant lui
        # aussi désormais dessiné centré sous le graphique.
        x_axis_row = QHBoxLayout()
        x_axis_row.addStretch(1)
        self._x_axis_edit = _TitleLikeLineEdit(block.x_axis_label, "Axe X", _AXIS_STYLE, self)
        self._x_axis_edit.setAlignment(Qt.AlignCenter)
        self._x_axis_edit.textChanged.connect(self._on_x_axis_changed)
        x_axis_row.addWidget(self._x_axis_edit)
        x_axis_row.addStretch(1)
        layout.addLayout(x_axis_row)

        self._series_area = QGridLayout()
        layout.addLayout(self._series_area)

        add_button = QPushButton("+ Ajouter une droite", self)
        add_button.clicked.connect(self._on_add_series)
        layout.addWidget(add_button)

        self._rebuild_series_rows()

        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    @property
    def block(self) -> LineChartBlock:
        return self._block

    def _gantt_blocks(self) -> list[DependencyGanttBlock]:
        return [b for b in self._document.blocks if isinstance(b, DependencyGanttBlock)]

    def _rebuild_series_rows(self) -> None:
        while self._series_area.count():
            item = self._series_area.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._syncing = True
        for row_index, s in enumerate(self._block.series):
            name_edit = QLineEdit(s["name"], self)
            name_edit.textChanged.connect(lambda text, sid=s["id"]: self._on_series_name_changed(sid, text))
            self._series_area.addWidget(name_edit, row_index, 0)

            mode_combo = NoScrollComboBox(self)
            mode_combo.addItem("Constante", SLOPE_MODE_CONSTANT)
            mode_combo.addItem("Vélocité réelle (planning)", SLOPE_MODE_EFFICIENCY)
            mode_combo.setCurrentIndex(0 if s["mode"] == SLOPE_MODE_CONSTANT else 1)
            self._series_area.addWidget(mode_combo, row_index, 1)

            slope_spin = QDoubleSpinBox(self)
            slope_spin.setRange(-1000, 1000)
            slope_spin.setSingleStep(0.1)
            slope_spin.setValue(s["slope"])
            slope_spin.setEnabled(s["mode"] == SLOPE_MODE_CONSTANT)
            slope_spin.valueChanged.connect(lambda v, sid=s["id"]: self._on_series_slope_changed(sid, v))
            self._series_area.addWidget(slope_spin, row_index, 2)

            source_combo = NoScrollComboBox(self)
            source_combo.addItem("(aucun planning)", None)
            for gantt in self._gantt_blocks():
                source_combo.addItem(f"Planning {gantt.id[:8]}", gantt.id)
            source_index = source_combo.findData(s.get("source_block_id"))
            source_combo.setCurrentIndex(source_index if source_index >= 0 else 0)
            source_combo.setEnabled(s["mode"] == SLOPE_MODE_EFFICIENCY)
            self._series_area.addWidget(source_combo, row_index, 3)

            mode_combo.currentIndexChanged.connect(
                lambda _, sid=s["id"], mc=mode_combo, sc=source_combo, ss=slope_spin: self._on_series_mode_changed(
                    sid, mc, sc, ss
                )
            )
            source_combo.currentIndexChanged.connect(
                lambda _, sid=s["id"], mc=mode_combo, sc=source_combo: self._on_series_source_changed(sid, mc, sc)
            )

            remove_button = QPushButton("×", self)
            remove_button.clicked.connect(lambda _, sid=s["id"]: self._on_remove_series(sid))
            self._series_area.addWidget(remove_button, row_index, 4)
        self._syncing = False

    # -- Callbacks --------------------------------------------------------

    def _on_title_changed(self, text: str) -> None:
        self._block.title = text

    def _on_x_axis_changed(self, text: str) -> None:
        self._block.x_axis_label = text
        self._canvas.set_axis_labels(self._block.x_axis_label, self._block.y_axis_label)

    def _on_y_axis_changed(self, text: str) -> None:
        self._block.y_axis_label = text
        self._canvas.set_axis_labels(self._block.x_axis_label, self._block.y_axis_label)

    def _on_x_max_changed(self, value: float) -> None:
        self._block.x_max = value
        self.refresh()

    def _on_add_series(self) -> None:
        self._block.add_series(name=f"Droite {len(self._block.series) + 1}")
        self._rebuild_series_rows()
        self.refresh()

    def _on_remove_series(self, series_id: str) -> None:
        self._block.remove_series(series_id)
        self._rebuild_series_rows()
        self.refresh()

    def _on_series_name_changed(self, series_id: str, text: str) -> None:
        if self._syncing:
            return
        self._block.set_series_name(series_id, text)
        self.refresh()

    def _on_series_slope_changed(self, series_id: str, value: float) -> None:
        if self._syncing:
            return
        self._block.set_series_slope(series_id, value)
        self.refresh()

    def _on_series_mode_changed(self, series_id: str, mode_combo, source_combo, slope_spin) -> None:
        if self._syncing:
            return
        mode = mode_combo.currentData()
        slope_spin.setEnabled(mode == SLOPE_MODE_CONSTANT)
        source_combo.setEnabled(mode == SLOPE_MODE_EFFICIENCY)
        self._block.set_series_mode(series_id, mode, source_combo.currentData() if mode == SLOPE_MODE_EFFICIENCY else None)
        self.refresh()

    def _on_series_source_changed(self, series_id: str, mode_combo, source_combo) -> None:
        if self._syncing:
            return
        if mode_combo.currentData() == SLOPE_MODE_EFFICIENCY:
            self._block.set_series_mode(series_id, SLOPE_MODE_EFFICIENCY, source_combo.currentData())
            self.refresh()

    # -- Rafraîchissement -------------------------------------------------

    def refresh(self) -> None:
        self._canvas.set_axis_labels(self._block.x_axis_label, self._block.y_axis_label)
        self._canvas.set_series(compute_line_series(self._document, self._block))
