from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ._colors import PALETA_COLORES


# ---------------------------------------------------------------------------
# AxisState
# ---------------------------------------------------------------------------
#
# All metadata that used to live "flattened" on the instance (self._bar_mode,
# self._x_axis_mode, self._pie_data, ...) now lives inside a single
# AxisState per subplot axis. Switching the active axis becomes swapping one
# reference (self._state) instead of copying every field in and out of a
# plain dict by hand.
#
# Adding a new piece of per-axis metadata now only requires adding ONE field
# here. Previously it required updating the class attribute list, the
# _generate_metadata() dict defaults, and both the "save" and "load" halves
# of _set_axis() -- four places kept in sync by hand. Two kinds of fields
# (`series_config`, and pie chart data) had already drifted out of sync
# with that old pattern; see the CHANGES note at the bottom of this file.
@dataclass
class AxisState:
    # DataFrame activo para este eje
    dataframe_idx: int | None = None
    dataframe: pd.DataFrame | None = None

    # Metadata del eje x
    x_axis_mode: str | None = None
    x_axis_fechas: object = None
    x_axis_metadata: dict | None = None
    x_vals: object = None
    months: object = None
    years: object = None

    # Metadata de barras
    bar_mode: str | None = None
    bar_stacked: bool | None = None
    bar_grouped: bool | None = None
    bar_rects: object = None
    bars_data: dict = field(default_factory=dict)
    bars_stacked: object = None
    bars_x_reference: list = field(default_factory=list)

    # Metadata de pie charts
    # NOTA: en el código original `graph_pie` nunca poblaba `self._pie_data`,
    # así que `tags_pie.py` siempre fallaba con
    # "No existe self._pie_data. Ejecuta graph_pie...". Se deja aquí
    # correctamente inicializado y listo para usarse; `graph_pie` debe
    # asignar `self._pie_data = {...}` para que los tags de pie funcionen.
    pie_data: dict = field(default_factory=dict)

    # Series / tickers
    ticker_label_color: list = field(default_factory=list)
    series_config: list = field(default_factory=list)

    # Leyenda
    custom_legend_handles: list = field(default_factory=list)

    # Eje y secundario
    right_ax: object = None
    axis_map: dict | None = None
    right_axis_enabled: bool = False
    right_axis_config: dict | None = None
    y_axis_right: dict | None = None


# Atributos "planos" que el resto del código (base.py, charts.py, tags_*.py)
# sigue leyendo/escribiendo como self._bar_mode, self._x_vals, etc. Cada uno
# de estos se redirige de forma transparente hacia self._state.<campo sin
# guion bajo>. Esto evita tener que tocar cientos de call-sites fuera de
# este archivo mientras se migra el manejo de metadata.
_STATE_ATTRS = {
    "_df_idx": "dataframe_idx",
    "_df": "dataframe",
    "_x_axis_mode": "x_axis_mode",
    "_x_axis_fechas": "x_axis_fechas",
    "_x_axis_metadata": "x_axis_metadata",
    "_x_vals": "x_vals",
    "_months": "months",
    "_years": "years",
    "_bar_mode": "bar_mode",
    "_bar_stacked": "bar_stacked",
    "_bar_grouped": "bar_grouped",
    "_bar_rects": "bar_rects",
    "_bars_data": "bars_data",
    "_bars_stacked": "bars_stacked",
    "_bars_x_reference": "bars_x_reference",
    "_pie_data": "pie_data",
    "_ticker_label_color": "ticker_label_color",
    "_series_config": "series_config",
    "_custom_legend_handles": "custom_legend_handles",
    "_right_ax": "right_ax",
    "_axis_map": "axis_map",
    "_right_axis_enabled": "right_axis_enabled",
    "_right_axis_config": "right_axis_config",
    "_y_axis_right": "y_axis_right",
}


