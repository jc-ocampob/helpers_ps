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
    from helpers_ps.GlobVars.var_globs import PALETA_COLORES
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
    Base class that provides shared Matplotlib utilities for chart construction.

    This class centralizes the common functionality used by higher-level chart
    builders, including axis preparation, title and subtitle handling, source
    notes, legends, horizontal guides, value annotations, shaded regions,
    recession overlays, figure creation, and figure export.

    It is intended to be inherited by chart-specific classes so that line, bar,
    pie, boxplot, and other chart types can reuse a consistent plotting style
    and metadata management workflow.

    Notes
    -----
    This class assumes that figure and axis metadata are managed through
    `Graph_meta_data`, particularly via `_generate_metadata`.
    """

    # =========================
    # funciones de ayuda
    # =========================
    def _months_years(self, fechas):
        """
        Extract Spanish month abbreviations and years from a date-like index.

        This helper stores month labels and year values in the instance so they can
        be reused when creating Bloomberg-style x-axis labels.

        Parameters
        ----------
        fechas : sequence of datetime-like values
            Date-like sequence used to extract month abbreviations and years.

        Returns
        -------
        None
            The extracted values are stored internally in `_months` and `_years`.
        """
        mes_es = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
            5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }

        self._months = [mes_es[d.month] for d in fechas]
        self._years = np.array([d.year for d in fechas])

    def _years_xaxis(self, y_offset=-0.08, fontsize=None, color='black'):
        """
        Add year labels below the x-axis for Bloomberg-style date charts.

        This method uses the internally stored `_years` array to place one centered
        year label below each group of monthly x-axis labels.

        Parameters
        ----------
        y_offset : float, default -0.08
            Vertical offset of the year labels relative to the x-axis transform.
        fontsize : float or None, optional
            Font size of the year labels. If None, the method uses the internal
            tick font size when available.
        color : str, default "black"
            Text color of the year labels.

        Returns
        -------
        None
            Year labels are added directly to the active axis.
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
        Convert an x-axis input value into the internal Bloomberg-style position.

        Bloomberg-style charts use integer positions instead of the original
        datetime values. This helper converts dates, timestamps, or numeric values
        into the corresponding numeric x-coordinate used by the active axis.

        Parameters
        ----------
        x : int, float, str, pandas.Timestamp, or datetime-like
            Input x-axis value to convert.

        Returns
        -------
        float
            Numeric x-axis position compatible with the Bloomberg-style axis.

        Notes
        -----
        If the internal Bloomberg date index is not available, the function attempts
        to return the input value as a float.
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
            year_y_offset: float = -0.08,
            lim: tuple[float, float] = None,
            fontsize: float = 8,
            return_dataframe: bool = True,
        ) -> pd.DataFrame:
        """
        Prepare the x-axis format, ticks, labels, limits, and internal metadata.

        This method detects whether the DataFrame index is datetime-like, numeric,
        or categorical, and applies the appropriate x-axis formatting. It also
        supports a Bloomberg-style date axis, where dates are represented as
        sequential integer positions with month labels and year labels.

        Parameters
        ----------
        dataframe : pandas.DataFrame or None, optional
            DataFrame used to configure the x-axis. If None, the active internal
            DataFrame `_df` is used.
        bbg_format : bool, default False
            Whether to use the Bloomberg-style x-axis format for datetime indexes.
        tick_step : int, default 6
            Step used to determine the frequency of visible x-axis tick labels.
        fmt : str or None, optional
            Format string used for datetime or numeric tick labels.
        year_y_offset : float, default -0.08
            Vertical offset used for year labels when `bbg_format=True`.
        lim : tuple[float, float] or None, optional
            Optional lower and upper x-axis filter applied to the DataFrame index.
        fontsize : float, default 8
            Font size used for x-axis tick labels.
        return_dataframe : bool, default True
            Kept for API compatibility. The method returns the transformed or
            filtered DataFrame.

        Returns
        -------
        pandas.DataFrame
            DataFrame after applying the optional x-axis limits.

        Notes
        -----
        The method updates internal x-axis metadata such as `_x_axis_mode`,
        `_x_axis_fechas`, `_x_vals`, `_months`, and `_years`.
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
            self._years_xaxis(y_offset=year_y_offset, fontsize=fontsize)
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
        """
        Prepare the y-axis limits, tick labels, formatting, and spacing.

        Parameters
        ----------
        lim : tuple[float, float] or None, optional
            Lower and upper y-axis limits. If None, Matplotlib determines the limits
            automatically.
        fmt : str or None, optional
            Numeric format string used for y-axis labels. If None, `",.0f"` is used.
        fontsize : float, default 7
            Font size used for y-axis tick labels.
        tick_step : int or None, optional
            Fixed interval between y-axis ticks. If None, Matplotlib determines the
            tick spacing automatically.

        Returns
        -------
        None
            The y-axis configuration is applied directly to the active axis.
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
        Add a main title and subtitle to the active figure.

        This method places figure-level text elements instead of using the default
        axis title, allowing for a consistent institutional layout across different
        chart types.

        Parameters
        ----------
        title : str or None, optional
            Main chart title.
        title_font_size : int, default 12
            Font size of the main title.
        subtitle : str or None, optional
            Subtitle displayed below the main title.
        subtitle_font_size : int, default 9
            Font size of the subtitle.

        Returns
        -------
        None
            Title and subtitle are added directly to the active figure.
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

        The source can be provided as a single string or as a list of lines. The
        method supports up to four lines and places them in the lower section of the
        figure.

        Parameters
        ----------
        text : str, list, or None, optional
            Source text to display. If None, no source note is added.
        x : float, default 0.02
            Horizontal figure coordinate for the source text.
        y : float, default 0.022
            Vertical figure coordinate for the first source line.
        fontsize : float, default 6
            Font size of the source note.
        color : str, default "#606060"
            Text color of the source note.
        line_spacing : float, default 0.022
            Vertical spacing between source lines.

        Returns
        -------
        None
            Source text is added directly to the active figure.

        Raises
        ------
        ValueError
            If more than four source lines are provided.
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
        Add and style a legend for the active axis.

        This method combines legend handles generated by Matplotlib with optional
        custom legend handles registered through helper methods. Duplicate labels
        are removed while preserving their original order.

        Parameters
        ----------
        show : bool, default False
            Whether to display the legend.
        loc : str, default "upper left"
            Legend location.
        bbox_to_anchor : tuple or None, optional
            Optional bounding box anchor used to position the legend.
        ncol : int, default 3
            Number of legend columns.
        fontsize : int, default 7
            Legend font size.
        frameon : bool, default True
            Whether to display the legend frame.
        edgecolor : str, default "white"
            Legend frame edge color.
        facecolor : str, default "white"
            Legend frame background color.
        framealpha : float, default 0.6
            Legend frame transparency.

        Returns
        -------
        None
            The legend is added directly to the active axis when available.
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

        Returns
        -------
        None
            The active figure is displayed if it exists.
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
        Save the active figure into an in-memory PNG buffer.

        This method exports the current figure as a PNG image into a `BytesIO`
        buffer and stores it in the provided dictionary-like object using `name`
        as the key. It is useful when charts need to be passed to PowerPoint,
        reports, dashboards, or other downstream workflows without writing files
        to disk.

        Parameters
        ----------
        dir : dict, default buffers
            Dictionary-like object where the image buffer will be stored.
        name : str, default "graph_1"
            Key assigned to the saved image buffer.
        dpi : int, default 400
            Resolution used when exporting the figure.
        reset_buffers : bool, default True
            Whether to reset internal figure, axis, layout, and metadata references
            after saving.

        Returns
        -------
        None
            The image buffer is stored in `dir[name]`.

        Notes
        -----
        The Matplotlib figure is closed after being saved.
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
        color: str = "#D5D5D5",
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
        Create the base Matplotlib figure and axes layout.

        This method initializes the figure and axes used by all chart methods. It
        supports standard subplot creation as well as custom GridSpec layouts when
        height ratios, width ratios, spacing, or DPI are provided.

        Parameters
        ----------
        figsize : tuple[float, float], default (6.00, 4.80)
            Figure size in inches.
        color : str, default "#D5D5D5"
            Color of the decorative horizontal divider lines.
        lw : float, default 0.8
            Line width of the decorative figure dividers.
        nrows : int, default 1
            Number of subplot rows.
        ncols : int, default 1
            Number of subplot columns.
        sharex : bool, default False
            Whether subplots should share the x-axis.
        sharey : bool, default False
            Whether subplots should share the y-axis.
        dpi : int or None, optional
            Figure DPI. If provided, a custom GridSpec layout is used.
        height_ratios : list[float] or None, optional
            Relative height ratios for GridSpec rows.
        width_ratios : list[float] or None, optional
            Relative width ratios for GridSpec columns.
        hspace : float or None, optional
            Vertical spacing between GridSpec rows.
        wspace : float or None, optional
            Horizontal spacing between GridSpec columns.

        Returns
        -------
        None
            The figure and axes are created and stored internally.

        Notes
        -----
        The method also adds institutional-style decorative horizontal lines to the
        figure and applies default subplot spacing when no custom GridSpec settings
        are used.
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
    def horizontal_guides(self, mostrar_cero=True):
        """
        Add horizontal guide lines to the active axis.

        Parameters
        ----------
        mostrar_cero : bool, default True
            Whether to add a highlighted horizontal line at y=0.

        Returns
        -------
        None
            Grid lines are applied directly to the active axis.
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

    def tag(
        self,
        x_value: float | str | pd.Timestamp,
        y_value: float,
        label: str,
        label_h_align: str = "center",
        label_v_align: str = "center",
        ubic_etq: tuple = (0, 17),
        fontsize: int = 7,
        fontweight: str = "normal",
        font_color: str = "black",
        bg_color: str = "#ECEFF1",
        bg_alpha: float = 1.0,
        edge_color: str = "none",
        show_bbox: bool = True,
        text_edge_color: str | None = None,
        text_edge_width: float = 0.0,
        zorder: int = 6,
    ):
        """
        Add a text annotation to a specific chart coordinate.

        This method supports standard datetime, numeric, categorical, and
        Bloomberg-style x-axis modes. It can optionally display the label inside a
        rounded bounding box and apply a text stroke to improve readability.

        Parameters
        ----------
        x_value : float, str, pandas.Timestamp, or datetime-like
            X-axis value where the annotation should be placed.
        y_value : float
            Y-axis value where the annotation should be placed.
        label : str
            Text displayed in the annotation.
        label_h_align : str, default "center"
            Horizontal alignment of the annotation text.
        label_v_align : str, default "center"
            Vertical alignment of the annotation text.
        ubic_etq : tuple, default (0, 17)
            Offset in points from the annotated coordinate.
        fontsize : int, default 7
            Font size of the annotation.
        fontweight : str, default "normal"
            Font weight of the annotation.
        font_color : str, default "black"
            Text color.
        bg_color : str, default "#ECEFF1"
            Background color of the annotation box.
        bg_alpha : float, default 1.0
            Transparency of the annotation box.
        edge_color : str, default "none"
            Edge color of the annotation box.
        show_bbox : bool, default True
            Whether to display a background box behind the annotation.
        text_edge_color : str or None, optional
            Optional stroke color applied to the annotation text.
        text_edge_width : float, default 0.0
            Width of the optional text stroke.
        zorder : int, default 6
            Drawing order of the annotation.

        Returns
        -------
        None
            The annotation is added directly to the active axis.

        Raises
        ------
        RuntimeError
            If the active axis has not been initialized.
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
    
    def dot(
        self,
        x_value,
        y_value,
        color="red",
        size=30,
        zorder=5
    ):
        """
        Add a highlighted point marker to the active chart.

        This method supports standard datetime, numeric, categorical, and
        Bloomberg-style x-axis modes.

        Parameters
        ----------
        x_value : any
            X-axis value where the marker should be placed.
        y_value : float
            Y-axis value where the marker should be placed.
        color : str, default "red"
            Marker color.
        size : float, default 30
            Marker size.
        zorder : int, default 5
            Drawing order of the marker.

        Returns
        -------
        None
            The marker is added directly to the active axis.

        Raises
        ------
        RuntimeError
            If the active axis has not been initialized.
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
        Add shaded vertical regions to the active chart.

        This method highlights one or multiple x-axis periods using vertical shaded
        spans. It supports datetime, numeric, categorical, Bloomberg-style, and bar
        chart x-axis modes. For categorical bar charts in `bar_mode="last"`, the
        method can shade entire bar clusters instead of only individual x positions.

        Parameters
        ----------
        periods : tuple, list[tuple], or list[dict]
            Period or periods to shade. A simple period can be provided as
            `(start, end)`. Multiple periods can be provided as a list of tuples.
            Each period can also be a dictionary with keys such as `start`, `end`,
            `color`, `alpha`, `label`, and `hatch`.
        color : str, default "#B0B0B0"
            Default fill color of the shaded region.
        alpha : float, default 0.25
            Default transparency of the shaded region.
        zorder : int, default 0
            Drawing order of the shaded region.
        label : str or None, optional
            Optional legend label for the shaded region.
        hatch : str or None, optional
            Optional hatch pattern for the shaded region.
        ymin : float, default 0.0
            Lower vertical bound of the shaded region in axis-relative coordinates.
        ymax : float, default 1.0
            Upper vertical bound of the shaded region in axis-relative coordinates.
        clip_to_xlim : bool, default True
            Whether to clip shaded regions to the current x-axis limits.

        Returns
        -------
        None
            Shaded regions are added directly to the active axis.

        Raises
        ------
        RuntimeError
            If the active axis has not been initialized.

        Notes
        -----
        When multiple periods are provided and `label` is used, the default label is
        applied only once to avoid duplicate legend entries.
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

        Parameters
        ----------
        y_values : float, list[float], or None, optional
            Y-axis value or values where horizontal lines should be drawn. If None,
            no lines are added.
        linestyle : str or None, optional
            Matplotlib line style used for the reference lines.
        linewidth : float, default 0.5
            Width of the reference lines.
        color : str, default "gray"
            Color of the reference lines.

        Returns
        -------
        None
            Horizontal lines are added directly to the active axis.
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
        Add recession shading to a date-based chart.

        This method reads recession periods from the package's recession dataset and
        shades the corresponding date ranges on the active chart. It only works with
        date-based x-axis modes, including standard datetime axes and
        Bloomberg-style axes.

        Parameters
        ----------
        country : str, default "United States"
            Country used to filter the recession dataset.
        data_frame : bool, default False
            If True, return the recession dataset instead of plotting the shaded
            regions.
        controles : dict or None, optional
            Styling parameters passed to `shade_x`, such as `color`, `alpha`,
            `label`, or `hatch`.

        Returns
        -------
        pandas.DataFrame or None
            Returns the recession DataFrame when `data_frame=True`; otherwise,
            returns None after adding the shaded regions.

        Raises
        ------
        RuntimeError
            If no active chart exists.
        TypeError
            If the active chart does not use a date-based x-axis.
        NotImplementedError
            If the selected country is not available in the recession dataset.
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

