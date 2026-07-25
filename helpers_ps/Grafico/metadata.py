from __future__ import annotations

import io
import locale
import warnings
from dataclasses import dataclass, field
from importlib.resources import files

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MultipleLocator

try:
    from helpers_ps.Config.var_globs import PALETA_COLORES
except Exception:
    PALETA_COLORES = [
        "#2F71E5", "#00A6A6", "#F28E2B", "#E15759", "#76B7B2",
        "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F"
    ]

class Graph_meta_data():
    """
    Store and manage figure, axis, dataframe, and per-subplot metadata.

    Notes
    -----
    This docstring was added during the modular refactor to make the API easier
    to understand for new users and maintainers.
    """

    # Información pasable como el data frame
    dataframe: pd.DataFrame | list[pd.DataFrame] = None
    _fig = None,                            # Figura
    _meta_data: dict = None                 # Donde se almacena la metadata
    _axes: list = None                      # lista de ejes
    _axes_shape: tuple[int, int] = None     # Forma de la estructura de gráficos

    # Detalles del grafico activo
    _ax_idx = None                  # Numero de eje activo
    _df_idx = None                  # Numero de dataframe activo
    _ax = None                      # Eje activo en la clase
    _df = None                      # Dataframe activo de la clase
    
    # Meta data alamacenada
    _ticker_label_color: list[tuple[str, str, str]] = None
    _x_axis_fechas = None
    _x_axis_mode = None
    _x_vals = None
    _months = None
    _years = None

    # Meta data de barras
    _bar_mode = None
    _bar_stacked = None
    _bar_grouped = None
    _bar_rects = None

    # Meta data de leyenda
    _custom_legend_handles: list = None

    def __post_init__(self):
        """
        Normalize constructor inputs after dataclass initialization.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        self.dataframe = [self.dataframe] if isinstance(self.dataframe, pd.DataFrame) else self.dataframe

    # funcion para poder actualizar el metadata hacia _meta_data
    def _set_axis(self, ax_index: int = 0) -> None:
        """
        Select the active Matplotlib axis and persist metadata for the previous axis.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not hasattr(self, "_axes") or self._axes is None:
            raise RuntimeError("Axes not initialized. Call plot() first.")

        if ax_index >= len(self._axes):
            raise IndexError("Axis index out of range.")
        
        if self._ax_idx == ax_index:
            raise ValueError(f"El subplot {ax_index} ya se encuenta seleccionado")

        # -------------------------------------------------
        # 1. Guardar metadata del eje actual
        # -------------------------------------------------
        current_idx = self._ax_idx

        self._meta_data[current_idx] = {
            "dataframe": self._df_idx,
            "xmeta": {
                "mode": self._x_axis_mode, 
                "fechas": self._x_axis_fechas,
                "x_vals": self._x_vals
            },
            "bar_mode": self._bar_mode,
            "bar_stacked": self._bar_stacked,
            "bar_grouped": self._bar_grouped,
            "bar_rects": self._bar_rects,
            "months": self._months,
            "years": self._years,
            "ticker_label_color": self._ticker_label_color,
            "custom_legend_handles": list(self._custom_legend_handles) if self._custom_legend_handles is not None else []
        }

        # Guardar el axis actual dentro de la lista
        self._axes[current_idx] = self._ax

        # -------------------------------------------------
        # 2. Cargar metadata del nuevo eje
        # -------------------------------------------------
        target_meta = self._meta_data[ax_index]

        self._df_idx = target_meta["dataframe"]

        if self._df_idx is not None:
            self._df = self.dataframe[self._df_idx]
        else:
            self._df = None

        self._x_axis_fechas = target_meta["xmeta"]["fechas"]
        self._x_axis_mode = target_meta["xmeta"]["mode"]
        self._x_vals = target_meta["xmeta"]["x_vals"]

        self._months = target_meta["months"]
        self._years = target_meta["years"]

        self._bar_mode = target_meta["bar_mode"]
        self._bar_stacked = target_meta["bar_stacked"]
        self._bar_grouped = target_meta["bar_grouped"]
        self._bar_rects = target_meta["bar_rects"]

        self._ticker_label_color = target_meta["ticker_label_color"]

        self._custom_legend_handles = list(
            target_meta.get("custom_legend_handles", [])
        )

        # -------------------------------------------------
        # 3. Activar nuevo eje
        # -------------------------------------------------
        self._ax_idx = ax_index
        self._ax = self._axes[ax_index]

        return None

    def _select_df(self, df_idx=0):
        """
        Select and store the active dataframe from the dataframe collection.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        self._df_idx = df_idx
        self._df = self.dataframe[df_idx]
        return self._df

    def _generate_metadata(
        self,
        fig,
        axes,
        nrows,
        ncols,
    ):
        # -------------------------------------------------
        # 2. Guardar figura
        # -------------------------------------------------
        """
        Initialize figure, axes, and per-axis metadata after creating a plot canvas.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        self._fig = fig

        # -------------------------------------------------
        # 3. Manejo de estructura de axes
        # -------------------------------------------------
        if isinstance(axes, np.ndarray):
            self._axes = axes.flatten().tolist()
            self._ax = self._axes[0]
        else:
            self._axes = [axes]
            self._ax = axes

        # -------------------------------------------------
        # 4. Manejo de metadata
        # -------------------------------------------------
        self._ax_idx = 0
        self._axes_shape = (nrows, ncols)

        self._meta_data = {
            i: {
                "dataframe": None,
                "xmeta": {
                    "mode": None,
                    "fechas": None,
                    "x_vals": None
                },
                "bar_mode": None,
                "bar_stacked": None,
                "bar_grouped": None,
                "bar_rects": None,
                "months": None,
                "years": None,
                "ticker_label_color": None,
                "custom_legend_handles": []
            }
            for i, ax in enumerate(self._axes)
        }

        # Metadata activa del primer eje
        self._custom_legend_handles = []

