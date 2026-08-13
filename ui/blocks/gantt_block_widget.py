"""
Widget graphique du bloc Gantt (PATCH 19, PATCH 71 : zoom + défilement).

Le widget ne conserve aucune copie des données du tableau : à chaque
rafraîchissement (changement de sélection, ou minuterie périodique),
il appelle `compute_gantt_rows` qui relit directement le TableBlock
référencé dans le document. Toute modification du tableau (cellule,
ajout/suppression de ligne...) apparaît donc automatiquement, sans
action de synchronisation explicite.

PATCH 71 (remplace PATCH 70, dont le zoom n'avait aucun effet tant que
le canvas était étiré pour remplir la zone visible) :
    - Le canvas a désormais une largeur FIXE, déterminée uniquement par
      le curseur "Échelle" (nombre de jours × pixels/jour à 100 % ×
      zoom). Il n'est plus jamais étiré par la zone de défilement, donc
      bouger le curseur a toujours un effet visible, immédiatement.
    - La zone de défilement (QScrollArea) ne défile qu'à l'horizontale
      (`_LABEL_WIDTH`/axe temporel) ; verticalement le canvas garde
      toujours sa hauteur complète (une ligne par tâche), sans
      découpage ni barre de défilement verticale.
    - Un bouton "Auto" recalcule le zoom nécessaire pour que tout
      l'intervalle de dates tienne exactement dans la largeur visible
      (comportement historique), et resynchronise le curseur. Tant que
      ce mode est actif, il se réajuste automatiquement quand le bloc
      est redimensionné ou que les données changent ; il se désactive
      dès que l'utilisateur bouge le curseur ou les boutons ±
      manuellement.
"""
from __future__ import annotations

import math
from datetime import date

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from blocks.gantt_block import (
    GanttBlock,
    available_date_columns,
    compute_gantt_rows,
    find_source_table,
)
from blocks.table_block import TableBlock
from ui.no_scroll_combo_box import NoScrollComboBox

_REFRESH_INTERVAL_MS = 500
_ROW_HEIGHT = 28
_BAR_COLOR = QColor("#4db6ac")
_LABEL_WIDTH = 140
# PATCH 71 — nombre de pixels par jour à l'échelle 100 %, multiplié par
# le zoom courant pour obtenir la largeur totale du graphique.
_BASE_PX_PER_DAY = 4
_ZOOM_MIN = 10
_ZOOM_MAX = 800
_ZOOM_STEP = 25
_ZOOM_DEFAULT = 100