class Graph_meta_data:
    """
    Store and manage figure, axis, dataframe, and per-subplot metadata.

    Per-axis metadata is stored in a list of `AxisState` instances
    (`self._states`), one per subplot. `self._state` always points at the
    `AxisState` of the currently active axis. Switching axes
    (`_set_axis`) simply repoints `self._state`; it does not copy fields.

    Backwards compatibility
    ------------------------
    Existing code (in this package and possibly downstream) reads and
    writes per-axis metadata as flat attributes, e.g. `self._bar_stacked`,
    `self._x_vals`, `self._pie_data`. Those names keep working unchanged:
    `__getattr__`/`__setattr__` transparently redirect them to
    `self._state.<field>`. New code can use `self._state.bar_stacked`
    directly if preferred.
    """

    # Información pasable como el data frame
    dataframe: pd.DataFrame | list[pd.DataFrame] = None

    _fig = None
    _axes: list = None
    _axes_shape: tuple[int, int] = None

    _ax_idx = None
    _ax = None
    _states: list = None
    _state: "AxisState | None" = None

    def __post_init__(self):
        """
        Normalize constructor inputs after dataclass initialization.
        """
        self.dataframe = [self.dataframe] if isinstance(self.dataframe, pd.DataFrame) else self.dataframe

    # -----------------------------------------------------------------
    # Delegación transparente de atributos "planos" hacia self._state
    # -----------------------------------------------------------------
    def __getattr__(self, name):
        # __getattr__ solo se llama cuando el atributo NO se encontró de la
        # forma normal (instancia / clase), así que es seguro interceptar
        # aquí sin riesgo de recursión sobre atributos reales.
        field_name = _STATE_ATTRS.get(name)
        if field_name is not None:
            state = self.__dict__.get("_state")
            if state is None:
                raise AttributeError(
                    f"{name!r} no está disponible todavía. "
                    "Llama a plot() / _generate_metadata() primero."
                )
            return getattr(state, field_name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        field_name = _STATE_ATTRS.get(name)
        if field_name is not None:
            state = self.__dict__.get("_state")
            if state is None:
                # Fail loudly instead of silently creating a shadow instance
                # attribute that would permanently break delegation for this
                # field. This mirrors the old behavior where writing
                # per-axis metadata before plot()/_generate_metadata() had
                # been called made no sense either.
                raise AttributeError(
                    f"No se puede asignar {name!r} todavía: no hay un eje "
                    "activo. Llama a plot() / _generate_metadata() primero."
                )
            setattr(state, field_name, value)
            return
        object.__setattr__(self, name, value)

    # -----------------------------------------------------------------
    # Selección de eje activo
    # -----------------------------------------------------------------
    def _set_axis(self, ax_index: int = 0) -> None:
        """
        Select the active Matplotlib axis.

        Persisting the previous axis's metadata and loading the new axis's
        metadata is now a single reference swap (`self._state = ...`)
        instead of copying every field by hand.
        """
        if not self._states:
            raise RuntimeError("Axes not initialized. Call plot() first.")

        if ax_index >= len(self._axes):
            raise IndexError("Axis index out of range.")

        if self._ax_idx == ax_index:
            raise ValueError(f"El subplot {ax_index} ya se encuenta seleccionado")

        # Guardar el axis de matplotlib actual dentro de la lista
        self._axes[self._ax_idx] = self._ax

        # Activar nuevo eje + su AxisState
        self._ax_idx = ax_index
        self._ax = self._axes[ax_index]
        self._state = self._states[ax_index]

        return None

    def _select_df(self, df_idx=0):
        """
        Select and store the active dataframe from the dataframe collection.

        Notes
        -----
        `graph_line`/`graph_bar`/`graph_pie`/`graph_box_whiskers` all call
        this *before* `plot()` creates the figure/axes on the very first
        call (`plot()` only runs afterwards, and only if no axis exists
        yet). At that point `self._state` doesn't exist yet, so a
        placeholder `AxisState` is created here to hold the selection.
        `_generate_metadata()` adopts this placeholder as axis 0's state
        once `plot()` actually runs, instead of discarding it.
        """
        if self._state is None:
            self._state = AxisState()

        self._state.dataframe_idx = df_idx
        self._state.dataframe = self.dataframe[df_idx]
        return self._state.dataframe

    def _generate_metadata(
        self,
        fig,
        axes,
        nrows,
        ncols,
    ):
        """
        Initialize figure, axes, and one AxisState per axis after creating a
        plot canvas.

        If `_select_df()` already created a placeholder `AxisState` (see its
        docstring) before this ran, that state is kept as axis 0's state so
        the dataframe selection made just before `plot()` isn't lost.
        """
        # `self._states` is only falsy here on a fresh instance (or right
        # after reset). If a dataframe was pre-selected via `_select_df()`,
        # `self._state` will hold that placeholder; adopt it for axis 0.
        pending_state = self._state if not self._states else None

        self._fig = fig

        if isinstance(axes, np.ndarray):
            self._axes = axes.flatten().tolist()
            self._ax = self._axes[0]
        else:
            self._axes = [axes]
            self._ax = axes

        self._ax_idx = 0
        self._axes_shape = (nrows, ncols)

        self._states = [
            pending_state if i == 0 and pending_state is not None else AxisState()
            for i in range(len(self._axes))
        ]
        self._state = self._states[0]


# ---------------------------------------------------------------------------
# CHANGES (refactor notes)
# ---------------------------------------------------------------------------
# 1. `_series_config` was read/written on self but was missing from the old
#    per-axis dict's defaults in `_generate_metadata` (only recovered via
#    `.get("series_config", [])` in `_set_axis`). It is now a first-class
#    `AxisState.series_config` field, always initialized.
# 2. `_bars_data`, `_bars_stacked`, `_bars_x_reference`, and
#    `_x_axis_metadata` were being set on `self` in `charts.py`/`base.py`
#    but were NEVER saved or restored by the old `_set_axis` -- meaning bar
#    chart state silently leaked or went stale across subplot axes. They
#    now live in `AxisState` and are correctly swapped per axis.
# 3. `_pie_data` is referenced throughout `tags_pie.py` but was never
#    assigned anywhere in `graph_pie` (charts.py). It's now a proper
#    `AxisState.pie_data` field so pie tag/label helpers will work as soon
#    as `graph_pie` is updated to populate it (currently pie tags/labels
#    raise "No existe self._pie_data..." -- this is a pre-existing bug,
#    unrelated to this refactor, that's now easy to fix in one place).
