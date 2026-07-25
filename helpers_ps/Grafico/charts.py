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

from .base import Graph_base
from .tags_line import Line_tags
from .tags_bar import Bar_tags
from .tags_pie import Pie_tags
from .tags_box import BoxW_tags

@dataclass
class Graph_mtplt(Graph_base, Line_tags, Bar_tags, Pie_tags, BoxW_tags):
    """
    Main public chart builder that combines base plotting utilities and chart-specific methods.

    Notes
    -----
    This docstring was added during the modular refactor to make the API easier
    to understand for new users and maintainers.
    """
    def __init__(self, dataframe: pd.DataFrame | list[pd.DataFrame] | None = None):
        """
        Initialize the graph object with one dataframe or a list of dataframes.

        Parameters
        ----------
        dataframe:
            DataFrame or list of DataFrames used by the chart methods.
        """
        self.dataframe = [dataframe] if isinstance(dataframe, pd.DataFrame) else dataframe

        # Figure and axis state
        self._fig = None
        self._meta_data = None
        self._axes = None
        self._axes_shape = None

        # Active graph state
        self._ax_idx = None
        self._df_idx = None
        self._ax = None
        self._df = None

        # X-axis metadata
        self._ticker_label_color = None
        self._x_axis_fechas = None
        self._x_axis_mode = None
        self._x_vals = None
        self._months = None
        self._years = None

        # Bar metadata
        self._bar_mode = None
        self._bar_stacked = None
        self._bar_grouped = None
        self._bar_rects = None

        # Legend metadata
        self._custom_legend_handles = []

    def graph_line(
        self,
        # --- Configuración del grafico
        figsize: tuple[float, float] = (6.00, 5.00),                        # Tamaño del grafico configuración general es (6,4.8) --> tamaño estandard
        # --- Configuración de los elementos adicionales del grafico
        titles: dict | None = None,                                         # titulo de la grafica
        source: dict | None = None,                                         # Fuente de datos del grafico
        # --- Configuración de df
        df_index: int = 0,                                                  # índice del dataframe a usar (en caso de tener varios)
        # --- Configuración de las series
        tickers: list[str] | str = "all",                                   # tickers en evaluación del dataframe
        labels: list[str] | str | None = None,                              # etiquetas de los tickers en el orden dado, sino defaultea a los tickers
        colors: list["str"] | str = PALETA_COLORES,                         # Lista de colors para cada uno de los tickers en evaluación
        lw: float=1.6,                                                      # grosor de línea
        # --- Configuración de etiquetas en la linea
        tag_dot: dict = None,
        # --- Configuración del eje y
        y_axis: dict = None,
        # --- Configuración del eje x
        x_axis: dict = None,
        # --- Configuración Leyenda
        legend: dict | None = None,                                    # None = auto (solo si hay >1 serie y labels)
        # --- Configuración lineas horizontales
        hlines: dict | None = None,                           # agregar lineas horizontales en el grafico
        # --- Mostrar guias horizontales
        show_hguide: bool = False
        ) -> None:
        """
        Create an institutional line chart from dataframe columns and optional annotations.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        # --- 1. Importación y setteo del dataframe 
        db = self._select_df(df_idx=df_index)
        
        # --- 3. Normalización de los tickers
        if isinstance(tickers, str):
            if tickers == "all":
                tickers = db.columns.tolist()
            else:
                tickers = [tickers]

        # 

        # --- 4. Asignación de etiquetas
        if isinstance(labels, str):
            labels = [labels]
        elif isinstance(labels, list):
            if len(labels) < len(db.columns.tolist()):
                add = db.columns.tolist()
                add = add[len(labels):]
                labels = labels + add
        else:
            labels = db.columns.tolist()
        
        # --- 4. Normalización de los colores
        if isinstance(colors, str):
            colors = [colors]
        elif isinstance(colors, list):
            if len(colors) < len(db.columns.tolist()):
                add = PALETA_COLORES
                add = add[len(colors):]
                colors = colors + add
        else:
            colors = PALETA_COLORES
        
        # --- 5. Asignación de ticker label color
        self._ticker_label_color = [(tickers[i], labels[i], colors[i]) for i,t in enumerate(tickers)]

        # --- 6. revision de dicts
        x_axis = x_axis if x_axis is not None else dict()
        y_axis = y_axis if y_axis is not None else dict()
        titles = titles if titles is not None else dict()
        y_axis = y_axis if y_axis is not None else dict()
        legend = legend if legend is not None else dict()
        legend = legend if legend is not None else dict()
        hlines = hlines if hlines is not None else dict()
        source = source if source is not None else dict()

        # --- 7. Generación del gráfico y el plot en caso no exista
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        # --- 8. Agregar titulos globales
        self.set_titles(**titles)
        self.add_source(**source)

        # --- 9. Manejo del eje x
        db = self.prep_x_axis(dataframe=db, **x_axis)

        # --- 10 Graficar las lineas
        for i, t in enumerate(tickers):
            s = db[[t]].copy()

            if s.empty:
                continue

            lab = labels[i] if labels is not None and i < len(labels) else None
            col = colors[i] if colors is not None and i < len(colors) else "#2F71E5"

            if self._x_axis_mode == "bbg":
                # Alinear series al calendario común
                serie = s.reindex(self._x_axis_fechas)[t]

                self._ax.plot(self._x_vals, serie.to_numpy(), color=col, lw=lw, label=lab)

            else:
                self._ax.plot(s.index, s[t], color=col, lw=lw, label=lab)
        

        # --- 11 Graficar ultimo valores
        self._line_label_generate(tag_dot)

        # --- 12. Configuración del eje y
        self.prep_y_axis(**y_axis)

        # -- 13. Agregar lineas horizontales
        self.horizontal_lines(**hlines)
        
        # -- 14. Agregar guias horizontales
        if show_hguide:
            self.guias_horizontales(mostrar_cero=False)
            

        # --- 15. Agregar leyenda
        self.add_legend(**legend)

    def graph_bar(
            self,
            # --- Configuración del grafico
            figsize: tuple[float, float] = (6.00, 5.00),

            # --- Configuración de los elementos adicionales del grafico
            titles: dict | None = None,
            source: dict | None = None,

            # --- Configuración de df
            df_index: int = 0,

            # --- Configuración de las series
            tickers: list[str] | str = "all",
            labels: list[str] | str | None = None,
            colors: list[str] | str = PALETA_COLORES,

            # --- Configuración del eje x / y
            x_axis: dict | None = None,
            y_axis: dict | None = None,

            # --- Configuración de barras
            bar_mode: str = "auto",       # "auto" | "time" | "last"
            stacked: bool = False,
            grouped: bool = False,
            bar_width: float = 0.8,
            alpha: float = 0.95,

            # --- Etiquetas de valores
            bar_labels: dict | None = None,

            # --- Configuración Leyenda
            legend: dict | None = None,

            # --- Configuración lineas horizontales
            hlines: dict | None = None,

            # --- Mostrar guias horizontales
            show_hguide: bool = False
        ) -> None:
            """
            Create an institutional bar chart supporting grouped, stacked, and custom formats.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """

            # --- 1. Importación y setteo del dataframe
            db = self._select_df(df_idx=df_index)

            # --- 2. Normalización de los tickers
            if isinstance(tickers, str):
                if tickers == "all":
                    tickers = db.columns.tolist()
                else:
                    tickers = [tickers]

            tickers = [t for t in tickers if t in db.columns]
            if len(tickers) == 0:
                raise ValueError("No hay tickers válidos para graficar.")
            
            db = db[tickers].copy()  # filtrar solo los tickers seleccionados

            # --- 3. Asignación de etiquetas
            if isinstance(labels, str):
                labels = [labels]
            elif isinstance(labels, list):
                if len(labels) < len(tickers):
                    labels = labels + tickers[len(labels):]
            else:
                labels = tickers.copy()

            # --- 4. Normalización de los colores
            if isinstance(colors, str):
                colors = [colors]
            elif isinstance(colors, list):
                if len(colors) < len(tickers):
                    add = PALETA_COLORES.copy()
                    colors = colors + add[:max(0, len(tickers) - len(colors))]
            else:
                colors = PALETA_COLORES.copy()

            colors = [
                colors[i] if i < len(colors) else PALETA_COLORES[i % len(PALETA_COLORES)]
                for i in range(len(tickers))
            ]

            # --- 5. Asignación de ticker label color
            self._ticker_label_color = [(tickers[i], labels[i], colors[i]) for i in range(len(tickers))]

            # --- 6. Revisión de dicts
            x_axis = x_axis if x_axis is not None else dict()
            y_axis = y_axis if y_axis is not None else dict()
            titles = titles if titles is not None else dict()
            source = source if source is not None else dict()
            legend = legend if legend is not None else dict()
            hlines = hlines if hlines is not None else dict()
            bar_labels = bar_labels if bar_labels is not None else dict()


            # --- 7. Generación del gráfico y el plot en caso no exista
            if not hasattr(self, "_ax") or self._ax is None:
                self.plot(figsize=figsize)

            # --- 8. Definición automática del modo
            if bar_mode == "auto":
                if len(tickers) == 1:
                    bar_mode = "time"
                else:
                    bar_mode = "time" if (grouped or stacked) else "last"

            self._bar_mode = bar_mode

            # --- 9. Agregar títulos globales
            self.set_titles(**titles)
            self.add_source(**source)

            bars_data = {}

            # ==========================================================
            # MODE: TIME
            # ==========================================================
            if bar_mode == "time":
                # preparar eje x usando helper base (igual lógica que graph_line)
                db = self.prep_x_axis(dataframe=db, **x_axis)
                
                if self._x_axis_mode == "bbg":
                    self._bars_x_reference = list(self._x_axis_fechas)
                else:
                    self._bars_x_reference = list(db.index)


                m = len(tickers)

                # --- A. Un ticker
                if m == 1:
                    t = tickers[0]
                    s = db[[t]].copy()

                    if self._x_axis_mode == "bbg":
                        serie = s.reindex(self._x_axis_fechas)[t]
                        bars = self._ax.bar(
                            self._x_vals,
                            serie.to_numpy(),
                            width=min(bar_width, 0.85),
                            color=colors[0],
                            alpha=alpha,
                            label=labels[0],
                            zorder=3
                        )
                    else:
                        bars = self._ax.bar(
                            s.index,
                            s[t],
                            width=min(bar_width, 0.85),
                            color=colors[0],
                            alpha=alpha,
                            label=labels[0],
                            zorder=3
                        )
                    
                    bars_data[t] = {
                        "bars": bars
                    }

                # --- B. Multiples tickers
                else:
                    # -------- grouped --------
                    if grouped and not stacked:
                        if self._x_axis_mode == "bbg":
                            base_x = self._x_vals.astype(float)
                            width = min(bar_width / m, 0.8 / m)

                            for i, t in enumerate(tickers):
                                serie = db[[t]].copy().reindex(self._x_axis_fechas)[t]
                                offset = (i - (m - 1) / 2) * width

                                bars = self._ax.bar(
                                    base_x + offset,
                                    serie.to_numpy(),
                                    width=width,
                                    color=colors[i],
                                    alpha=alpha,
                                    label=labels[i],
                                    zorder=3
                                )

                                bars_data[t] = {
                                    "bars": bars
                                }

                        else:
                            x_index = db.index
                            is_datetime = pd.api.types.is_datetime64_any_dtype(x_index)
                            is_numeric = pd.api.types.is_numeric_dtype(x_index)

                            if is_datetime:
                                x_num = mdates.date2num(pd.to_datetime(x_index).to_pydatetime())
                                diffs = np.diff(np.sort(np.unique(x_num)))
                                base_step = np.median(diffs) if len(diffs) else 30.0
                                group_total = base_step * 0.8
                                width = group_total / m

                                for i, t in enumerate(tickers):
                                    offset = (i - (m - 1) / 2) * width
                                    bars = self._ax.bar(
                                        x_num + offset,
                                        np.asarray(db[t].values, dtype=float),
                                        width=width,
                                        color=colors[i],
                                        alpha=alpha,
                                        label=labels[i],
                                        zorder=3
                                    )

                                    bars_data[t] = {
                                        "bars": bars
                                    }

                                self._ax.xaxis_date()

                            elif is_numeric:
                                x_num = np.asarray(x_index.values, dtype=float)
                                diffs = np.diff(np.sort(np.unique(x_num)))
                                base_step = np.median(diffs) if len(diffs) else 1.0
                                group_total = base_step * 0.8
                                width = group_total / m

                                for i, t in enumerate(tickers):
                                    offset = (i - (m - 1) / 2) * width
                                    bars = self._ax.bar(
                                        x_num + offset,
                                        np.asarray(db[t].values, dtype=float),
                                        width=width,
                                        color=colors[i],
                                        alpha=alpha,
                                        label=labels[i],
                                        zorder=3
                                    )

                                    bars_data[t] = {
                                        "bars": bars
                                    }

                            else:
                                # categórico en modo time
                                x = np.arange(len(db.index), dtype=float)
                                width = min(bar_width / m, 0.8 / m)

                                for i, t in enumerate(tickers):
                                    offset = (i - (m - 1) / 2) * width
                                    bars = self._ax.bar(
                                        x + offset,
                                        np.asarray(db[t].values, dtype=float),
                                        width=width,
                                        color=colors[i],
                                        alpha=alpha,
                                        label=labels[i],
                                        zorder=3
                                    )

                                    bars_data[t] = {
                                        "bars": bars
                                    }

                                self._ax.set_xticks(x)
                                _x_font = x_axis.get("fontsize", 8)
                                self._ax.set_xticklabels([str(v) for v in db.index], fontsize=_x_font)

                    # -------- stacked --------
                    else:
                        if self._x_axis_mode == "bbg":
                            bottom_pos = np.zeros(len(self._x_vals), dtype=float)
                            bottom_neg = np.zeros(len(self._x_vals), dtype=float)

                            for i, t in enumerate(tickers):
                                serie = db[[t]].copy().reindex(self._x_axis_fechas)[t]
                                y = np.asarray(serie.values, dtype=float)

                                y_pos = np.where(np.isnan(y), 0.0, np.where(y > 0, y, 0.0))
                                y_neg = np.where(np.isnan(y), 0.0, np.where(y < 0, y, 0.0))

                                bars_pos = None
                                bars_neg = None

                                if np.any(y_pos != 0):
                                    bars_pos = self._ax.bar(
                                        self._x_vals,
                                        y_pos,
                                        width=min(bar_width, 0.85),
                                        bottom=bottom_pos,
                                        color=colors[i],
                                        alpha=alpha,
                                        label=labels[i],
                                        zorder=3
                                    )
                                    bottom_pos = bottom_pos + y_pos

                                if np.any(y_neg != 0):
                                    bars_neg = self._ax.bar(
                                        self._x_vals,
                                        y_neg,
                                        width=min(bar_width, 0.85),
                                        bottom=bottom_neg,
                                        color=colors[i],
                                        alpha=alpha,
                                        zorder=3
                                    )
                                    bottom_neg = bottom_neg + y_neg

                                bars_data[t] = {
                                    "bars": {
                                        "pos": bars_pos,
                                        "neg": bars_neg
                                    }
                                }

                        else:
                            x_plot = db.index
                            bottom_pos = np.zeros(len(db.index), dtype=float)
                            bottom_neg = np.zeros(len(db.index), dtype=float)

                            for i, t in enumerate(tickers):
                                y = np.asarray(db[t].values, dtype=float)

                                y_pos = np.where(np.isnan(y), 0.0, np.where(y > 0, y, 0.0))
                                y_neg = np.where(np.isnan(y), 0.0, np.where(y < 0, y, 0.0))

                                bars_pos = None
                                bars_neg = None

                                if np.any(y_pos != 0):
                                    bars_pos = self._ax.bar(
                                        x_plot,
                                        y_pos,
                                        width=min(bar_width, 0.85),
                                        bottom=bottom_pos,
                                        color=colors[i],
                                        alpha=alpha,
                                        label=labels[i],
                                        zorder=3
                                    )
                                    bottom_pos = bottom_pos + y_pos

                                if np.any(y_neg != 0):
                                    bars_neg = self._ax.bar(
                                        x_plot,
                                        y_neg,
                                        width=min(bar_width, 0.85),
                                        bottom=bottom_neg,
                                        color=colors[i],
                                        alpha=alpha,
                                        zorder=3
                                    )
                                    bottom_neg = bottom_neg + y_neg

                                bars_data[t] = {
                                    "bars": {
                                        "pos": bars_pos,
                                        "neg": bars_neg
                                    }
                                }

            # ==========================================================
            # MODE: LAST
            # ==========================================================
            elif bar_mode == "last":
                
                db = db[tickers].copy()
                self._bars_x_reference = list(db.index)
                x = np.arange(len(db.index), dtype=float)
                cats = [str(v) for v in db.index]
                m = len(tickers)

                vals_matrix = np.column_stack([
                    np.asarray(db[t].values, dtype=float) for t in tickers
                ])

                # guardar metadata básica del eje x
                self._x_axis_mode = "categorical"
                self._x_axis_fechas = None
                self._x_vals = x

                # -------- grouped --------
                if grouped and not stacked:
                    width = min(bar_width / max(m, 1), 0.8 / max(m, 1))

                    for i, t in enumerate(tickers):
                        offset = (i - (m - 1) / 2) * width
                        y = vals_matrix[:, i]

                        bars = self._ax.bar(
                            x + offset,
                            y,
                            width=width,
                            color=colors[i],
                            alpha=alpha,
                            label=labels[i],
                            zorder=3
                        )

                        bars_data[t] = {
                            "bars": bars
                        }

                # -------- stacked --------
                elif stacked:
                    bottom_pos = np.zeros(len(x), dtype=float)
                    bottom_neg = np.zeros(len(x), dtype=float)

                    for i, t in enumerate(tickers):
                        y = vals_matrix[:, i]

                        y_pos = np.where(np.isnan(y), 0.0, np.where(y > 0, y, 0.0))
                        y_neg = np.where(np.isnan(y), 0.0, np.where(y < 0, y, 0.0))

                        bars_pos = None
                        bars_neg = None

                        if np.any(y_pos != 0):
                            bars_pos = self._ax.bar(
                                x,
                                y_pos,
                                width=min(bar_width, 0.85),
                                bottom=bottom_pos,
                                color=colors[i],
                                alpha=alpha,
                                label=labels[i],
                                zorder=3
                            )
                            bottom_pos = bottom_pos + y_pos

                        if np.any(y_neg != 0):
                            bars_neg = self._ax.bar(
                                x,
                                y_neg,
                                width=min(bar_width, 0.85),
                                bottom=bottom_neg,
                                color=colors[i],
                                alpha=alpha,
                                zorder=3
                            )
                            bottom_neg = bottom_neg + y_neg

                        bars_data[t] = {
                            "bars": {
                                "pos": bars_pos,
                                "neg": bars_neg
                            }
                        }
                # -------- default: first ticker only --------
                else:
                    y = vals_matrix[:, 0]

                    bars = self._ax.bar(
                        x,
                        y,
                        width=min(bar_width, 0.85),
                        color=colors[0],
                        alpha=alpha,
                        label=labels[0],
                        zorder=3
                    )

                    bars_data[tickers[0]] = {
                        "bars": bars
                    }

                self._ax.set_xticks(x)
                _x_font = x_axis.get("fontsize", 8)
                self._ax.set_xticklabels(cats, fontsize=_x_font)

            else:
                raise ValueError("bar_mode must be one of: 'auto', 'time', 'last'")

            # --- guardar referencia para uso posterior
            self._bars_data = bars_data
            self._bars_stacked = stacked

            # --- 10. Configuración del eje y
            self.prep_y_axis(**y_axis)

            # --- 11. Agregar lineas horizontales
            self.horizontal_lines(**hlines)

            # --- 12. Agregar guias horizontales
            if show_hguide:
                self.guias_horizontales(mostrar_cero=False)

            # --- 13. Agregar leyenda
            self.add_legend(**legend)

            if bar_labels:
                self._bar_value_label_generate_dict(label_dict=bar_labels)

    def graph_pie(
        self,
        figsize: tuple[float, float] = (6.00, 5.00),
        titles: dict | None = None,
        source: str | list[str] | None = None,
        df_index: int = 0,
        tickers: list[str] | str = "all",
        labels: list[str] | str | None = None,
        colors: list[str] | str = PALETA_COLORES,
        x_value: str | int | float | pd.Timestamp = "last",
        donut_width: float | None = None,
        startangle: float = 90,
        counterclock: bool = False,
        autopct: str | None = "%1.1f%%",
        pctdistance: float = 0.72,
        labeldistance: float = 1.05,
        textprops: dict | None = None,
        wedgeprops: dict | None = None,
        legend: dict | None = None,
        sort_values: bool = False,
        normalize: bool = True,
        text_edge_color: str | None = None,
        text_edge_width: float = 0.0,
        label_color: str = "black",
        autopct_color: str = "white",
    ) -> None:
        """
        Create an institutional pie chart with configurable labels, tags, and legend.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        db = self._select_df(df_idx=df_index)

        if isinstance(tickers, str):
            if tickers == "all":
                tickers = db.columns.tolist()
            else:
                tickers = [tickers]

        tickers = [t for t in tickers if t in db.columns]
        if len(tickers) == 0:
            raise ValueError("No hay tickers validos para graficar.")

        db = db[tickers].copy()

        if isinstance(labels, str):
            labels = [labels]
        elif labels is None:
            labels = tickers.copy()
        elif isinstance(labels, list) and len(labels) < len(tickers):
            labels = labels + tickers[len(labels):]

        if isinstance(colors, str):
            colors = [colors]
        elif not isinstance(colors, list):
            colors = PALETA_COLORES.copy()

        colors = [
            colors[i] if i < len(colors) else PALETA_COLORES[i % len(PALETA_COLORES)]
            for i in range(len(tickers))
        ]

        ticker_to_label = {tickers[i]: labels[i] for i in range(len(tickers))}
        ticker_to_color = {tickers[i]: colors[i] for i in range(len(tickers))}

        if isinstance(x_value, str) and x_value == "last":
            db_non_empty = db.dropna(how="all")
            if db_non_empty.empty:
                raise ValueError("No hay datos disponibles para graficar pie.")
            serie = db_non_empty.iloc[-1]
        else:
            if x_value in db.index:
                serie = db.loc[x_value, tickers]
                if isinstance(serie, pd.DataFrame):
                    serie = serie.iloc[-1]
            elif isinstance(x_value, int):
                serie = db.iloc[x_value]
            else:
                raise KeyError("x_value no existe en el indice del dataframe.")

        serie = pd.to_numeric(serie, errors="coerce")
        serie = serie.replace([np.inf, -np.inf], np.nan).dropna()

        if serie.empty:
            raise ValueError("La fila seleccionada no tiene valores numericos para graficar pie.")

        if sort_values:
            serie = serie.sort_values(ascending=False)

        plot_tickers = serie.index.tolist()
        plot_labels = [ticker_to_label.get(t, t) for t in plot_tickers]
        plot_colors = [ticker_to_color.get(t, PALETA_COLORES[i % len(PALETA_COLORES)]) for i, t in enumerate(plot_tickers)]

        self._ticker_label_color = [
            (plot_tickers[i], plot_labels[i], plot_colors[i]) for i in range(len(plot_tickers))
        ]

        titles = titles if titles is not None else dict()
        legend = legend if legend is not None else dict()
        textprops = textprops if textprops is not None else dict()
        wedgeprops = wedgeprops if wedgeprops is not None else dict()

        if donut_width is not None:
            wedgeprops["width"] = donut_width

        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        self._ax.clear()
        self.set_titles(**titles)
        if source:
            self.add_source(source)

        pie_out = self._ax.pie(
            serie.values,
            labels=plot_labels,
            colors=plot_colors,
            startangle=startangle,
            counterclock=counterclock,
            autopct=autopct,
            pctdistance=pctdistance,
            labeldistance=labeldistance,
            textprops=textprops,
            wedgeprops=wedgeprops,
            normalize=normalize,
        )

        # labels (texto)
        if len(pie_out) > 1:
            for txt in pie_out[1]:
                txt.set_color(label_color)

        # porcentajes (números)
        if len(pie_out) > 2:
            for txt in pie_out[2]:
                txt.set_color(autopct_color)
                txt.set_fontweight("bold")

        self._ax.axis("equal")
        
        if text_edge_color is not None and text_edge_width and text_edge_width > 0:
            for txt in pie_out[1]:
                txt.set_path_effects([
                    path_effects.withStroke(linewidth=text_edge_width, foreground=text_edge_color)
                ])

            if len(pie_out) > 2:
                for txt in pie_out[2]:
                    txt.set_path_effects([
                        path_effects.withStroke(linewidth=text_edge_width, foreground=text_edge_color)
                    ])

        if legend.get("show", False):
            _legend = legend.copy()
            del _legend["show"]
            if "loc" not in _legend:
                _legend["loc"] = "center left"
            if "bbox_to_anchor" not in _legend:
                _legend["bbox_to_anchor"] = (1.02, 0.5)
            self._ax.legend(pie_out[0], plot_labels, **_legend)

        self._fig.subplots_adjust(
            left=0.08,
            right=0.88,
            top=0.80,
            bottom=0.18
        )

    def graph_box_whiskers(
        self,
        # --- Configuración del gráfico ---
        figsize: tuple[float, float] = (6.00, 5.00),
        # --- Configuración de elementos adicionales ---
        titles: dict | None = None,
        source: dict | None = None,
        # --- Configuración de df -----
        df_index: int = 0,                      # índice del dataframe a usar (en caso de tener varios)
        # --- Configuración de series ---
        tickers: list[str] | str = "all",
        labels: list[str] | str | None = None,
        colors: list[str] | str = PALETA_COLORES,
        box_face_alpha: float = 0.5,
        # --- Configuración del boxplot ---
        box_config: dict | None = None,
        box_style: dict | None = None,
        median_style: dict | None = None,
        whisker_style: dict | None = None,
        cap_style: dict | None = None,
        flier_style: dict | None = None,
        mean_style: dict | None = None,
        # --- Configuración del eje y ---
        y_axis: dict | None = None,
        # --- Configuración del eje x ---
        x_axis: dict | None = None,
        # --- Configuración de rangos
        range_tag_high: dict | None = None,
        range_tag_low: dict | None = None,
        mean_tag: dict | None = None,
        
        # Configuración de la leyenda   
        legend: dict | None = None,
        tag_dot: dict | None = None,

        # --- Configuración de otros factores ---
        hlines: dict | None = None,
        show_hguide: bool = False,
    ):
        """
        Create an institutional box-and-whisker chart from dataframe columns.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        # --- 1. Importación y setteo del dataframe 
        db = self._select_df(df_idx=df_index)
        
        # --- 3. Normalización de los tickers
        if isinstance(tickers, str):
            if tickers == "all":
                tickers = db.columns.tolist()
            else:
                tickers = [tickers]

        db = db[tickers].copy()  # filtrar solo los tickers seleccionados

        # --- 4. Asignación de etiquetas
        if isinstance(labels, str):
            labels = [labels]
        elif isinstance(labels, list):
            if len(labels) < len(db.columns.tolist()):
                add = db.columns.tolist()
                add = add[len(labels):]
                labels = labels + add
        else:
            labels = db.columns.tolist()
        
        # --- 4. Normalización de los colores
        if isinstance(colors, str):
            colors = [colors]
        elif isinstance(colors, list):
            if len(colors) < len(db.columns.tolist()):
                add = PALETA_COLORES
                add = add[len(colors):]
                colors = colors + add
        else:
            colors = PALETA_COLORES
        
        # --- 5. Asignación de ticker label color
        self._ticker_label_color = [(tickers[i], labels[i], colors[i]) for i,t in enumerate(tickers)]

        # --- 6. revision de dicts
        x_axis = x_axis if x_axis is not None else dict()
        y_axis = y_axis if y_axis is not None else dict()
        titles = titles if titles is not None else dict()
        legend = legend if legend is not None else dict()
        hlines = hlines if hlines is not None else dict()
        source = source if source is not None else dict()

        # --- 7. Generación del gráfico y el plot en caso no exista
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        # --- 8. Agregar titulos globales
        self.set_titles(**titles)
        self.add_source(**source)

        # --- 9. Manejo del eje x
        db = self.prep_x_axis(dataframe=db, **x_axis)
        
        #overide el eje a categorico para este tipo de grafico
        self._x_axis_mode = "categorical"

        # --- 10. preparar datos para el boxplot
        data_plot = [db[t].dropna().values for t in tickers]

        # --- 11. Funciones de ayuda para los elementos del boxplot
        def _median(
                color: str = "#222222",
                lw: float = 1.5,
        ):
            """
            Execute `_median` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            return locals()
        
        def _whisker(
                color: str = "#6E6E6E",
                lw: float = 0.5,
        ):
            """
            Execute `_whisker` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            return locals()

        def _cap(
                color: str = "#6E6E6E",
                lw: float = 0.5,
        ):
            """
            Execute `_cap` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            return locals()

        def _box(
                color: str = "#6E6E6E",
                lw: float = 0.5,
        ):
            """
            Execute `_box` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            return locals()

        def _fliers(
                marker: str = "o",
                markersize: float = 3.5,
                markerfacecolor: str = "#999999",
                markeredgecolor: str = "#999999",
                alpha: float = 0.85,
        ):
            """
            Execute `_fliers` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            return locals()         
        
        def _mean(
                color: str = "#404040",
                lw: float = 0.5,
                linestyle: str = "--"
        ):
            """
            Execute `_mean` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            return locals()
        
        def _box_config(
            whis=(0, 100),                    
            showfliers: bool = False,
            showmeans: bool = False,
            meanline: bool = False,
            widths: float | list[float] = 0.6,
            notch: bool = False,
            vert: bool = True, 
        ):
            """
            Execute `_box_config` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            return locals()
        
        # --- 12. Configuración de elementos del boxplot
        box_config = _box_config() if box_config is None else _box_config(**box_config)
        box_style = _box() if box_style is None else _box(**box_style)
        median_style = _median() if median_style is None else _median(**median_style)
        whisker_style = _whisker() if whisker_style is None else _whisker(**whisker_style)
        cap_style = _cap() if cap_style is None else _cap(**cap_style)
        flier_style = _fliers() if flier_style is None else _fliers(**flier_style)
        mean_style = _mean() if mean_style is None else _mean(**mean_style)

        # Vamos a sacar el valor de vert del box_config para usarlo en otras partes del código
        vert = box_config.get("vert", True)

        # --- 14. Grafica boxplot
        bp = self._ax.boxplot(
            data_plot,
            labels=labels,
            **box_config,
            patch_artist=True,
            boxprops=box_style,
            medianprops=median_style,
            whiskerprops=whisker_style,
            capprops=cap_style,
            flierprops=flier_style,
            meanprops=mean_style,
        )

        # --- 15. Aplicar colores a las cajas
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(colors[i])
            patch.set_alpha(box_face_alpha)

        # --- 17. funcion de ayuda para las etiquetas de estadisticos de muestra
        def _tag(
            # asociado a valor_etiqueta
            label_h_align: str = "center",
            label_v_align: str = "center",
            ubic_etq: tuple[float, float] = (0, 10),
            fontsize: float = 8,
            fontweight: str = "bold",
            font_color:str = "black",
            bg_color: str = "None",
            bg_alpha: float = 1.0,
            edge_color: str = "None",
            show_bbox: bool = True,
            zorder: float = 20,
            # eliminar una vez guardados
            fmt: str = ",.1f",
            show: bool = True,
        ):
            """
            Execute `_tag` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            return locals()
        
        # --- 18 generación de dicts para estadisticos
        range_tag_high = _tag() if range_tag_high is None else _tag(**range_tag_high)
        range_tag_low = _tag() if range_tag_low is None else _tag(**range_tag_low)
        mean_tag = _tag() if mean_tag is None else _tag(**mean_tag)

        # almacenamiento y eliminación de puntos del dict
        range_tag_high_show = range_tag_high.get("show", False)
        range_tag_high_fmt = range_tag_high.get("fmt", ",.2f")

        range_tag_low_show = range_tag_low.get("show", False)
        range_tag_low_fmt = range_tag_low.get("fmt", ",.2f")
        
        mean_tag_show = mean_tag.get("show", False)
        mean_tag_fmt = mean_tag.get("fmt", ",.2f")

        # eliminación de puntos
        del range_tag_high["show"]
        del range_tag_high["fmt"]
        
        del range_tag_low["show"]
        del range_tag_low["fmt"]
        if range_tag_low["ubic_etq"] == (0,10):
            range_tag_low["ubic_etq"] = (0,-10)

        del mean_tag["show"]
        del mean_tag["fmt"]
        if mean_tag["ubic_etq"] == (0,10):
            mean_tag["ubic_etq"] = (0,0)

        if range_tag_high_show or range_tag_low_show or mean_tag_show:
            for i, t in enumerate(tickers):
                low_whisker = bp["whiskers"][2 * i]
                high_whisker = bp["whiskers"][2 * i + 1]
                s = db[t].dropna()
                stat_val = float(s.mean())

                if vert:
                    # real whisker end coordinates
                    x_low = float(np.mean(low_whisker.get_xdata()))
                    y_low = float(np.min(low_whisker.get_ydata()))

                    x_high = float(np.mean(high_whisker.get_xdata()))
                    y_high = float(np.max(high_whisker.get_ydata()))

                else:
                    y_low = float(np.mean(low_whisker.get_ydata()))
                    x_low = float(np.min(low_whisker.get_xdata()))

                    y_high = float(np.mean(high_whisker.get_ydata()))
                    x_high = float(np.max(high_whisker.get_xdata()))

                if range_tag_low_show:
                    self.etiqueta_valor(
                        x_value=x_low,
                        y_value=y_low,
                        label=f"{y_low:{range_tag_low_fmt}}",
                        **range_tag_low
                    )

                if range_tag_high_show:
                    self.etiqueta_valor(
                        x_value=x_high,
                        y_value=y_high,
                        label=f"{y_high:{range_tag_high_fmt}}",
                        **range_tag_high
                    )
                
                if mean_tag_show:
                    self.etiqueta_valor(
                        x_value=i+1,
                        y_value=stat_val,
                        label=f"{stat_val:{mean_tag_fmt}}",
                        **mean_tag
                    )
                    
        self._box_whiskers_label_generate(control_dict=tag_dot)


        # -----------------------
        # 7) Shared styling
        # -----------------------
        self.horizontal_lines(**hlines)

        if show_hguide:
            self.guias_horizontales(mostrar_cero=False)

        self.prep_y_axis(**y_axis)

        self.add_legend(**legend)

