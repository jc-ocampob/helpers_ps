import matplotlib.font_manager as fm
import warnings
import locale
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from helper_ps.Config.var_globs import PALETA_COLORES

# -----------------------
# Setteo de parametros iniciales
# -----------------------

warnings.filterwarnings("ignore")

# Register Inter font with matplotlib


# Rebuild font cache
fm._load_fontmanager(try_read_cache=False)

locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
mpl.rcParams["axes.formatter.use_locale"] = True

# Set matplotlib theme for all graphics
plt.rcParams['font.family'] = 'Inter'
plt.rcParams['font.size'] = 9
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.titleweight'] = 'bold'

# Diccionario para guardar imágenes en memoria
buffers = {}

class Graph_base():

    # =========================
    # Internal helpers for multi-axis metadata
    # =========================
    def _get_active_ax_idx(self) -> int:
        """
        Return the index of the current active axis.
        """
        if not hasattr(self, "_axes") or self._axes is None:
            raise RuntimeError("Axes not initialized. Call plot() first.")

        if hasattr(self, "_active_ax_idx"):
            return self._active_ax_idx

        # fallback: infer from self._ax identity
        for i, ax in enumerate(self._axes):
            if ax is self._ax:
                self._active_ax_idx = i
                return i

        self._active_ax_idx = 0
        return 0

    def _ensure_axes_state(self):
        """
        Ensure per-axis state dict exists.
        """
        if not hasattr(self, "_axes_state") or self._axes_state is None:
            self._axes_state = {}

        if hasattr(self, "_axes") and self._axes is not None:
            for i in range(len(self._axes)):
                if i not in self._axes_state:
                    self._axes_state[i] = {
                        "xmeta": {"mode": None, "fechas": None},
                        "bar_meta": None,
                        "months": None,
                        "years": None,
                    }

    def _sync_active_axis_meta(self):
        """
        Sync legacy attributes with active axis metadata.
        This preserves backward compatibility with methods that still
        reference self._xmeta / self._bar_meta / self._months / self._years.
        """
        self._ensure_axes_state()
        idx = self._get_active_ax_idx()
        state = self._axes_state[idx]

        self._xmeta = state.get("xmeta", {"mode": None, "fechas": None})
        self._bar_meta = state.get("bar_meta", None)
        self._months = state.get("months", None)
        self._years = state.get("years", None)

    def _get_axis_state(self):
        """
        Return state of current active axis.
        """
        self._ensure_axes_state()
        idx = self._get_active_ax_idx()
        return self._axes_state[idx]

    def _set_bar_meta(self, bar_meta: dict | None):
        """
        Store bar metadata for the active axis only.
        """
        state = self._get_axis_state()
        state["bar_meta"] = bar_meta
        self._sync_active_axis_meta()

    def _select_df(self, df_index: int = 0):
        """
        Select dataframe when working with multiple subplots.
        """
        if self.dataframe is None:
            raise RuntimeError("No dataframe(s) provided.")

        if isinstance(self.dataframe, pd.DataFrame):
            return self.dataframe

        if df_index >= len(self.dataframe):
            raise IndexError("DataFrame index out of range.")

        return self.dataframe[df_index]
    # =========================
    # Public methods
    # =========================

    # para mostrar el grafico
    def show(self) -> None:
        """
        Si la figura existe va a mostrarlo.
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
        Guarda la figura actual en memoria
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

    def plot(
        self,
        figsize=(6.00, 4.80),
        color="#D5D5D5",
        lw=0.8,
        nrows: int = 1,
        ncols: int = 1,
        sharex: bool = False,
        sharey: bool = False
    ) -> None:
        """
        Base plot creator.

        Supports:
        - single axis (default)
        - multiple subplots

        Keeps backward compatibility with existing code.
        """

        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=figsize,
            sharex=sharex,
            sharey=sharey
        )

        self._fig = fig

        # --- Handle axes structure ---
        if isinstance(axes, np.ndarray):
            self._axes = axes.flatten().tolist()
            self._ax = self._axes[0]
        else:
            self._axes = [axes]
            self._ax = axes

        self._axes_shape = (nrows, ncols)
        self._active_ax_idx = 0

        # --- Initialize per-axis state ---
        self._axes_state = {
            i: {
                "xmeta": {"mode": None, "fechas": None},
                "bar_meta": None,
                "months": None,
                "years": None,
            }
            for i in range(len(self._axes))
        }
        self._sync_active_axis_meta()

        # --- Top & bottom lines at figure level ---
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

        self._fig.subplots_adjust(
            left=0.15,
            right=0.93,
            top=0.80,
            bottom=0.18
        )

    def set_axis(self, ax_index: int):
        """
        Select active axis when working with multiple subplots.
        """
        if not hasattr(self, "_axes") or self._axes is None:
            raise RuntimeError("Axes not initialized. Call plot() first.")

        if ax_index >= len(self._axes):
            raise IndexError("Axis index out of range.")

        self._active_ax_idx = ax_index
        self._ax = self._axes[ax_index]
        self._sync_active_axis_meta()

    def meses_y_años(self, fechas):
        """
        Store months/years for the active axis only.
        """
        mes_es = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
            5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }

        state = self._get_axis_state()
        state["months"] = [mes_es[d.month] for d in fechas]
        state["years"] = np.array([d.year for d in fechas])

        self._sync_active_axis_meta()

    def set_tick_fontsize(self, size=8):
        """
        Force font size for ALL tick labels (works even if labels were manually set).
        """
        self._tick_fontsize = size
        # --- standard tick params ---
        self._ax.tick_params(axis='x', labelsize=size)
        self._ax.tick_params(axis='y', labelsize=size)

        # --- force overwrite existing text objects ---
        for lbl in self._ax.get_xticklabels():
            lbl.set_fontsize(size)

        for lbl in self._ax.get_yticklabels():
            lbl.set_fontsize(size)

    def años_eje_x(self, y_offset=-0.08, fontsize=None, color='black'):
        """
        Add year labels for the active axis.
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

    def guias_horizontales(self, mostrar_cero=True):
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
        x_value,
        y_value,
        label,
        label_h_align="right",
        label_v_align="top",
        ubic_etq=(0, 17),
        fontsize=7,
        fontweight="bold",
        font_color="black",
        bg_color="#ECEFF1",
        bg_alpha=1.0,
        edge_color="none",
        show_bbox=True,
    ):
        """
        Adds a label at (x_value, y_value), handling any x type and
        allowing full control of styling.
        """

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("Axis not initialized.")

        # always sync current axis metadata before using
        self._sync_active_axis_meta()

        mode = getattr(self, "_xmeta", {}).get("mode", None)

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
        self._ax.annotate(
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
            zorder=6
        )

    def add_source(
        self,
        text="Source: ...",
        x=0.02,
        y=0.022,
        fontsize=6,
        color="#606060",
        line_spacing=0.022,
    ):
        """
        Add source text at the bottom.

        Supports:
        - string -> single line
        - list[str] -> multiple lines
        """

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

    def set_titles(
        self,
        title: str | None = None,
        title_font_size: int = 12,
        subtitle: str | None = None,
        subtitle_font_size: int = 9
    ) -> None:
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

    def _set_xmeta(self, mode: str, fechas=None):
        """
        Store x-axis metadata for active axis only.
        mode: 'bbg' | 'datetime' | 'numeric' | 'categorical'
        fechas: only for bbg mode (pd.Index of timestamps)
        """
        state = self._get_axis_state()
        state["xmeta"] = {
            "mode": mode,
            "fechas": fechas
        }
        self._sync_active_axis_meta()

    def _coerce_to_bbg_x(self, x):
        """
        Convert a user x (date/str/int) to bbg integer x-position.
        Uses metadata of the active axis.
        """
        self._sync_active_axis_meta()

        fechas = self._xmeta.get("fechas", None)
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

    def shade_x_periods(
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
        Shade vertical regions on the active axis.

        Compatible with:
        - line charts
        - bar charts (time-series and snapshot)
        - BBG format
        - datetime / numeric / categorical axes

        periods:
        - tuple(start, end)
        - list of tuples [(start, end), ...]
        - list of dicts with full control
        """

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("No axis found. Call graph_line/graph_bar first.")

        self._sync_active_axis_meta()

        if isinstance(periods, tuple) and len(periods) == 2:
            periods = [periods]

        mode = getattr(self, "_xmeta", {}).get("mode", None)
        bar_meta = getattr(self, "_bar_meta", None)

        used_label = False
        xlim = self._ax.get_xlim()

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

            elif bar_meta is not None and bar_meta.get("mode") == "last":
                xticklabels = [t.get_text() for t in self._ax.get_xticklabels()]

                def _to_pos(val):
                    if isinstance(val, str):
                        if val not in xticklabels:
                            raise ValueError(f"{val} not found in x labels")
                        return xticklabels.index(val)
                    return float(val)

                x0 = float(_to_pos(start))
                x1 = float(_to_pos(end))

                width = bar_meta.get("width", 0.8)
                x0 -= width / 2
                x1 += width / 2

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
                    if bar_meta is not None and bar_meta.get("mode") == "time":
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

@dataclass
class Graph_mtplt(Graph_base):
    
    dataframe: pd.DataFrame | list[pd.DataFrame] = None

    def graph_line(
        self,
        # --- Configuración del grafico ---
        figsize: tuple[float, float] = (6.00, 5.00),                        # Tamaño del grafico configuración general es (6,4.8) --> tamaño estandard

        # --- Configuración de los elementos adicionales del grafico ---
        title: str | None = None,                                           # titulo de la grafica
        subtitle: str | None = None,                                        # Subtitulo de la grafica
        source: str | None = None,                                          # Fuente de datos del grafico

        # --- Configuración de df -----
        df_index: int = 0,                                                  # índice del dataframe a usar (en caso de tener varios)

        # --- Configuración de las series ---
        tickers: list[str] | str = "all",                                   # tickers en evaluación del dataframe
        labels: list[str] | str | None = None,                              # etiquetas de los tickers en el orden dado, sino defaultea a los tickers
        colors: list["str"] | str = PALETA_COLORES,                         # Lista de colors para cada uno de los tickers en evaluación
        lw: float=1.6,                                                      # grosor de línea
        show_dot: list[str] | None | str = None,                            # controla bolita si str = "all" se asigna bolita para todas las series si None para ninguna y si es una lista pasar tickers a cuales aplicar
        
        # --- Configuración de etiqueta de último valor ---
        show_tag: list[str] | None | str = None,                            # controla etiqueta si str = "all" se asigna etiqueta para todas las series si None para ninguna y si es una lista pasar tickers a cuales aplicar
        tag_template: str = "{ticker}\n{x_value:%B-%Y}: {y_value:,.2f}",    # plantilla para poder generar la etiqueta tiene a disposición {ticker}, {x_value} y {y_value} para formatear a gusto
        tag_loc: tuple[int, int] = (0, 17),                                 # (x_offset, y_offset) para la etiqueta del último value
        tag_bg_color: str = "#F7F7F7",                                  # color de fondo de la etiqueta

        # --- Configuración del eje y ---
        y_lim: tuple[float, float] | tuple[int, int] | None = None,         # Limites del eje y (min, max)
        y_fmt: str = ",.2f",                                                # formato para eje y (ej: ",.2f" para mostrar con 2 decimales y separador de miles)

        # --- Configuración del eje x ---
        x_lim: tuple[float, float] | tuple[int, int] | None = None,         # limites del eje x
        x_tick_step: int = 6,                                               # cada cuántos meses mostrar etiqueta en el eje X
        bbg_format: bool = False,                                           # meses arriba y año abajo (eje X numérico)
        x_fmt: str | None = None,                                           # formato para eje x (ej: "%b-%y" para mostrar mes-año en caso de eje datetime
        year_y_offset: float = -0.08,                                       # offset del año debajo del eje

        # --- Configuración Leyenda---
        show_legend: bool | None = None,                                    # None = auto (solo si hay >1 serie y labels)

        # --- Configuración de otros factores ---
        hlines: float | list[float]| None = None,                           # agregar lineas horizontales en el grafico
        show_hguide: bool = False,                                          # Incluye las lineas de guia horizontales   
    ) -> None:
        
        # --- Normaliza tickers a lista ---
        if isinstance(tickers, str):
            if tickers == "all":
                tickers = self.dataframe.columns.tolist()
            else:
                tickers = [tickers]
        
        # --- acortar la muestra del data frame ---
        db = self._select_df(df_index=df_index)

        # --- Corta ventana temporal si aplica (ANTES de preparar eje X) ---
        if x_lim is not None and isinstance(x_lim, tuple):
            start_value_x, end_value_x = x_lim
            if start_value_x is not None:
                db = db[db.index >= start_value_x].copy()
            if end_value_x is not None:
                db = db[db.index <= end_value_x].copy()

        # --- Levantar que no hay información ---
        if db.empty:
            raise ValueError("No hay datos para mostrar en el gráfico. Verifique los tickers y el rango de fechas.")

        # --- Normaliza labels a lista (si viene string) ---
        if isinstance(labels, str):
            labels = [labels]
        elif isinstance(labels, list):
            if len(labels) < len(db.columns.tolist()):
                add = db.columns.tolist()
                add = add[len(labels):]
                labels = labels + add
        else:
            labels = db.columns.tolist()

        # --- Figura base: tamaño configurable ---
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        self._set_bar_meta(None)
        self.set_titles(title=title, subtitle=subtitle)



        # --- Agrega titulos y subtitulos ---
        self.set_titles(title=title, subtitle=subtitle)

        # --- Preparar eje X ---
        fechas = None
        x_vals = None

        x_index = db.index

        is_datetime = pd.api.types.is_datetime64_any_dtype(x_index)
        is_numeric = pd.api.types.is_numeric_dtype(x_index)
      
        # --- Preparar eje X: Formato Bloomberg ---
        if bbg_format and is_datetime:

            fechas = pd.Index(db.index.sort_values().unique())
            x_vals = np.arange(len(fechas))

            self.meses_y_años(fechas)

            month_change = pd.Series(fechas).dt.to_period("M").ne(
                pd.Series(fechas).dt.to_period("M").shift()
            )
            month_idx = np.where(month_change)[0]

            tick_idx = month_idx[::x_tick_step]

            self._ax.set_xticks(tick_idx)
            self._ax.set_xticklabels([self._months[i] for i in tick_idx])

            self.años_eje_x(y_offset=year_y_offset)
            self._set_xmeta(mode="bbg", fechas=fechas)

        # --- Preparar eje X: Formato datetime clasico ---
        elif is_datetime:

            x_axis_format = x_fmt if x_fmt is not None else "%b-%y"

            locator = mdates.MonthLocator(interval=x_tick_step)
            formatter = mdates.DateFormatter(x_axis_format)

            self._ax.xaxis.set_major_locator(locator)
            self._ax.xaxis.set_major_formatter(formatter)
            self._ax.tick_params(axis='x', labelsize=9)
            self._set_xmeta(mode="datetime")

        # --- Preparar eje X: Formato numerico ---
        elif is_numeric:

            x_axis_format = x_fmt if x_fmt is not None else ",.0f"

            x_vals = db.index.values

            # sample ticks every N observations
            tick_idx = np.arange(0, len(x_vals), x_tick_step)

            self._ax.set_xticks(x_vals[tick_idx])

            # formatting (optional)
            self._ax.set_xticklabels(
                [f"{x_vals[i]:{x_axis_format}}" for i in tick_idx],  # adjust format if needed
                fontsize=9
            )

            self._ax.tick_params(axis='x', labelsize=9)
            self._set_xmeta(mode="numeric")

        # --- Preparar eje X: Fall back ---
        else:
            self._ax.tick_params(axis='x', labelsize=9)
            self._set_xmeta(mode="categorical")

        # --- Series + captura del último punto ---
        list_last_point = []

        for i, t in enumerate(tickers):
            last_point = None
            s = db[[t]].copy()

            if s.empty:
                continue

            lab = labels[i] if labels is not None and i < len(labels) else None
            col = colors[i] if colors is not None and i < len(colors) else "#2F71E5"

            if bbg_format:
                # Alinear series al calendario común
                serie = s.reindex(fechas)[t]
                self._ax.plot(x_vals, serie.to_numpy(), color=col, lw=lw, label=lab)

                # Guardar último valor válido si vamos a mostrar bolita o etiqueta
                valid = serie.dropna()
                fecha_last = valid.index[-1]
                valor_last = float(valid.iloc[-1])
                x_last = int(np.where(fechas == fecha_last)[0][-1])
                last_point = (x_last, valor_last, t , col, fecha_last)

            else:
                self._ax.plot(s.index, s[t], color=col, lw=lw, label=lab)
                last_point = (s.index[-1], float(s[t].iloc[-1]), t, col, s.index[-1])
            
            list_last_point.append(last_point)

            # Colocación de la bolita si es que califica
            if show_dot is not None:
                if "all" in str(show_dot) or t in str(show_dot):
                    x_or_fecha_last, y_last, ticker, c_last, fecha_real = last_point
                    self._ax.scatter(x_or_fecha_last, y_last, color=c_last, s=22, zorder=5)
                

        # -- Agregar lineas horizontales de ser necesario ---
        if isinstance(hlines, float) and hlines is not None:
            self._ax.axhline(hlines, color="gray", linestyle="--", linewidth=0.8)
        elif isinstance(hlines, list) and hlines is not None:
            for i in hlines:
                self._ax.axhline(i, color="gray", linestyle="--", linewidth=0.8)
        
        # -- Mostrar las lineas de guía ---
        if show_hguide:
            self.guias_horizontales(mostrar_cero=False)
            
        # --- Configuración del limite y ---
        if y_lim is not None:
            self._ax.set_ylim(*y_lim)
        self._ax.margins(x=0.01)

        # --- Configuración del limite y ---
        self.set_tick_fontsize(size=8)

        # --- Controla la muestra de etiquetas
        for i, punto in enumerate(list_last_point):
            x_or_fecha_last, y_last, ticker, c_last, fecha_real = punto

            if i < len(labels):
                ticker = labels[i]

            # Etiqueta (solo si quieres)
            if show_tag is not None and ("all" in str(show_tag) or ticker in str(show_tag)):
                self.etiqueta_valor(
                    label=tag_template.format(x_value=fecha_real, y_value=y_last, ticker=ticker),
                    x_value=x_or_fecha_last,          # datetime real para texto "Mar 26: 4.3"
                    y_value=y_last,
                    ubic_etq=tag_loc,
                    bg_color=tag_bg_color,
                    font_color=c_last
                    )
                
        # Agregar format al eje y
        self._ax.yaxis.set_major_formatter(
            FuncFormatter(lambda x, pos: f"{x:{y_fmt}}")
        )

        # --- Leyenda: auto o forzada ---
        if show_legend is None:
            show_legend = (labels is not None and len(tickers) > 1)

        if show_legend:
            self._ax.legend(
                loc="upper left",
                fontsize=8,
                frameon=True,
                edgecolor="white",
                facecolor="white",
                framealpha=0.6
            )
        
        
        # layout
        if bbg_format:
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

        # source
        if source:
            self.add_source(source)

    def graph_bar(
        self,
        # --- Configuración del grafico ---
        figsize: tuple[float, float] = (6.00, 5.00),                        # Tamaño del grafico configuración general es (6,4.8) --> tamaño estandard

        # --- Configuración de los elementos adicionales del grafico ---
        title: str | None = None,                                           # titulo de la grafica
        subtitle: str | None = None,                                        # Subtitulo de la grafica
        source: str | None = None,                                          # Fuente de datos del grafico
        
        # --- Configuración de df -----
        df_index: int = 0,                      # índice del dataframe a usar (en caso de tener varios)

        # --- Configuración de las series ---
        tickers: list[str] | str = "all",                                   # tickers en evaluación del dataframe
        labels: list[str] | str | None = None,                              # etiquetas de los tickers en el orden dado, sino defaultea a los tickers
        colors: list["str"] | str = PALETA_COLORES,                         # Lista de colors para cada uno de los tickers en evaluación

        # --- Configuración del eje y ---
        y_lim: tuple[float, float] | tuple[int, int] | None = None,         # Limites del eje y (min, max)
        y_fmt: str = ",.2f",                                                # formato para eje y (ej: ",.2f" para mostrar con 2 decimales y separador de miles)

        transformations=None,

        # --- Configuración de las barras ---
        bar_mode: str = "auto",                                             # "auto" | "time" | "last"
        stacked: bool = False,                                               # for time mode when multiple tickers
        grouped: bool = False,                                              # alternative to stacked in time mode (multiple tickers)
        bar_width: float = 0.8,                                             # category width (bbg/numeric/categorical). For datetime grouped we compute internally.
        alpha: float = 0.95,

        # --- x-axis options (time mode) ---
        bbg_format: bool = False,
        x_tick_step: int = 6,
        year_y_offset: float = -0.08,
        x_fmt: str | None = None,        # datetime formatter (e.g. "%b-%y")

        # --- y-axis + annotations ---
        show_values: bool = False,
        value_fmt: str = ",.2f",
        value_fontsize: int = 7,

        # --- guides/legend ---
        hlines: float | list[float] | None = None,
        show_hguide: bool = False,
        show_legend: bool | None = None,
    ):
        # -----------------------
        # 1) Normalize inputs
        # -----------------------
        if isinstance(tickers, str):
            if tickers == "all":
                tickers = self.dataframe.columns.tolist()
            else:
                tickers = [tickers]

        db = self._select_df(df_index=df_index)

        if isinstance(labels, str):
            if labels == "default":
                labels = db.columns.tolist()
            else:
                labels = [labels]
        elif isinstance(labels, list):
            if len(labels) < len(db.columns.tolist()):
                labels = labels + db.columns.tolist()[len(labels):]

        # Decide mode automatically
        if bar_mode == "auto":
            if len(tickers) == 1:
                bar_mode = "time"
            else:
                # if user explicitly wants grouped/stacked, assume time comparison
                bar_mode = "time" if (grouped or stacked) else "last"


        # Figure size + titles (keeps your styling)
        
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        self.set_titles(title=title, subtitle=subtitle)

        # Normalize colors
        cols = colors if isinstance(colors, list) else [colors] * len(tickers)
        cols = [cols[i] if i < len(cols) else "#2F71E5" for i in range(len(tickers))]

        # Helper: apply transformation (supports series or scalar)
        def _apply_transform(ticker, series_or_value):
            if transformations is None or ticker not in transformations:
                return series_or_value
            fn = transformations[ticker]
            if not callable(fn):
                return series_or_value
            try:
                return fn(series_or_value)
            except Exception:
                # If fn expects a Series and received scalar, wrap it
                if np.isscalar(series_or_value):
                    return float(fn(pd.Series([series_or_value])).iloc[0])
                return series_or_value

        # -----------------------
        # 2) MODE: LAST (snapshot / categorical matrix)
        # -----------------------
        if bar_mode == "last":
            # In "last" mode, the dataframe is treated as an already prepared
            # snapshot table:
            #   - rows/index   -> categories on x-axis
            #   - columns      -> series inside each category
            #
            # Example:
            #           TickerA   TickerB   TickerC
            # Mar-2024   10        20        30
            # Apr-2024   12        18        35
            # May-2024   15        22        31
            #
            # grouped=True, stacked=False  -> 3 categories, 3 bars per category
            # stacked=True                 -> 3 stacked bars (one per category)

            cats = db.index.tolist()
            x = np.arange(len(cats), dtype=float)
            m = len(tickers)

            # build matrix: rows=categories, cols=tickers
            vals_matrix = np.zeros((len(db.index), m), dtype=float)

            for i, t in enumerate(tickers):
                serie = db[t].copy()
                serie = _apply_transform(t, serie)
                vals_matrix[:, i] = np.asarray(serie.values, dtype=float)

            xt = [str(c) for c in cats]
            legend_labels = labels if labels is not None else tickers

            # ---------------------------------
            # A) GROUPED
            # ---------------------------------
            if grouped and not stacked:
                width = min(bar_width / max(m, 1), 0.8 / max(m, 1))

                for i, t in enumerate(tickers):
                    offset = (i - (m - 1) / 2) * width
                    y = vals_matrix[:, i]

                    bars = self._ax.bar(
                        x + offset,
                        y,
                        width=width,
                        color=cols[i],
                        alpha=alpha,
                        label=legend_labels[i],
                        zorder=3
                    )

                    if show_values:
                        for rect, v in zip(bars, y):
                            if np.isnan(v):
                                continue
                            if v >= 0:
                                xytext = (0, 3)
                                va = "bottom"
                                y_anchor = rect.get_height()
                            else:
                                xytext = (0, -3)
                                va = "top"
                                y_anchor = rect.get_height()

                            self._ax.annotate(
                                f"{v:{value_fmt}}",
                                xy=(rect.get_x() + rect.get_width() / 2, y_anchor),
                                xytext=xytext,
                                textcoords="offset points",
                                ha="center",
                                va=va,
                                fontsize=value_fontsize,
                                fontweight="bold",
                                color="#222222",
                                zorder=6
                            )

                self._ax.set_xticks(x)
                self._ax.set_xticklabels(xt, fontsize=9)

                if len(x) > 8:
                    for lab in self._ax.get_xticklabels():
                        lab.set_rotation(45)
                        lab.set_ha("right")

                self._set_xmeta(mode="categorical")

                if show_legend is None:
                    show_legend = (m > 1)

            # ---------------------------------
            # B) STACKED
            # ---------------------------------
            elif stacked:
                bottom_pos = np.zeros(len(x), dtype=float)
                bottom_neg = np.zeros(len(x), dtype=float)

                for i, t in enumerate(tickers):
                    y = vals_matrix[:, i]

                    y_pos = np.where(np.isnan(y), 0.0, np.where(y > 0, y, 0.0))
                    y_neg = np.where(np.isnan(y), 0.0, np.where(y < 0, y, 0.0))

                    if np.any(y_pos != 0):
                        self._ax.bar(
                            x,
                            y_pos,
                            width=min(bar_width, 0.85),
                            bottom=bottom_pos,
                            color=cols[i],
                            alpha=alpha,
                            label=legend_labels[i],
                            zorder=3
                        )
                        bottom_pos = bottom_pos + y_pos

                    if np.any(y_neg != 0):
                        # only add legend once
                        self._ax.bar(
                            x,
                            y_neg,
                            width=min(bar_width, 0.85),
                            bottom=bottom_neg,
                            color=cols[i],
                            alpha=alpha,
                            zorder=3
                        )
                        bottom_neg = bottom_neg + y_neg

                self._ax.set_xticks(x)
                self._ax.set_xticklabels(xt, fontsize=9)

                if len(x) > 8:
                    for lab in self._ax.get_xticklabels():
                        lab.set_rotation(45)
                        lab.set_ha("right")

                if show_values:
                    totals = np.nansum(vals_matrix, axis=1)
                    for xi, total, top_pos, bot_neg in zip(x, totals, bottom_pos, bottom_neg):
                        if np.isnan(total):
                            continue

                        if total >= 0:
                            y_anchor = top_pos
                            xytext = (0, 3)
                            va = "bottom"
                        else:
                            y_anchor = bot_neg
                            xytext = (0, -3)
                            va = "top"

                        self._ax.annotate(
                            f"{total:{value_fmt}}",
                            xy=(xi, y_anchor),
                            xytext=xytext,
                            textcoords="offset points",
                            ha="center",
                            va=va,
                            fontsize=value_fontsize,
                            fontweight="bold",
                            color="#222222",
                            zorder=6
                        )

                self._set_xmeta(mode="categorical")

                if show_legend is None:
                    show_legend = (m > 1)

            # ---------------------------------
            # C) DEFAULT (one bar per category using first ticker)
            # ---------------------------------
            else:
                # if neither grouped nor stacked, use first ticker only
                y = vals_matrix[:, 0]

                bars = self._ax.bar(
                    x,
                    y,
                    color=cols[0],
                    alpha=alpha,
                    width=min(bar_width, 0.85),
                    zorder=3,
                    label=legend_labels[0]
                )

                self._ax.set_xticks(x)
                self._ax.set_xticklabels(xt, fontsize=9)

                if len(x) > 8:
                    for lab in self._ax.get_xticklabels():
                        lab.set_rotation(45)
                        lab.set_ha("right")

                if show_values:
                    for rect, v in zip(bars, y):
                        if np.isnan(v):
                            continue
                        if v >= 0:
                            xytext = (0, 3)
                            va = "bottom"
                            y_anchor = rect.get_height()
                        else:
                            xytext = (0, -3)
                            va = "top"
                            y_anchor = rect.get_height()

                        self._ax.annotate(
                            f"{v:{value_fmt}}",
                            xy=(rect.get_x() + rect.get_width()/2, y_anchor),
                            xytext=xytext,
                            textcoords="offset points",
                            ha="center",
                            va=va,
                            fontsize=value_fontsize,
                            fontweight="bold",
                            color="#222222",
                            zorder=6
                        )

                self._set_xmeta(mode="categorical")

                if show_legend is None:
                    show_legend = False


        # -----------------------
        # 3) MODE: TIME (time-series)
        # -----------------------
        elif bar_mode == "time":
            x_index = db.index
            is_datetime = pd.api.types.is_datetime64_any_dtype(x_index)
            is_numeric = pd.api.types.is_numeric_dtype(x_index)

            fechas = None
            x_vals = None

            # --- Prepare x-axis (mirrors your line chart) ---
            if bbg_format and not db.empty:
                fechas = pd.Index(db.index.sort_values().unique())
                x_vals = np.arange(len(fechas))
                self.meses_y_años(fechas)

                month_change = pd.Series(fechas).dt.to_period("M").ne(
                    pd.Series(fechas).dt.to_period("M").shift()
                )
                month_idx = np.where(month_change)[0]
                tick_idx = month_idx[::x_tick_step]

                self._ax.set_xticks(tick_idx)
                self._ax.set_xticklabels([self._months[i] for i in tick_idx])
                self.años_eje_x(y_offset=year_y_offset)

                self._set_xmeta(mode="bbg", fechas=fechas)

            elif is_datetime and not db.empty:
                x_axis_format = x_fmt if x_fmt is not None else "%b-%y"
                locator = mdates.MonthLocator(interval=x_tick_step)
                formatter = mdates.DateFormatter(x_axis_format)
                self._ax.xaxis.set_major_locator(locator)
                self._ax.xaxis.set_major_formatter(formatter)
                self._ax.tick_params(axis="x", labelsize=9)
                self._set_xmeta(mode="datetime")

            elif is_numeric and not db.empty:
                x_axis_format = x_fmt if x_fmt is not None else ",.0f"
                x_vals = db.index.values
                tick_idx = np.arange(0, len(x_vals), x_tick_step)
                self._ax.set_xticks(x_vals[tick_idx])
                self._ax.set_xticklabels([f"{x_vals[i]:{x_axis_format}}" for i in tick_idx], fontsize=9)
                self._ax.tick_params(axis="x", labelsize=9)
                self._set_xmeta(mode="numeric")

            else:
                self._ax.tick_params(axis="x", labelsize=9)
                self._set_xmeta(mode="categorical")

            # --- Plot logic ---
            # If multiple tickers:
            # - default stacked=True (clean + robust)
            # - grouped=True for grouped bars (bbg or numeric; datetime also supported via date2num)
            m = len(tickers)

            if bbg_format:
                # align to common calendar
                fechas = pd.Index(db.index.sort_values().unique())
                x_vals = np.arange(len(fechas))

                if m > 1 and grouped and not stacked:
                    width = min(bar_width / m, 0.8 / m)
                    base = x_vals.astype(float)
                    for i, t in enumerate(tickers):
                        serie = db[t].reindex(fechas)
                        serie = _apply_transform(t, serie)
                        offset = (i - (m - 1) / 2) * width
                        self._ax.bar(
                            base + offset,
                            np.asarray(serie),
                            width=width,
                            color=cols[i],
                            alpha=alpha,
                            label=(labels[i] if labels is not None else t),
                            zorder=3
                        )
                else:
                    bottom = np.zeros(len(fechas), dtype=float)
                    for i, t in enumerate(tickers):
                        serie = db[t].reindex(fechas)
                        serie = _apply_transform(t, serie)
                        y = np.asarray(serie, dtype=float)
                        self._ax.bar(
                            x_vals,
                            y,
                            width=min(bar_width, 0.85),
                            bottom=bottom,
                            color=cols[i],
                            alpha=alpha,
                            label=(labels[i] if labels is not None else t),
                            zorder=3
                        )
                        bottom = np.nan_to_num(bottom) + np.nan_to_num(y)

                    if show_values:
                        totals = bottom
                        for xi, total in zip(x_vals, totals):
                            if np.isnan(total):
                                continue
                            self._ax.annotate(
                                f"{total:{value_fmt}}",
                                xy=(xi, total),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha="center",
                                va="bottom",
                                fontsize=value_fontsize,
                                fontweight="bold",
                                color="#222222",
                                zorder=6
                            )

            else:
                # Non-BBG
                if m == 1:
                    t = tickers[0]
                    serie = _apply_transform(t, db[t])

                    bars = self._ax.bar(
                        serie.index,
                        serie.values,
                        width=min(bar_width, 0.85),
                        color=cols[0],
                        alpha=alpha,
                        zorder=3,
                        label=(labels[0] if labels is not None else t),
                    )

                    if show_values:
                        for rect in bars:
                            h = rect.get_height()
                            if np.isnan(h):
                                continue
                            self._ax.annotate(
                                f"{h:{value_fmt}}",
                                xy=(rect.get_x() + rect.get_width()/2, h),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha="center",
                                va="bottom",
                                fontsize=value_fontsize,
                                fontweight="bold",
                                color="#222222",
                                zorder=6
                            )
                else:
                    # multiple tickers over time
                    if grouped and not stacked and is_datetime:
                        # grouped bars on datetime: convert to date numbers
                        x_num = mdates.date2num(pd.to_datetime(db.index).to_pydatetime())

                        # estimate spacing in "days" for reasonable bar widths
                        diffs = np.diff(np.sort(np.unique(x_num)))
                        base_step = np.median(diffs) if len(diffs) else 30.0
                        group_total = base_step * 0.8
                        width = group_total / m

                        for i, t in enumerate(tickers):
                            serie = _apply_transform(t, db[t])
                            offset = (i - (m - 1) / 2) * width
                            self._ax.bar(
                                x_num + offset,
                                np.asarray(serie.values, dtype=float),
                                width=width,
                                color=cols[i],
                                alpha=alpha,
                                label=(labels[i] if labels is not None else t),
                                zorder=3
                            )
                        self._ax.xaxis_date()

                    elif grouped and not stacked and is_numeric:
                        x = np.asarray(db.index.values, dtype=float)
                        # numeric spacing
                        diffs = np.diff(np.sort(np.unique(x)))
                        base_step = np.median(diffs) if len(diffs) else 1.0
                        group_total = base_step * 0.8
                        width = group_total / m

                        for i, t in enumerate(tickers):
                            serie = _apply_transform(t, db[t])
                            offset = (i - (m - 1) / 2) * width
                            self._ax.bar(
                                x + offset,
                                np.asarray(serie.values, dtype=float),
                                width=width,
                                color=cols[i],
                                alpha=alpha,
                                label=(labels[i] if labels is not None else t),
                                zorder=3
                            )
                    else:
                        # default stacked (robust)
                        bottom = np.zeros(len(db.index), dtype=float)
                        for i, t in enumerate(tickers):
                            serie = _apply_transform(t, db[t])
                            y = np.asarray(serie.values, dtype=float)
                            self._ax.bar(
                                db.index,
                                y,
                                width=min(bar_width, 0.85),
                                bottom=bottom,
                                color=cols[i],
                                alpha=alpha,
                                label=(labels[i] if labels is not None else t),
                                zorder=3
                            )
                            bottom = np.nan_to_num(bottom) + np.nan_to_num(y)

                        if show_values:
                            totals = bottom
                            for x_i, total in zip(db.index, totals):
                                if np.isnan(total):
                                    continue
                                self._ax.annotate(
                                    f"{total:{value_fmt}}",
                                    xy=(x_i, total),
                                    xytext=(0, 3),
                                    textcoords="offset points",
                                    ha="center",
                                    va="bottom",
                                    fontsize=value_fontsize,
                                    fontweight="bold",
                                    color="#222222",
                                    zorder=6
                                )

            if show_legend is None:
                show_legend = (labels is not None and len(tickers) > 1)

        else:
            raise ValueError("bar_mode must be one of: 'auto', 'time', 'last'")

        # -----------------------
        # 4) Shared styling blocks
        # -----------------------
        # Horizontal lines
        if isinstance(hlines, (float, int)) and hlines is not None:
            self._ax.axhline(float(hlines), color="gray", linestyle="--", linewidth=0.8)
        elif isinstance(hlines, list) and hlines is not None:
            for h in hlines:
                self._ax.axhline(float(h), color="gray", linestyle="--", linewidth=0.8)

        if show_hguide:
            self.guias_horizontales(mostrar_cero=False)

        # Y format + limits
        if y_lim is not None:
            self._ax.set_ylim(*y_lim)

        self._ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:{y_fmt}}"))
        self._ax.margins(x=0.01)
        self.set_tick_fontsize(size=8)

        # Legend (same style as line)
        if show_legend:
            self._ax.legend(
                loc="upper left",
                fontsize=8,
                frameon=True,
                edgecolor="white",
                facecolor="white",
                framealpha=0.6
            )

        # Layout (same logic as line)
        if bar_mode == "time" and bbg_format:
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


        if isinstance(source, str):
            self.add_source(source, color="#454444")
        elif isinstance(source, list) and len(source) > 1:
            self.add_source(source, fontsize=5, color="#454444")
        elif isinstance(source, list) and len(source) <= 1:
            self.add_source(source, color="#454444")
        
        self._set_bar_meta({
            "mode": bar_mode,
            "width": bar_width
        })

    def graph_box_whiskers(
        self,
        # --- Configuración del gráfico ---
        figsize: tuple[float, float] = (6.00, 5.00),

        # --- Configuración de elementos adicionales ---
        title: str | None = None,
        subtitle: str | None = None,
        source: str | list[str] | None = None,

        # --- Configuración de df -----
        df_index: int = 0,                      # índice del dataframe a usar (en caso de tener varios)

        # --- Configuración de series ---
        tickers: list[str] | str = "all",
        labels: list[str] | str | None = None,
        colors: list[str] | str = PALETA_COLORES,

        # --- Configuración del boxplot ---
        whis=(0, 100),                    # full range by default
        show_fliers: bool = False,
        show_means: bool = False,
        meanline: bool = False,
        widths: float | list[float] = 0.6,
        notch: bool = False,
        vert: bool = True,

        # --- Styling de elementos internos ---
        box_face_alpha: float = 0.85,
        median_color: str = "#222222",
        median_lw: float = 1.5,
        whisker_color: str = "#6E6E6E",
        whisker_lw: float = 1.0,
        cap_color: str = "#6E6E6E",
        cap_lw: float = 1.0,
        box_edge_color: str = "#6E6E6E",
        box_edge_lw: float = 1.0,
        flier_marker: str = "o",
        flier_markersize: float = 3.5,
        flier_markerfacecolor: str = "#999999",
        flier_markeredgecolor: str = "#999999",

        # --- Configuración del eje y ---
        y_lim: tuple[float, float] | tuple[int, int] | None = None,
        y_fmt: str = ",.2f",

        # --- Configuración del eje x ---
        x_label_rotation: float = 0,
        x_label_ha: str = "center",

        # --- Opcionales estadísticos ---
        show_stats: bool = False,
        stats: str = "median",            # "median" | "count"
        stats_fmt: str = ",.2f",
        stats_fontsize: int = 7,
        stats_color: str = "#222222",
        stats_offset: tuple[int, int] = (0, 5),

        # --- NUEVO: etiquetas de rango (whiskers) ---
        show_range_tags: bool = False,
        range_tag_fmt: str = ",.2f",
        range_tag_fontsize: int = 7,
        range_tag_color: str = "#4A4A4A",
        range_tag_bg_color: str = "#F7F7F7",
        range_tag_edge_color: str = "none",
        range_tag_alpha: float = 1.0,
        range_tag_show_high: bool = True,
        range_tag_show_low: bool = True,
        range_tag_offset_high: tuple[int, int] = (0, 4),
        range_tag_offset_low: tuple[int, int] = (0, -4),

        # --- NUEVO: último valor de la serie ---
        show_last_value: bool = False,
        last_value_mode: str = "dot",     # "dot" | "tag" | "dot_tag"
        last_value_marker: str = "o",
        last_value_marker_size: float = 26,
        last_value_edge_color: str = "white",
        last_value_edge_width: float = 0.6,
        last_value_alpha: float = 1.0,
        last_value_use_series_color: bool = True,
        last_value_color: str = "#111111",
        last_value_label_fmt: str = "{value:,.2f}",
        last_value_fontsize: int = 7,
        last_value_fontweight: str = "bold",
        last_value_bg_color: str = "#ECEFF1",
        last_value_edgecolor: str = "none",
        last_value_loc: tuple[int, int] = (0, 10),

        
        show_last_value_legend: bool = True,
        last_value_legend_label: str = "Last value",
        last_value_legend_loc: str = "upper right",
        last_value_legend_fontsize: int = 8,
        last_value_legend_frameon: bool = False,
        last_value_legend_color: str | None = None,


        # --- Configuración de otros factores ---
        x_lim: tuple[pd.Timestamp | str | None, pd.Timestamp | str | None] | None = None,
        hlines: float | list[float] | None = None,
        show_hguide: bool = False,
    ):
        """
        Grafica box & whiskers por columna.

        Supuesto principal:
        - dataframe.index = fechas
        - dataframe.columns = series (ej. múltiplos P/E)

        Cada caja resume la distribución histórica de una columna.

        Nuevas opciones:
        - show_range_tags: muestra etiquetas en el whisker superior/inferior
        - show_last_value: muestra el último valor histórico de cada serie
        """

        # -----------------------
        # 1) Normalize inputs
        # -----------------------
        if isinstance(tickers, str):
            if tickers == "all":
                tickers = self.dataframe.columns.tolist()
            else:
                tickers = [tickers]

        db = self._select_df(df_index=df_index)

        # Recorte temporal usando index (fechas)
        if x_lim is not None and isinstance(x_lim, tuple):
            start_value_x, end_value_x = x_lim

            if start_value_x is not None:
                start_value_x = pd.to_datetime(start_value_x)
                db = db[db.index >= start_value_x].copy()

            if end_value_x is not None:
                end_value_x = pd.to_datetime(end_value_x)
                db = db[db.index <= end_value_x].copy()

        if db.empty:
            raise ValueError("No hay datos para mostrar en el gráfico. Verifique los tickers y el rango de fechas.")

        # eliminar columnas completamente vacías dentro de la ventana
        valid_tickers = [c for c in db.columns if db[c].dropna().shape[0] > 0]
        if len(valid_tickers) == 0:
            raise ValueError("Todas las series están vacías después de aplicar el filtro.")

        db = db[valid_tickers]
        tickers = valid_tickers

        # labels
        if isinstance(labels, str):
            labels = [labels]
        elif isinstance(labels, list):
            if len(labels) < len(tickers):
                labels = labels + tickers[len(labels):]
        else:
            labels = tickers.copy()

        # colors
        cols = colors if isinstance(colors, list) else [colors] * len(tickers)
        cols = [cols[i] if i < len(cols) else "#2F71E5" for i in range(len(tickers))]

        # -----------------------
        # 2) Base figure format
        # -----------------------
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        self._set_bar_meta(None)
        self.set_titles(title=title, subtitle=subtitle)
        self._set_xmeta(mode="categorical")


        self.set_titles(title=title, subtitle=subtitle)
        self._set_xmeta(mode="categorical")

        # -----------------------
        # 3) Prepare data
        # -----------------------
        data_plot = [db[t].dropna().values for t in tickers]

        medianprops = dict(color=median_color, linewidth=median_lw)
        whiskerprops = dict(color=whisker_color, linewidth=whisker_lw)
        capprops = dict(color=cap_color, linewidth=cap_lw)
        boxprops = dict(color=box_edge_color, linewidth=box_edge_lw)
        flierprops = dict(
            marker=flier_marker,
            markersize=flier_markersize,
            markerfacecolor=flier_markerfacecolor,
            markeredgecolor=flier_markeredgecolor,
            alpha=0.85
        )
        meanprops = dict(
            color="#404040",
            linewidth=1.2,
            linestyle="--"
        )

        bp = self._ax.boxplot(
            data_plot,
            labels=labels,
            whis=whis,
            showfliers=show_fliers,
            showmeans=show_means,
            meanline=meanline,
            widths=widths,
            notch=notch,
            vert=vert,
            patch_artist=True,
            boxprops=boxprops,
            medianprops=medianprops,
            whiskerprops=whiskerprops,
            capprops=capprops,
            flierprops=flierprops,
            meanprops=meanprops,
        )

        # fill colors
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(cols[i])
            patch.set_alpha(box_face_alpha)

        # -----------------------
        # 4) Optional stats annotation
        # -----------------------
        if show_stats:
            for i, t in enumerate(tickers):
                s = db[t].dropna()
                if s.empty:
                    continue

                pos = i + 1  # matplotlib boxplot positions start at 1

                if stats == "median":
                    stat_val = float(s.median())
                    label_txt = f"{stat_val:{stats_fmt}}"

                    if vert:
                        xy = (pos, stat_val)
                    else:
                        xy = (stat_val, pos)

                elif stats == "count":
                    label_txt = f"n={len(s)}"
                    anchor_val = float(s.max()) if vert else float(i + 1)

                    if vert:
                        xy = (pos, float(s.max()))
                    else:
                        xy = (float(s.max()), pos)

                else:
                    raise ValueError("stats must be one of: 'median', 'count'")

                self._ax.annotate(
                    label_txt,
                    xy=xy,
                    xytext=stats_offset,
                    textcoords="offset points",
                    ha="center" if vert else "left",
                    va="bottom" if vert else "center",
                    fontsize=stats_fontsize,
                    fontweight="bold",
                    color=stats_color,
                    zorder=6
                )

        # -----------------------
        # 5) NUEVO: range tags on whiskers
        # -----------------------
        if show_range_tags:
            for i in range(len(tickers)):
                low_whisker = bp["whiskers"][2 * i]
                high_whisker = bp["whiskers"][2 * i + 1]

                if vert:
                    # real whisker end coordinates
                    x_low = float(np.mean(low_whisker.get_xdata()))
                    y_low = float(np.min(low_whisker.get_ydata()))

                    x_high = float(np.mean(high_whisker.get_xdata()))
                    y_high = float(np.max(high_whisker.get_ydata()))

                    if range_tag_show_low:
                        self._ax.annotate(
                            f"{y_low:{range_tag_fmt}}",
                            xy=(x_low, y_low),
                            xytext=range_tag_offset_low,
                            textcoords="offset points",
                            ha="center",
                            va="top",
                            fontsize=range_tag_fontsize,
                            color=range_tag_color,
                            bbox=dict(
                                boxstyle="round,pad=0.25",
                                fc=range_tag_bg_color,
                                ec=range_tag_edge_color,
                                alpha=range_tag_alpha
                            ),
                            zorder=6
                        )

                    if range_tag_show_high:
                        self._ax.annotate(
                            f"{y_high:{range_tag_fmt}}",
                            xy=(x_high, y_high),
                            xytext=range_tag_offset_high,
                            textcoords="offset points",
                            ha="center",
                            va="bottom",
                            fontsize=range_tag_fontsize,
                            color=range_tag_color,
                            bbox=dict(
                                boxstyle="round,pad=0.25",
                                fc=range_tag_bg_color,
                                ec=range_tag_edge_color,
                                alpha=range_tag_alpha
                            ),
                            zorder=6
                        )

                else:
                    y_low = float(np.mean(low_whisker.get_ydata()))
                    x_low = float(np.min(low_whisker.get_xdata()))

                    y_high = float(np.mean(high_whisker.get_ydata()))
                    x_high = float(np.max(high_whisker.get_xdata()))

                    if range_tag_show_low:
                        self._ax.annotate(
                            f"{x_low:{range_tag_fmt}}",
                            xy=(x_low, y_low),
                            xytext=range_tag_offset_low,
                            textcoords="offset points",
                            ha="right",
                            va="center",
                            fontsize=range_tag_fontsize,
                            color=range_tag_color,
                            bbox=dict(
                                boxstyle="round,pad=0.25",
                                fc=range_tag_bg_color,
                                ec=range_tag_edge_color,
                                alpha=range_tag_alpha
                            ),
                            zorder=6
                        )

                    if range_tag_show_high:
                        self._ax.annotate(
                            f"{x_high:{range_tag_fmt}}",
                            xy=(x_high, y_high),
                            xytext=range_tag_offset_high,
                            textcoords="offset points",
                            ha="left",
                            va="center",
                            fontsize=range_tag_fontsize,
                            color=range_tag_color,
                            bbox=dict(
                                boxstyle="round,pad=0.25",
                                fc=range_tag_bg_color,
                                ec=range_tag_edge_color,
                                alpha=range_tag_alpha
                            ),
                            zorder=6
                        )

        # -----------------------
        # 6) NUEVO: show last value from each series
        # -----------------------
        if show_last_value:
            for i, t in enumerate(tickers):
                s = db[t].dropna()
                if s.empty:
                    continue

                pos = i + 1
                last_val = float(s.iloc[-1])

                point_color = cols[i] if last_value_use_series_color else last_value_color

                mode = (last_value_mode or "").lower()

                # --- dot ---
                if mode in {"dot", "dot_tag"}:
                    if vert:
                        self._ax.scatter(
                            pos,
                            last_val,
                            s=last_value_marker_size,
                            marker=last_value_marker,
                            color=point_color,
                            edgecolor=last_value_edge_color,
                            linewidth=last_value_edge_width,
                            alpha=last_value_alpha,
                            zorder=7
                        )
                    else:
                        self._ax.scatter(
                            last_val,
                            pos,
                            s=last_value_marker_size,
                            marker=last_value_marker,
                            color=point_color,
                            edgecolor=last_value_edge_color,
                            linewidth=last_value_edge_width,
                            alpha=last_value_alpha,
                            zorder=7
                        )

                # --- tag ---
                if mode in {"tag", "dot_tag"}:
                    label_txt = last_value_label_fmt.format(
                        value=last_val,
                        ticker=labels[i] if i < len(labels) else t,
                        date=s.index[-1] if len(s.index) > 0 else None
                    )

                    if vert:
                        self._ax.annotate(
                            label_txt,
                            xy=(pos, last_val),
                            xytext=last_value_loc,
                            textcoords="offset points",
                            ha="center",
                            va="bottom",
                            fontsize=last_value_fontsize,
                            fontweight=last_value_fontweight,
                            color=point_color,
                            bbox=dict(
                                boxstyle="round,pad=0.3",
                                fc=last_value_bg_color,
                                ec=last_value_edgecolor,
                                alpha=1.0
                            ),
                            zorder=7
                        )
                    else:
                        self._ax.annotate(
                            label_txt,
                            xy=(last_val, pos),
                            xytext=last_value_loc,
                            textcoords="offset points",
                            ha="left",
                            va="center",
                            fontsize=last_value_fontsize,
                            fontweight=last_value_fontweight,
                            color=point_color,
                            bbox=dict(
                                boxstyle="round,pad=0.3",
                                fc=last_value_bg_color,
                                ec=last_value_edgecolor,
                                alpha=1.0
                            ),
                            zorder=7
                        )


        if show_last_value and show_last_value_legend:
            mode = (last_value_mode or "").lower()

            # color used in legend
            legend_color = last_value_legend_color
            if legend_color is None:
                if last_value_use_series_color and len(cols) == 1:
                    legend_color = cols[0]
                else:
                    legend_color = last_value_color

            # build handle depending on mode
            if mode == "tag":
                legend_handle = Patch(
                    facecolor=last_value_bg_color,
                    edgecolor=last_value_edgecolor,
                    label=last_value_legend_label,
                    alpha=1.0
                )
            else:
                # for "dot" and "dot_tag"
                legend_handle = Line2D(
                    [0], [0],
                    linestyle="None",
                    marker=last_value_marker,
                    markersize=np.sqrt(last_value_marker_size),
                    markerfacecolor=legend_color,
                    markeredgecolor=last_value_edge_color,
                    markeredgewidth=last_value_edge_width,
                    alpha=last_value_alpha,
                    label=last_value_legend_label
                )

            # keep any existing legend items, avoid duplicates
            handles, legend_labels = self._ax.get_legend_handles_labels()

            if last_value_legend_label not in legend_labels:
                handles = handles + [legend_handle]
                legend_labels = legend_labels + [last_value_legend_label]

            self._ax.legend(
                handles=handles,
                labels=legend_labels,
                loc=last_value_legend_loc,
                frameon=last_value_legend_frameon,
                fontsize=last_value_legend_fontsize
            )


        # -----------------------
        # 7) Shared styling
        # -----------------------
        if isinstance(hlines, (float, int)) and hlines is not None:
            self._ax.axhline(float(hlines), color="gray", linestyle="--", linewidth=0.8)
        elif isinstance(hlines, list) and hlines is not None:
            for h in hlines:
                self._ax.axhline(float(h), color="gray", linestyle="--", linewidth=0.8)

        if show_hguide:
            self.guias_horizontales(mostrar_cero=False)

        if y_lim is not None:
            self._ax.set_ylim(*y_lim)

        self._ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:{y_fmt}}"))
        self.set_tick_fontsize(size=8)

        for lab in self._ax.get_xticklabels():
            lab.set_rotation(x_label_rotation)
            lab.set_ha(x_label_ha)

        self._ax.margins(x=0.03)

        self._fig.subplots_adjust(
            left=0.15,
            right=0.93,
            top=0.80,
            bottom=0.18 if x_label_rotation == 0 else 0.24
        )

        # source
        if isinstance(source, str):
            self.add_source(source, color="#454444")
        elif isinstance(source, list) and len(source) > 1:
            self.add_source(source, fontsize=5, color="#454444")
        elif isinstance(source, list) and len(source) <= 1:
            self.add_source(source, color="#454444")

