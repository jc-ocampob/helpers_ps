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

from .metadata import Graph_meta_data
from .config import buffers

@dataclass
class Graph_base(Graph_meta_data):  
    """
    Provide shared plotting utilities for axes, titles, legends, guides, saving, and layout.

    Notes
    -----
    This docstring was added during the modular refactor to make the API easier
    to understand for new users and maintainers.
    """

    # =========================
    # funciones de ayuda
    # =========================
    def _months_years(self, fechas):
        """
        Extract month and year labels from a date-like sequence.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        mes_es = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
            5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }

        self._months = [mes_es[d.month] for d in fechas]
        self._years = np.array([d.year for d in fechas])

    def años_eje_x(self, y_offset=-0.08, fontsize=None, color='black'):     
        """
        Add year labels below the x-axis for date-based charts.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        years = getattr(self, "_years", None)
        if years is None:
            return

        if fontsize is None:
                fontsize = getattr(self, "_tick_fontsize", 8)

        for yr in np.unique(years):
            idx = np.where(years == yr)[0]
            mid = idx.mean()
            self._ax.text(
                mid, y_offset, str(yr),
                transform=self._ax.get_xaxis_transform(),
                ha='center', va='top',
                fontsize=fontsize,
                color=color
            )

    def _coerce_to_bbg_x(self, x):
        """
        Convert incoming x values into the internal Bloomberg-style x-axis representation.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        fechas = self._x_axis_fechas
        if fechas is None or len(fechas) == 0:
            return float(x)

        if isinstance(x, (int, float, np.integer, np.floating)):
            return float(x)

        try:
            dt = pd.to_datetime(x)
        except Exception:
            return float(x)

        arr = fechas.values
        pos = np.searchsorted(arr, np.datetime64(dt), side="left")
        pos = int(np.clip(pos, 0, len(fechas) - 1))
        return float(pos)

    # =========================
    # Metodos de los ejes
    # =========================
    def prep_x_axis(
            self,
            dataframe: pd.DataFrame = None,
            bbg_format: bool = False, 
            tick_step: int = 6, 
            fmt: str = None, 
            year_y_offset:float = -0.08, 
            lim: tuple[float, float] = None,
            fontsize: float = 8,
            return_dataframe: bool = True,
        ) -> pd.DataFrame:

        """
        Prepare the x-axis format, labels, ticks, and internal x-axis metadata.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if dataframe is None:
            dataframe = self._df
        fechas = None
        x_vals = None
        x_index = dataframe.index

        if lim is not None and isinstance(lim, tuple):
            start_value_x, end_value_x = lim
            if start_value_x is not None:
                dataframe = dataframe[dataframe.index >= start_value_x].copy()
            if end_value_x is not None:
                dataframe = dataframe[dataframe.index <= end_value_x].copy()

        # validar el tipo de información
        is_datetime = pd.api.types.is_datetime64_any_dtype(x_index)
        is_numeric = pd.api.types.is_numeric_dtype(x_index)
      
        # -- si el eje es fecha con formato bbg 
        if bbg_format and is_datetime:
            fechas = pd.Index(dataframe.index.sort_values().unique())
            x_vals = np.arange(len(fechas))
            self._months_years(fechas)
            month_change = pd.Series(fechas).dt.to_period("M").ne(
                pd.Series(fechas).dt.to_period("M").shift()
            )
            month_idx = np.where(month_change)[0]
            tick_idx = month_idx[::tick_step]
            self._ax.set_xticks(tick_idx)
            self._ax.set_xticklabels([self._months[i] for i in tick_idx], fontsize=fontsize)
            self.años_eje_x(y_offset=year_y_offset, fontsize=fontsize)
            self._x_axis_mode = "bbg"
            self._x_axis_fechas = fechas

        elif is_datetime:
            x_vals = dataframe.index.values
            x_axis_format = fmt if fmt is not None else "%B-%y"
            locator = mdates.MonthLocator(interval=tick_step)
            formatter = mdates.DateFormatter(x_axis_format)
            self._ax.xaxis.set_major_locator(locator)
            self._ax.xaxis.set_major_formatter(formatter)
            self._ax.tick_params(axis='x', labelsize=fontsize)
            self._x_axis_mode = "datetime"
        
        elif is_numeric:
            x_axis_format = fmt if fmt is not None else ",.0f"
            x_vals = dataframe.index.values
            # sample ticks every N observations
            tick_idx = np.arange(0, len(x_vals), tick_step)
            self._ax.set_xticks(x_vals[tick_idx])
            # formatting (optional)
            self._ax.set_xticklabels(
                [f"{x_vals[i]:{x_axis_format}}" for i in tick_idx],  # adjust format if needed
                fontsize=fontsize
            )
            self._ax.tick_params(axis='x', labelsize=fontsize)
            self._x_axis_mode = "numeric"

        # --- Preparar eje X: Fall back ---
        else:
            x_vals = dataframe.index.values
            self._ax.tick_params(axis='x', labelsize=fontsize)
            self._x_axis_mode = "categorical"
        
        self._x_vals = x_vals

        # layout adjust con el formato bbg
        if self._x_axis_mode == "bbg":
            self._fig.subplots_adjust(
                left=0.15,
                right=0.93,
                top=0.80,
                bottom=0.21
            )
        else:
            self._fig.subplots_adjust(
                left=0.15,
                right=0.93,
                top=0.80,
                bottom=0.18
            )
        
        return dataframe

    def prep_y_axis(
        self,
        lim: tuple[float, float] | None = None,
        fmt: str | None = None,
        fontsize: float = 7,
        tick_step: int = None
    ) -> None:
        
        # --- Configuración del limite y ---
        """
        Prepare the y-axis format, labels, limits, tick spacing, and number formatting.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if lim is not None:
            self._ax.set_ylim(*lim)
        self._ax.margins(x=0.01)
                
        # Agregar format al eje y
        fmt = fmt if fmt is not None else ",.0f"
        self._ax.yaxis.set_major_formatter(
            FuncFormatter(lambda x, pos: f"{x:{fmt}}")
        )
        self._ax.tick_params(axis='y', labelsize=fontsize)

        if tick_step is not None:
            self._ax.yaxis.set_major_locator(MultipleLocator(tick_step))

    # =========================
    # Metodos de titulos subtitulos y fuente
    # =========================
    def set_titles(
        self,
        title: str | None = None,
        title_font_size: int = 12,
        subtitle: str | None = None,
        subtitle_font_size: int = 9
    ) -> None:
        """
        Add and format main title, subtitle, and related textual headers for the active figure.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        
        # eliminar title del axis
        self._ax.set_title("")

        # título principal (arriba del todo)
        if title:
            self._fig.text(
                0.02, 0.93,
                title,
                ha="left",
                va="top",
                fontsize=title_font_size,
                fontweight="bold"
            )

        # subtítulo
        if subtitle:
            self._fig.text(
                0.02, 0.88,
                subtitle,
                ha="left",
                va="top",
                fontsize=subtitle_font_size,
                color="#333333"
            )

    def add_source(
        self,
        text: str | list | None = None,
        x: float = 0.02,
        y: float = 0.022,
        fontsize: float = 6,
        color: str = "#606060",
        line_spacing: float = 0.022,
    ):
        """
        Add a source note or footer text to the active figure.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if text is None:
            return None
        
        if isinstance(text, str):
            lines = [text]
        else:
            lines = list(text)

        if len(lines) > 4:
            raise ValueError("Too many lines for source. Max 4.")
        elif len(lines) < 4:
            lines += [""] * (4 - len(lines))

        for i, line in enumerate(lines[::-1]):
            self._fig.text(
                x,
                y + i * line_spacing,
                line,
                ha="left",
                va="bottom",
                fontsize=fontsize,
                color=color
            )

    def add_legend(
            self,
            show: bool = False,
            loc: str = "upper left",
            bbox_to_anchor: tuple = None,
            ncol: int = 3,
            fontsize: int = 7,
            frameon: bool = True,
            edgecolor: str = "white",
            facecolor: str = "white",
            framealpha: float = 0.6
    ) -> None:
        """
        Create and style the legend using chart series and custom legend handles.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        if not show:
            return None

        handles, labels = self._ax.get_legend_handles_labels()

        custom_handles = getattr(self, "_custom_legend_handles", None)

        if custom_handles:
            handles = handles + custom_handles
            labels = labels + [h.get_label() for h in custom_handles]

        # -------------------------------------------------
        # Evitar duplicados preservando orden
        # -------------------------------------------------
        final_handles = []
        final_labels = []
        seen = set()

        for h, lab in zip(handles, labels):
            if lab is None or lab == "" or lab.startswith("_"):
                continue

            if lab in seen:
                continue

            final_handles.append(h)
            final_labels.append(lab)
            seen.add(lab)

        if len(final_handles) == 0:
            return None

        self._ax.legend(
            final_handles,
            final_labels,
            loc=loc,
            bbox_to_anchor=bbox_to_anchor,
            ncol=ncol,
            fontsize=fontsize,
            frameon=frameon,
            edgecolor=edgecolor,
            facecolor=facecolor,
            framealpha=framealpha
        )

    def add_legend_point(
        self,
        label: str,
        color: str,
        marker: str = "o",
        markersize: float = 6,
    ):
        
        """
        Register a custom point-style legend item for the active axis.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not hasattr(self, "_custom_legend_handles"):
            self._custom_legend_handles = []

        existing_labels = {
            h.get_label()
            for h in self._custom_legend_handles
        }

        if label in existing_labels:
            return None

        self._custom_legend_handles.append(
            Line2D(
                [0],
                [0],
                marker=marker,
                linestyle="None",
                color="none",
                markerfacecolor=color,
                markeredgecolor=color,
                markersize=markersize,
                label=label,
            )
        )

    # =========================
    # Metodos de la figura general
    # =========================
    def show(self) -> None:
        """
        Display the active Matplotlib figure.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if self._fig:
            return self._fig.show()

    def save(
        self,
        dir: dict = buffers,
        name: str = "graph_1",
        dpi: int = 400,
        reset_buffers: bool = True
    ):
        """
        Save the active figure into an in-memory PNG buffer or custom buffer store.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        buf = io.BytesIO()
        self._fig.savefig(buf, format="png", dpi=dpi)   # use figure-level save
        buf.seek(0)
        dir[name] = buf
        plt.close(self._fig)

        if reset_buffers:
            self._fig = None
            self._ax = None
            self._axes = None
            self._axes_shape = None
            self._axes_state = None
            self._active_ax_idx = 0
            self._xmeta = None
            self._bar_meta = None
            self._months = None
            self._years = None
            self._custom_legend_handles = None

    def plot(
        self,
        figsize: tuple[float, float] = (6.00, 4.80),
        color: str ="#D5D5D5",
        lw: float = 0.8,
        nrows: int = 1,
        ncols: int = 1,
        sharex: bool = False,
        sharey: bool = False,
        dpi: int | None = None,
        height_ratios: list[float] | None = None,
        width_ratios: list[float] | None = None,
        hspace: float | None = None,
        wspace: float | None = None
    ) -> None:
        """
        Create the base Matplotlib figure and axes layout used by chart methods.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        # -------------------------------------------------
        # 1. Crear figura + axes
        # -------------------------------------------------
        use_gridspec = any([
            height_ratios is not None,
            width_ratios is not None,
            hspace is not None,
            wspace is not None,
            dpi is not None
        ])

        if not use_gridspec:
            fig, axes = plt.subplots(
                nrows=nrows,
                ncols=ncols,
                figsize=figsize,
                sharex=sharex,
                sharey=sharey
            )
        else:
            fig = plt.figure(figsize=figsize, dpi=dpi)

            gs_kwargs = {
                "nrows": nrows,
                "ncols": ncols
            }

            if height_ratios is not None:
                gs_kwargs["height_ratios"] = height_ratios

            if width_ratios is not None:
                gs_kwargs["width_ratios"] = width_ratios

            if hspace is not None:
                gs_kwargs["hspace"] = hspace

            if wspace is not None:
                gs_kwargs["wspace"] = wspace

            gs = fig.add_gridspec(**gs_kwargs)

            axes = []
            first_ax = None

            for r in range(nrows):
                row_axes = []
                for c in range(ncols):
                    subplot_kwargs = {}

                    if first_ax is not None:
                        if sharex:
                            subplot_kwargs["sharex"] = first_ax
                        if sharey:
                            subplot_kwargs["sharey"] = first_ax

                    ax = fig.add_subplot(gs[r, c], **subplot_kwargs)

                    if first_ax is None:
                        first_ax = ax

                    row_axes.append(ax)

                axes.append(row_axes)

            if nrows == 1 and ncols == 1:
                axes = axes[0][0]
            else:
                axes = np.array(axes, dtype=object)

        # -------------------------------------------------
        # 2. Guardar figura
        # -------------------------------------------------
        self._generate_metadata(
            fig,
            axes,
            nrows,
            ncols
        )

        # -------------------------------------------------
        # 5. Líneas decorativas de figura
        # -------------------------------------------------
        self._fig.add_artist(
            Line2D(
                [0.01, 0.98], [0.95, 0.95],
                transform=self._fig.transFigure,
                color=color, lw=lw
            )
        )

        self._fig.add_artist(
            Line2D(
                [0.01, 0.98], [0.12, 0.12],
                transform=self._fig.transFigure,
                color=color, lw=lw
            )
        )

        # -------------------------------------------------
        # 6. Ajustes globales
        # -------------------------------------------------
        # Si no usas gridspec custom, mantén el comportamiento original
        if not use_gridspec:
            self._fig.subplots_adjust(
                left=0.15,
                right=0.93,
                top=0.80,
                bottom=0.30
            )

    # =========================
    # Metodos de as etiquetas, guias y sombras
    # =========================
    def guias_horizontales(self, mostrar_cero=True):
        """
        Add horizontal guide lines to improve chart readability.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        self._ax.yaxis.grid(
            True,
            linestyle='--',
            linewidth=0.5,
            color='gray',
            alpha=0.35
        )
        self._ax.set_axisbelow(True)
        if mostrar_cero:
            self._ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)

    def etiqueta_valor(
        self,
        x_value: float | str | pd.Timestamp,
        y_value: float,
        label: str,
        label_h_align: str ="center",
        label_v_align: str ="center",
        ubic_etq: tuple =(0, 17),
        fontsize: int =7,
        fontweight: str ="normal",
        font_color: str ="black",
        bg_color: str = "#ECEFF1",
        bg_alpha: float = 1.0,
        edge_color: str = "none",
        show_bbox: bool = True,
        text_edge_color: str | None = None,
        text_edge_width: float = 0.0,
        zorder: int = 6,
    ):
        """
        Add a value label annotation to a selected chart point or coordinate.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("Axis not initialized.")


        mode = self._x_axis_mode

        # --- Convert x_value ---
        if mode == "bbg":
            x_plot = self._coerce_to_bbg_x(x_value)
        else:
            x_conv = x_value

            if mode == "datetime":
                try:
                    x_conv = pd.to_datetime(x_value)
                except Exception:
                    pass

            x_plot = self._ax.convert_xunits(x_conv)

            if np.ndim(x_plot) > 0:
                x_plot = np.asarray(x_plot).item()

        # --- Bounding box config ---
        bbox = None
        if show_bbox:
            bbox = dict(
                boxstyle="round,pad=0.4",
                fc=bg_color,
                ec=edge_color,
                alpha=bg_alpha
            )

        # --- Annotate ---
        annotation = self._ax.annotate(
            label,
            xy=(x_plot, y_value),
            xytext=ubic_etq,
            textcoords="offset points",
            ha=label_h_align,
            va=label_v_align,
            fontsize=fontsize,
            fontweight=fontweight,
            color=font_color,
            bbox=bbox,
            zorder=zorder
        )

        # Optional text stroke to improve readability over busy backgrounds.
        if text_edge_color is not None and text_edge_width and text_edge_width > 0:
            annotation.set_path_effects([
                path_effects.withStroke(linewidth=text_edge_width, foreground=text_edge_color)
            ])
    
    def punto_valor(
        self,
        x_value,
        y_value,
        color="red",
        size=30,
        zorder=5
    ):
        """
        Add a highlighted point marker and optional label to the chart.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("Axis not initialized.")

        mode = self._x_axis_mode

        # --- Convert x_value ---
        if mode == "bbg":
            x_plot = self._coerce_to_bbg_x(x_value)
        else:
            x_conv = x_value

            if mode == "datetime":
                try:
                    x_conv = pd.to_datetime(x_value)
                except Exception:
                    pass

            x_plot = self._ax.convert_xunits(x_conv)

            if np.ndim(x_plot) > 0:
                x_plot = np.asarray(x_plot).item()

        # --- Plot point ---
        self._ax.scatter(
            x_plot,
            y_value,
            color=color,
            s=size,
            zorder=zorder
        )

    def shade_x(
        self,
        periods,
        color="#B0B0B0",
        alpha=0.25,
        zorder=0,
        label=None,
        hatch=None,
        ymin=0.0,
        ymax=1.0,
        clip_to_xlim=True,
    ):
        """
        Add shaded x-axis regions to highlight periods or ranges.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("No axis found. Call graph_line/graph_bar first.")

        if isinstance(periods, tuple) and len(periods) == 2:
            periods = [periods]

        mode = self._x_axis_mode
        bar_meta = self._bar_mode

        used_label = False
        xlim = self._ax.get_xlim()

        # ==========================================================
        # Helpers locales para bar_mode="last"
        # ==========================================================
        def _collect_rects_for_idx(idx: int) -> list:
            """
            Execute `_collect_rects_for_idx` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            rects = []

            if not hasattr(self, "_bars_data") or not self._bars_data:
                return rects

            for entry in self._bars_data.values():
                bars_obj = entry.get("bars")

                # --- stacked
                if isinstance(bars_obj, dict):
                    for side in ("pos", "neg"):
                        bars_side = bars_obj.get(side)
                        if bars_side is None or idx >= len(bars_side):
                            continue

                        rect = bars_side[idx]
                        if rect is None:
                            continue

                        try:
                            h = rect.get_height()
                        except Exception:
                            h = None

                        if h is None:
                            continue

                        try:
                            if np.isnan(h):
                                continue
                        except Exception:
                            pass

                        rects.append(rect)

                # --- grouped / single
                else:
                    if bars_obj is None or idx >= len(bars_obj):
                        continue

                    rect = bars_obj[idx]
                    if rect is None:
                        continue

                    try:
                        h = rect.get_height()
                    except Exception:
                        h = None

                    if h is None:
                        continue

                    try:
                        if np.isnan(h):
                            continue
                        # si quieres excluir barras vacías:
                        # if abs(h) == 0:
                        #     continue
                    except Exception:
                        pass

                    rects.append(rect)

            return rects

        def _cluster_bounds(idx: int, default_half_width: float = 0.4) -> tuple[float, float]:
            """
            Execute `_cluster_bounds` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            rects = _collect_rects_for_idx(idx)

            if not rects:
                center = float(idx)
                return center - default_half_width, center + default_half_width

            left = min(r.get_x() for r in rects)
            right = max(r.get_x() + r.get_width() for r in rects)
            return float(left), float(right)

        # ==========================================================
        # Main
        # ==========================================================
        for p in periods:
            if isinstance(p, dict):
                start = p.get("start")
                end = p.get("end")
                c = p.get("color", color)
                a = p.get("alpha", alpha)
                lab = p.get("label", None)
                hat = p.get("hatch", hatch)
            else:
                start, end = p
                c, a, lab, hat = color, alpha, None, hatch

            if mode == "bbg":
                x0 = self._coerce_to_bbg_x(start)
                x1 = self._coerce_to_bbg_x(end)

            elif bar_meta is not None and bar_meta == "last":
                xticklabels = [t.get_text() for t in self._ax.get_xticklabels()]

                def _to_pos(val):
                    # string => buscar en labels del eje
                    """
                    Execute `_to_pos` as part of the chart-building workflow.

                    Notes
                    -----
                    This docstring was added during the modular refactor to make the API easier
                    to understand for new users and maintainers.
                    """
                    if isinstance(val, str):
                        if val not in xticklabels:
                            raise ValueError(f"{val} not found in x labels")
                        return int(xticklabels.index(val))

                    # enteros => posición categórica
                    if isinstance(val, (int, np.integer)):
                        return int(val)

                    # floats enteros => posición categórica
                    if isinstance(val, (float, np.floating)) and float(val).is_integer():
                        return int(val)

                    # cualquier otro numérico fino => usar directo
                    return float(val)

                p0 = _to_pos(start)
                p1 = _to_pos(end)

                if isinstance(p0, (int, np.integer)) and isinstance(p1, (int, np.integer)):
                    left0, right0 = _cluster_bounds(int(p0))
                    left1, right1 = _cluster_bounds(int(p1))
                    x0 = left0
                    x1 = right1
                else:
                    x0 = float(p0)
                    x1 = float(p1)

            else:
                s = start
                e = end

                if mode == "datetime":
                    try:
                        s = pd.to_datetime(start)
                    except Exception:
                        pass

                    try:
                        e = pd.to_datetime(end)
                    except Exception:
                        pass

                    # widen only for bar charts in time mode
                    if bar_meta is not None and bar_meta == "time":
                        delta = pd.Timedelta(days=15)
                        s = s - delta
                        e = e + delta

                x0 = self._ax.convert_xunits(s)
                x1 = self._ax.convert_xunits(e)

                if np.ndim(x0) > 0:
                    x0 = np.asarray(x0).item()
                if np.ndim(x1) > 0:
                    x1 = np.asarray(x1).item()

            if x1 < x0:
                x0, x1 = x1, x0

            if clip_to_xlim:
                x0 = max(x0, xlim[0])
                x1 = min(x1, xlim[1])
                if x1 <= x0:
                    continue

            final_label = None
            if lab is not None:
                final_label = lab
            elif label is not None and not used_label:
                final_label = label
                used_label = True

            self._ax.axvspan(
                x0,
                x1,
                ymin=ymin,
                ymax=ymax,
                facecolor=c,
                alpha=a,
                zorder=zorder,
                label=final_label,
                hatch=hat
            )

    def horizontal_lines(
            self,
            y_values: list[float] | float | None = None,
            linestyle: str | None = None,
            linewidth: float = 0.5,
            color: str = "gray",
    ) -> None:
        """
        Add one or more horizontal reference lines to the active axis.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if y_values is None:
            return None

        if isinstance(y_values, (int, float)):
            y_values = [y_values]
        
        for y in y_values:
            self._ax.axhline(y, color=color, linestyle=linestyle, linewidth=linewidth)

    # =========================
    # Metodos para agregar recesiones a las graficas
    # =========================
    def add_recesiones(
            self,
            country: str = "United States",
            data_frame: bool = False,
            controles: dict = None
    ):
        """
        Add recession or event-shading regions over a date-based x-axis.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        csv_path = files("helpers_ps").joinpath("Data/recessions.csv")
        recesiones = pd.read_csv(csv_path, parse_dates=["start_date", "end_date"])
        recesiones = recesiones.set_index("recesion_id")
        if data_frame:
            return recesiones
        
        # plotear en el eje
        if self._ax is None:
            raise RuntimeError("No existe grafico para agregar las recesiones")
        
        if self._x_axis_mode not in ["bbg", "datetime"]:
            raise TypeError("No se pueden aplicar recesiones a un grafico que no tiene como eje fechas")
        
        if country not in recesiones["country"].unique():
            raise NotImplementedError("No hay registro de recesiones para ese pais")
        
        recesiones = recesiones[recesiones["country"] == country].copy()
        
        # agregar recesiones a la grafica
        date_list = [(recesiones.loc[x,"start_date"].strftime("%Y-%m-%d"), recesiones.loc[x,"end_date"].strftime("%Y-%m-%d")) for x in recesiones.index.tolist()]
        controles = controles if controles is not None else dict(color="grey", alpha=0.3)
        self.shade_x(periods=date_list, **controles)

        return None