def _parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class _GanttCanvas(QWidget):
    """Zone de dessin : une ligne par tâche, une barre proportionnelle aux dates.

    PATCH 71 — Sa taille (`_update_geometry`) est désormais FIXE : la
    largeur dépend du nombre de jours à représenter et du zoom courant
    (jamais de la largeur disponible), la hauteur du nombre de lignes.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._span_days = 1
        self._zoom_percent = _ZOOM_DEFAULT
        # PATCH 72 — notifié à chaque changement de taille du canvas,
        # pour que la QScrollArea parente puisse copier sa hauteur
        # (celle-ci ne le fait pas toute seule quand `widgetResizable`
        # est à False, voir GanttBlockWidget._sync_scroll_height).
        self.on_geometry_changed = None
        self._update_geometry()

    @property
    def span_days(self) -> int:
        return self._span_days

    def set_zoom(self, zoom_percent: int) -> None:
        self._zoom_percent = zoom_percent
        self._update_geometry()
        self.update()

    def set_rows(self, rows: list[dict]) -> None:
        self._rows = rows
        dated = [(r, _parse_iso(r["start"]), _parse_iso(r["end"])) for r in rows]
        valid_dates = [d for _, s, e in dated for d in (s, e) if d is not None]
        min_date = min(valid_dates) if valid_dates else None
        max_date = max(valid_dates) if valid_dates else None
        self._span_days = max((max_date - min_date).days, 1) if min_date and max_date else 1
        self._update_geometry()
        self.update()

    def _update_geometry(self) -> None:
        chart_width = int(self._span_days * _BASE_PX_PER_DAY * self._zoom_percent / 100)
        self.setFixedWidth(_LABEL_WIDTH + max(chart_width, 20) + 10)
        self.setFixedHeight(max(_ROW_HEIGHT, _ROW_HEIGHT * len(self._rows)))
        if self.on_geometry_changed is not None:
            self.on_geometry_changed()

    def paintEvent(self, event) -> None:  # noqa: N802 (nom imposé par Qt)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self._rows:
            painter.drawText(self.rect(), Qt.AlignCenter, "Aucune donnée à afficher.")
            painter.end()
            return

        dated = [
            (r, _parse_iso(r["start"]), _parse_iso(r["end"]))
            for r in self._rows
        ]
        valid_dates = [d for _, s, e in dated for d in (s, e) if d is not None]
        min_date = min(valid_dates) if valid_dates else None
        max_date = max(valid_dates) if valid_dates else None
        span_days = max((max_date - min_date).days, 1) if min_date and max_date else 1

        chart_width = max(self.width() - _LABEL_WIDTH - 10, 20)

        for i, (row, start, end) in enumerate(dated):
            y = i * _ROW_HEIGHT
            painter.drawText(0, y, _LABEL_WIDTH, _ROW_HEIGHT, Qt.AlignVCenter, row["label"] or "(sans titre)")

            if start is None:
                continue
            end = end or start
            x_start = _LABEL_WIDTH + int((start - min_date).days / span_days * chart_width)
            x_end = _LABEL_WIDTH + int(max((end - min_date).days, 0) / span_days * chart_width) + 6
            painter.fillRect(x_start, y + 4, max(x_end - x_start, 6), _ROW_HEIGHT - 8, _BAR_COLOR)

        painter.end()


class GanttBlockWidget(QWidget):
    """Widget d'un GanttBlock : sélecteurs de source + zone de dessin."""

    def __init__(self, block: GanttBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
        self._syncing = False
        # PATCH 71 — tant que True, le zoom suit automatiquement la
        # largeur visible (comportement historique "tout voir") ; se
        # désactive dès que l'utilisateur touche au curseur/boutons ±,
        # se réactive via le bouton "Auto".
        self._zoom_auto = True
        self._syncing_zoom = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        selectors = QHBoxLayout()
        selectors.addWidget(QLabel("Tableau :", self))
        self._table_combo = NoScrollComboBox(self)
        self._table_combo.currentIndexChanged.connect(self._on_table_changed)
        selectors.addWidget(self._table_combo, 1)

        selectors.addWidget(QLabel("Libellé :", self))
        self._label_combo = NoScrollComboBox(self)
        self._label_combo.currentIndexChanged.connect(self._on_label_column_changed)
        selectors.addWidget(self._label_combo, 1)

        selectors.addWidget(QLabel("Dates :", self))
        self._date_combo = NoScrollComboBox(self)
        self._date_combo.currentIndexChanged.connect(self._on_date_column_changed)
        selectors.addWidget(self._date_combo, 1)
        layout.addLayout(selectors)

        # PATCH 71 — curseur d'échelle (zoom) : agrandit/réduit le
        # nombre de pixels par jour, plus bouton "Auto" pour ajuster
        # exactement à la largeur visible et resynchroniser le curseur.
        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Échelle :", self))
        zoom_out_button = QToolButton(self)
        zoom_out_button.setText("－")
        zoom_out_button.setAutoRaise(True)
        zoom_out_button.clicked.connect(lambda: self._nudge_zoom(-_ZOOM_STEP))
        zoom_row.addWidget(zoom_out_button)
        self._zoom_slider = QSlider(Qt.Horizontal, self)
        self._zoom_slider.setRange(_ZOOM_MIN, _ZOOM_MAX)
        self._zoom_slider.setSingleStep(_ZOOM_STEP)
        self._zoom_slider.setPageStep(_ZOOM_STEP)
        self._zoom_slider.setValue(_ZOOM_DEFAULT)
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        zoom_row.addWidget(self._zoom_slider)
        zoom_in_button = QToolButton(self)
        zoom_in_button.setText("＋")
        zoom_in_button.setAutoRaise(True)
        zoom_in_button.clicked.connect(lambda: self._nudge_zoom(_ZOOM_STEP))
        zoom_row.addWidget(zoom_in_button)
        self._zoom_label = QLabel(f"{_ZOOM_DEFAULT} %", self)
        self._zoom_label.setFixedWidth(42)
        zoom_row.addWidget(self._zoom_label)
        self._auto_button = QPushButton("Auto", self)
        self._auto_button.setToolTip("Ajuster l'échelle pour tout voir")
        self._auto_button.setFixedWidth(56)
        self._auto_button.clicked.connect(self._enable_auto_zoom)
        zoom_row.addWidget(self._auto_button)
        zoom_row.addStretch(1)
        layout.addLayout(zoom_row)

        self._canvas = _GanttCanvas(self)
        # PATCH 71 — zone de défilement STRICTEMENT horizontale : le
        # canvas garde toujours sa hauteur complète (jamais tronquée
        # verticalement), `widgetResizable=False` pour que sa largeur
        # ne soit jamais étirée par la zone de défilement (sinon le
        # zoom n'a plus d'effet visible).
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(False)
        self._scroll_area.setFrameShape(QScrollArea.NoFrame)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setWidget(self._canvas)
        layout.addWidget(self._scroll_area)
        # PATCH 72 — `widgetResizable=False` ne fait pas suivre à la
        # QScrollArea la hauteur de son contenu toute seule : sans ce
        # câblage elle gardait sa hauteur par défaut (~192 px), ce qui
        # tronquait le graphique et affichait un ascenseur vertical dès
        # qu'il y avait beaucoup de tâches. On force sa hauteur à
        # toujours correspondre exactement à celle du canvas.
        self._canvas.on_geometry_changed = self._sync_scroll_height
        self._sync_scroll_height()

        self._populate_table_combo()

        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    @property
    def block(self) -> GanttBlock:
        return self._block

    # -- Sélection de la source -----------------------------------------

    def _table_blocks(self) -> list[TableBlock]:
        return [b for b in self._document.blocks if isinstance(b, TableBlock)]

    def _populate_table_combo(self) -> None:
        self._syncing = True
        self._table_combo.clear()
        self._table_combo.addItem("(aucun)", None)
        for table in self._table_blocks():
            title = f"Tableau ({table.columns[0]['name']}...)" if table.columns else "Tableau"
            self._table_combo.addItem(title, table.id)
        index = self._table_combo.findData(self._block.table_block_id)
        self._table_combo.setCurrentIndex(index if index >= 0 else 0)
        self._syncing = False
        self._populate_column_combos()

    def _populate_column_combos(self) -> None:
        self._syncing = True
        self._label_combo.clear()
        self._date_combo.clear()

        table = find_source_table(self._document, self._block)
        if table is not None:
            for column in table.columns:
                self._label_combo.addItem(column["name"] or "(sans nom)", column["id"])
            for column in available_date_columns(table):
                self._date_combo.addItem(column["name"] or "(sans nom)", column["id"])

        label_index = self._label_combo.findData(self._block.label_column_id)
        self._label_combo.setCurrentIndex(label_index if label_index >= 0 else 0)
        date_index = self._date_combo.findData(self._block.date_column_id)
        self._date_combo.setCurrentIndex(date_index if date_index >= 0 else 0)
        self._syncing = False

    def _on_table_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(self._table_combo.currentData(), None, None)
        self._populate_column_combos()
        self.refresh()

    def _on_label_column_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(
            self._block.table_block_id, self._label_combo.currentData(), self._block.date_column_id
        )
        self.refresh()

    def _on_date_column_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(
            self._block.table_block_id, self._block.label_column_id, self._date_combo.currentData()
        )
        self.refresh()

    # -- Zoom (PATCH 71) --------------------------------------------------

    def _nudge_zoom(self, delta: int) -> None:
        self._zoom_slider.setValue(self._zoom_slider.value() + delta)

    def _on_zoom_changed(self, value: int) -> None:
        self._zoom_label.setText(f"{value} %")
        self._canvas.set_zoom(value)
        if not self._syncing_zoom:
            # Ajustement manuel (curseur ou boutons ±) : on quitte le
            # mode "Auto" jusqu'à ce que l'utilisateur y revienne.
            self._zoom_auto = False

    def _enable_auto_zoom(self) -> None:
        self._zoom_auto = True
        self._sync_auto_zoom()

    def _sync_auto_zoom(self) -> None:
        """Calcule le zoom nécessaire pour que tout l'intervalle de
        dates tienne dans la largeur visible, et resynchronise le
        curseur (sans repasser en mode manuel, voir `_syncing_zoom`)."""
        if not self._zoom_auto:
            return
        viewport_width = self._scroll_area.viewport().width()
        available = max(viewport_width - _LABEL_WIDTH - 10, 20)
        span_days = max(self._canvas.span_days, 1)
        ideal = available / (span_days * _BASE_PX_PER_DAY) * 100
        target = max(_ZOOM_MIN, min(_ZOOM_MAX, math.floor(ideal)))
        self._syncing_zoom = True
        self._zoom_slider.setValue(target)
        self._syncing_zoom = False
        # setValue() n'émet pas valueChanged si la valeur ne change pas
        # (ex. redimensionnement négligeable) : on force quand même la
        # mise à jour du canvas pour rester exact.
        self._zoom_label.setText(f"{target} %")
        self._canvas.set_zoom(target)

    def _sync_scroll_height(self) -> None:
        """PATCH 73 — Aligne la hauteur de la zone de défilement sur
        celle du canvas (voir le commentaire au niveau de sa création),
        pour qu'elle prenne toujours toute la place verticale
        nécessaire, sans jamais tronquer ni faire défiler le contenu.
        La réserve pour la barre horizontale est lue via une métrique
        de style (PM_ScrollBarExtent, toujours disponible et non
        nulle) plutôt que `QScrollBar.sizeHint()`, qui peut renvoyer 0
        sur certains styles tant que la barre n'a encore jamais été
        affichée — ce qui, PATCH 72, ne lui laissait alors plus aucune
        place et la faisait purement disparaître, même quand le canvas
        dépassait bien la largeur visible."""
        reserve = self.style().pixelMetric(QStyle.PM_ScrollBarExtent) + 2
        self._scroll_area.setFixedHeight(self._canvas.height() + reserve)

    def resizeEvent(self, event) -> None:  # noqa: N802 (nom imposé par Qt)
        super().resizeEvent(event)
        # PATCH 71 — différé au prochain passage de la boucle
        # d'événements : au moment où `resizeEvent` se déclenche, la
        # zone de défilement n'a pas toujours encore sa géométrie
        # finale (ex. juste après `show()`), un calcul immédiat
        # utiliserait alors une largeur de secours trop petite.
        QTimer.singleShot(0, self._sync_auto_zoom)

    def showEvent(self, event) -> None:  # noqa: N802 (nom imposé par Qt)
        super().showEvent(event)
        QTimer.singleShot(0, self._sync_auto_zoom)

    # -- Rafraîchissement -------------------------------------------------

    def refresh(self) -> None:
        """Relit le tableau source et redessine (PATCH 19 : aucune donnée
        propre au Gantt, tout est recalculé à partir du document)."""
        rows = compute_gantt_rows(self._document, self._block)
        self._canvas.set_rows(rows)
        QTimer.singleShot(0, self._sync_auto_zoom)
