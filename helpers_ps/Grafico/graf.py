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
from matplotlib.ticker import FuncFormatter, MultipleLocator
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from helpers_ps.Config.var_globs import PALETA_COLORES
from importlib.resources import files

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

# Clase diseñado para almacenar la metadata del grafico
@dataclass
class Graph_meta_data():
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

    def __post_init__(self):
        self.dataframe = [self.dataframe] if isinstance(self.dataframe, pd.DataFrame) else self.dataframe

    # funcion para poder actualizar el metadata hacia _meta_data
    def _set_axis(self, ax_index: int = 0) -> None:
        """
        Select active axis when working with multiple subplots.
        """
        if not hasattr(self, "_axes") or self._axes is None:
            raise RuntimeError("Axes not initialized. Call plot() first.")

        if ax_index >= len(self._axes):
            raise IndexError("Axis index out of range.")
        
        if self._ax_idx == ax_index:
            raise ValueError(f"El subplot {ax_index} ya se encuenta seleccionado")
        
        #actualizar información en el _meta_data
        self._meta_data[ax_index] = {
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
                "ticker_label_color": self._ticker_label_color
            }
        
        # jalar la informacion del nuevo plot
        self._df_idx = self._meta_data[ax_index]["dataframe"]
        self._df = self.dataframe[self._df_idx]

        self._x_axis_fechas = self._meta_data[ax_index]["xmeta"]["fechas"]
        self._x_axis_mode = self._meta_data[ax_index]["xmeta"]["mode"]
        self._x_vals = self._meta_data[ax_index]["xmeta"]["x_vals"]
        self._months = self._meta_data[ax_index]["months"]
        self._years = self._meta_data[ax_index]["years"]

        self._bar_mode = self._meta_data[ax_index]["bar_mode"]
        self._bar_stacked = self._meta_data[ax_index]["bar_stacked"]
        self._bar_grouped = self._meta_data[ax_index]["bar_grouped"]
        self._bar_rects = self._meta_data[ax_index]["bar_rects"]
        
        self._ticker_label_color = self._meta_data[ax_index]["ticker_label_color"]

        # Guardar el ax y jalar el nuevo
        self._axes[self._ax_idx] = self._ax
        self._ax = self._axes[ax_index]
        return None

    def _select_df(self, df_idx=0):
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
                "ticker_label_color": None
            }
            for i, ax in enumerate(self._axes)
        }

class Graph_base(Graph_meta_data):

    # =========================
    # funciones de ayuda
    # =========================
    def _months_years(self, fechas):
        """
        Store months/years for the active axis only.
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

    def _coerce_to_bbg_x(self, x):
        """
        Convert a user x (date/str/int) to bbg integer x-position.
        Uses metadata of the active axis.
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
    def _prep_x_axis(
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
        return dataframe

    def _prep_y_axis(
        self,
        lim: tuple[float, float] | None = None,
        fmt: str | None = None,
        fontsize: float = 7,
        tick_step: int = None
    ) -> None:
        
        # --- Configuración del limite y ---
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

    def add_legend(
            self,
            show: bool = False,
            loc: str = "upper left",
            fontsize: int = 7,
            frameon: bool = True,
            edgecolor: str = "white",
            facecolor: str = "white",
            framealpha: float = 0.6
    ) -> None:
        if show:
            self._ax.legend(
                loc=loc,
                fontsize=fontsize,
                frameon=frameon,
                edgecolor=edgecolor,
                facecolor=facecolor,
                framealpha=framealpha
            )

    # =========================
    # Metodos de la figura general
    # =========================
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
        sharey: bool = False,
        dpi: int | None = None,
        height_ratios: list[float] | None = None,
        width_ratios: list[float] | None = None,
        hspace: float | None = None,
        wspace: float | None = None
    ) -> None:
        """
        Base plot creator.

        Supports:
        - single axis (default)
        - multiple subplots
        - custom GridSpec layout via height_ratios / width_ratios / hspace / wspace

        Keeps backward compatibility with existing code.
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
                bottom=0.18
            )

    # =========================
    # Metodos de as etiquetas, guias y sombras
    # =========================
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
        label_h_align="center",
        label_v_align="center",
        ubic_etq=(0, 17),
        fontsize=7,
        fontweight="normal",
        font_color="black",
        bg_color="#ECEFF1",
        bg_alpha=1.0,
        edge_color="none",
        show_bbox=True,
        zorder=6,
    ):
        """
        Adds a label at (x_value, y_value), handling any x type and
        allowing full control of styling.
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
            zorder=zorder
        )
    
    def punto_valor(
        self,
        x_value,
        y_value,
        color="red",
        size=30,
        zorder=5
    ):
        """
        Adds a point at (x_value, y_value), handling any x type.
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


        if isinstance(periods, tuple) and len(periods) == 2:
            periods = [periods]

        mode = self._x_axis_mode
        bar_meta = self._bar_mode

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

            elif bar_meta is not None and bar_meta == "last":
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

    def lineas_horizontales(
            self,
            y_values: list[float] | float | None = None,
            linestyle: str | None = None,
            linewidth: float = 0.5,
            color: str = "gray",
    ) -> None:
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
        date_list = [(f"{recesiones.loc[x,"start_date"]:%Y-%m-%d}", f"{recesiones.loc[x,"end_date"]:%Y-%m-%d}") for x in recesiones.index.tolist()]
        controles = controles if controles is not None else dict(color="grey", alpha=0.3)
        self.shade_x_periods(periods=date_list, **controles)

        return None

class Line_tags():
    # funcion para procesar diccionario de controles de annotaciones
    def _line_label_generate(
        self,
        control_dict: dict = None,
    ) -> None:
        """
        Funcion encargada de graficar los puntos en la linea que se desean

        El formato del dict es:
        {
            key_random: {
                ticker: ticker en cuestion,
                x_values: lista de valores x sobre el que se quiere poner el punto / punto y tag / tag
                template: plantilla de tag con disponibles ticker, x_value, y_value
                loc_offset: offset para el tag relativo al punto original
                font_color: color de la fuente
                font_size: tamaño de la fuente
                bg_color: color de fondo del tag
                show: dot / tag / dot_tag
                dot_color: color del punto
                dot_size: tamaño del punto
                dot_zorder: zorder del punto
            }
        }
        """
        if control_dict is None:
            return None
        df = self._df
        
        # una vez validado la información generar los puntos en base a las variables de control
        def _generate(
                ticker,
                x_values: list[str | float | int] | str = "last",
                template: str = "{ticker}\n{x_value:%B-%Y}: {y_value:,.2f}",
                font_color: str = None,
                fontsize: int = 7,
                bg_color: str = "None",
                show: str = "dot",       # dot = solo punto | dot_tag = punto + etiqueta | tag = solo etiqueta):
                dot_color: str = None,
                dot_size: int = 30,
                dot_zorder: int = 5,
                fontweight: str = "normal",
                label_h_align="center",
                label_v_align="center",
                ubic_etq=(0, 17),
                bg_alpha=1.0,
                edge_color="none",
                show_bbox=True,
                zorder=6,
        ):
            # Validar que es un ticker valido
            if ticker not in df.columns:
                raise ValueError(f"El ticker {ticker} no es una columna disponible en el dataframe")
            
            # obtener los valores referenciales en formato de list of tuple
            xy_pairs = []
            if isinstance(x_values, str) and x_values == "last":
                last_x_value = df.tail(1)
                last_x_value = last_x_value.index.tolist()[0]
                last_value_y = df.loc[last_x_value, ticker].item()
                xy_pairs.append((last_x_value, last_value_y))
            elif isinstance(x_values, list):
                for i in x_values:
                    
                    if isinstance(i, str) and i == "last":
                        last_x_value = df.tail(1)
                        last_x_value = last_x_value.index.tolist()[0]
                        last_value_y = df.loc[last_x_value, ticker].item()
                        xy_pairs.append((last_x_value, last_value_y))
                        continue

                    _val_x = i
                    _val_y = df.loc[i, ticker].item()
                    xy_pairs.append((_val_x, _val_y))
            
            # con los pares xy generarlo en el grafico
            for pair in xy_pairs:
                x, y = pair
                _ticker_label_color = [dd for dd in self._ticker_label_color if dd[0] == ticker]
                if "tag" in show:
                    font_color = _ticker_label_color[0][2] if font_color is None else font_color
                    self.etiqueta_valor(
                        label=template.format(x_value=x, y_value=y, ticker=ticker),
                        x_value=x,          # datetime real para texto "Mar 26: 4.3"
                        y_value=y,
                        ubic_etq=ubic_etq,
                        bg_color=bg_color,
                        font_color=font_color,
                        fontsize=fontsize,
                        fontweight=fontweight,
                        bg_alpha=bg_alpha,
                        edge_color=edge_color,
                        show_bbox=show_bbox,
                        zorder=zorder,
                        label_h_align=label_h_align,
                        label_v_align=label_v_align,
                        )
                
                if "dot" in show:
                    dot_color = _ticker_label_color[0][2] if dot_color is None else dot_color
                    self.punto_valor(
                        x_value=x,
                        y_value=y,
                        color=dot_color,
                        size=dot_size,
                        zorder=dot_zorder
                    )

        for ti in control_dict.keys():
            _temp_controls = control_dict[ti]
            _generate(**_temp_controls)

class Bar_tags():

    def _bar_x_key_normalize(self, value):
        """
        Normaliza fechas/categorías para comparación consistente.
        """
        try:
            if isinstance(value, (pd.Timestamp, np.datetime64)):
                return pd.Timestamp(value)
            return pd.Timestamp(value)
        except Exception:
            return str(value)

    def _bar_resolve_x_indices(self, ticker: str, x_values) -> list[int]:
        """
        Resuelve x_values a posiciones enteras del eje x usando self._bars_x_reference.

        x_values soporta:
        - "all"
        - "last"
        - lista/tupla/set de fechas/categorías
        """
        if not hasattr(self, "_bars_x_reference"):
            raise ValueError("No existe self._bars_x_reference. Guarda la referencia del eje x dentro de graph_bar.")

        x_ref = list(self._bars_x_reference)
        x_ref_norm = [self._bar_x_key_normalize(v) for v in x_ref]

        if x_values == "all":
            return list(range(len(x_ref)))

        if x_values == "last":
            bars_entry = self._bars_data.get(ticker)
            if bars_entry is None:
                return []

            for idx in range(len(x_ref) - 1, -1, -1):
                rect, _mode = self._bar_get_rect_for_index(bars_entry=bars_entry, idx=idx)
                if rect is None:
                    continue

                h = rect.get_height()
                if h is not None and not np.isnan(h) and abs(h) > 0:
                    return [idx]

            return [len(x_ref) - 1] if len(x_ref) > 0 else []

        if not isinstance(x_values, (list, tuple, set)):
            raise ValueError("x_values debe ser 'all', 'last' o una lista/tupla/set de fechas/categorías.")

        requested = {self._bar_x_key_normalize(v) for v in x_values}
        return [i for i, v in enumerate(x_ref_norm) if v in requested]

    def _bar_get_rect_for_index(self, bars_entry: dict, idx: int):
        """
        Retorna el rectángulo útil para un ticker en la posición idx.

        Retorna:
        - (rect, "grouped") si bars_entry["bars"] es BarContainer
        - (rect, "stacked") si bars_entry["bars"] es {"pos":..., "neg":...}
        - (None, mode) si no hay rectángulo válido
        """
        bars_obj = bars_entry["bars"]

        # --- stacked
        if isinstance(bars_obj, dict):
            bars_pos = bars_obj.get("pos")
            bars_neg = bars_obj.get("neg")

            rect_pos = None
            rect_neg = None

            if bars_pos is not None and idx < len(bars_pos):
                rect_pos = bars_pos[idx]

            if bars_neg is not None and idx < len(bars_neg):
                rect_neg = bars_neg[idx]

            h_pos = rect_pos.get_height() if rect_pos is not None else 0.0
            h_neg = rect_neg.get_height() if rect_neg is not None else 0.0

            if rect_pos is not None and h_pos is not None and not np.isnan(h_pos) and abs(h_pos) > 0:
                return rect_pos, "stacked"

            if rect_neg is not None and h_neg is not None and not np.isnan(h_neg) and abs(h_neg) > 0:
                return rect_neg, "stacked"

            return None, "stacked"

        # --- grouped / single
        if idx < len(bars_obj):
            return bars_obj[idx], "grouped"

        return None, "grouped"

    def _bar_get_stack_total_anchor(self, idx: int, ref_ticker: str):
        """
        Obtiene el ancla del total del stack en la posición idx.

        Retorna:
        - x
        - y_anchor
        - total_value
        - sign ("positive" | "negative")
        """
        if ref_ticker not in self._bars_data:
            return None, None, None, None

        total_value = 0.0
        top_positive = 0.0
        bottom_negative = 0.0

        # --- usar un rect de referencia para obtener x
        ref_rect, ref_mode = self._bar_get_rect_for_index(self._bars_data[ref_ticker], idx)
        if ref_rect is None:
            return None, None, None, None

        if ref_mode != "stacked":
            raise ValueError("El total del stack solo aplica cuando el gráfico es stacked.")

        x = ref_rect.get_x() + ref_rect.get_width() / 2.0

        for _ticker, entry in self._bars_data.items():
            bars_obj = entry["bars"]

            if not isinstance(bars_obj, dict):
                continue

            rect_pos = None
            rect_neg = None

            if bars_obj.get("pos") is not None and idx < len(bars_obj["pos"]):
                rect_pos = bars_obj["pos"][idx]

            if bars_obj.get("neg") is not None and idx < len(bars_obj["neg"]):
                rect_neg = bars_obj["neg"][idx]

            if rect_pos is not None:
                h = rect_pos.get_height()
                if h is not None and not np.isnan(h):
                    total_value += h
                    top_positive = max(top_positive, rect_pos.get_y() + rect_pos.get_height())

            if rect_neg is not None:
                h = rect_neg.get_height()
                if h is not None and not np.isnan(h):
                    total_value += h
                    bottom_negative = min(bottom_negative, rect_neg.get_y() + rect_neg.get_height())

        if total_value >= 0:
            return x, top_positive, total_value, "positive"

        return x, bottom_negative, total_value, "negative"

    def _bar_format_template(
            self,
            template: str,
            ticker: str,
            x_value,
            y_value: float | None = None,
            total_value: float | None = None,
            label: str | None = None
        ) -> str:
        """
        Formatea template con placeholders estilo:
        {ticker}, {label}, {x_value}, {y_value}, {total_value}
        """
        return template.format(
            ticker=ticker,
            label=label if label is not None else ticker,
            x_value=x_value,
            y_value=y_value,
            total_value=total_value
        )

    def _bar_value_label_generate_dict(self, label_dict: dict | None = None) -> None:
        """
        Genera etiquetas numéricas sobre barras usando una configuración tipo dict.

        Comportamiento:
        - grouped / single: etiqueta al final de la barra
        - stacked: etiqueta al centro del segmento del ticker seleccionado

        Estructura esperada de label_dict:
        {
            "1": dict(
                ticker="PX_LAST-SPX INDEX",
                x_values=["last", pd.Timestamp("2025-12-31")],   # o "all" o "last"
                template="{y_value:,.0f}",
                fontsize=7,
                font_color="black",
                fontweight="normal",
                bbox=None,
                pad_points=2,
                zorder=6
            ),
            "2": dict(
                ticker="PX_LAST-RUO INDEX",
                x_values=[pd.Timestamp("2023-12-31")],
                template="{y_value:,.0f}",
                fontsize=7,
                font_color="blue",
                fontweight="bold"
            )
        }
        """

        if not label_dict:
            return

        if not hasattr(self, "_bars_data") or not self._bars_data:
            raise ValueError("No existe self._bars_data. Ejecuta graph_bar antes de usar este helper.")

        # label -> ticker
        ticker_to_label = {}
        if hasattr(self, "_ticker_label_color"):
            for t, lbl, _c in self._ticker_label_color:
                ticker_to_label[t] = lbl

        x_ref = list(self._bars_x_reference)

        def _control(
                ticker: str | None = None,
                x_values: list[str | int | float] | str | None = None,
                template: str = "{ticker}\n{x_value:%B-%Y}: {y_value:,.2f}",
                font_color: str = "black",
                fontsize: int = 7,
                bg_color: str = "None",
                fontweight: str = "normal",
                label_h_align="center",
                label_v_align="center",
                ubic_etq=(0, 0),
                bg_alpha=1.0,
                edge_color="none",
                show_bbox=True,
                zorder=6,

        ):
            # Funcion para controlar el dictionario de input
            if not ticker:
                return None

            if ticker not in self._bars_data.keys():
                return None

            idxs = self._bar_resolve_x_indices(ticker=ticker, x_values=x_values)

            for idx in idxs:
                rect, mode = self._bar_get_rect_for_index(
                    bars_entry=self._bars_data[ticker],
                    idx=idx
                )

                if rect is None:
                    continue

                h = rect.get_height()
                if h is None or np.isnan(h) or abs(h) == 0:
                    continue

                x = rect.get_x() + rect.get_width() / 2.0
                x_value = x_ref[idx]
                label = ticker_to_label.get(ticker, ticker)

                text = self._bar_format_template(
                    template=template,
                    ticker=ticker,
                    x_value=x_value,
                    y_value=h,
                    total_value=None,
                    label=label
                )

                # --- stacked: centro del segmento
                if mode == "stacked":
                    y = rect.get_y() + rect.get_height() / 2.0
                    
                    self.etiqueta_valor(
                        x_value = x_value,
                        y_value = y,
                        label=text,
                        ubic_etq=ubic_etq,
                        bg_color=bg_color,
                        font_color=font_color,
                        fontsize=fontsize,
                        fontweight=fontweight,
                        bg_alpha=bg_alpha,
                        edge_color=edge_color,
                        show_bbox=show_bbox,
                        zorder=zorder,
                        label_h_align=label_h_align,
                        label_v_align=label_v_align,
                    )

                # --- grouped / single: final de la barra
                else:
                    y_end = rect.get_y() + rect.get_height()
                    
                    if h >= 0:
                        local_va = "bottom" if label_v_align == "center" else label_v_align
                        local_offset = (ubic_etq[0], abs(ubic_etq[1]))
                    else:
                        local_va = "top" if label_v_align == "center" else label_v_align
                        local_offset = (ubic_etq[0], -abs(ubic_etq[1]))
                    
                    self.etiqueta_valor(
                        x_value = x,
                        y_value = y_end,
                        label=text,
                        ubic_etq=local_offset,
                        bg_color=bg_color,
                        font_color=font_color,
                        fontsize=fontsize,
                        fontweight=fontweight,
                        bg_alpha=bg_alpha,
                        edge_color=edge_color,
                        show_bbox=show_bbox,
                        zorder=zorder,
                        label_h_align=label_h_align,
                        label_v_align=local_va,
                    )            

        for _key, cfg in label_dict.items():
            _control(**label_dict[_key])
            
    def _bar_tag_generate_dict(self, tag_dict: dict | None = None) -> None:
        """
        Genera tags sobre barras usando una configuración tipo dict.

        show soporta:
        - "bar_tag"      -> tag al centro de la barra / segmento
        - "stack_total"  -> tag sobre el total del stack (solo si stacked)

        Estructura esperada:
        {
            "1": dict(
                ticker="PX_LAST-SPX INDEX",
                x_values=["last", pd.Timestamp("2025-12-31")],
                template="hola",
                show="bar_tag",
                fontsize=7,
                font_color="black",
                fontweight="normal",
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    facecolor="white",
                    edgecolor="#BFBFBF",
                    alpha=0.95
                ),
                zorder=7
            ),
            "2": dict(
                ticker="PX_LAST-SPX INDEX",
                x_values=[pd.Timestamp("2025-12-31")],
                template="{total_value:,.0f}",
                show="stack_total",
                fontsize=7,
                font_color="black"
            )
        }
        """

        if not tag_dict:
            return

        if not hasattr(self, "_bars_data") or not self._bars_data:
            raise ValueError("No existe self._bars_data. Ejecuta graph_bar antes de usar este helper.")

        # ticker -> label
        ticker_to_label = {}
        if hasattr(self, "_ticker_label_color"):
            for t, lbl, _c in self._ticker_label_color:
                ticker_to_label[t] = lbl

        x_ref = list(self._bars_x_reference)

        def _control(
                ticker: str | None = None,
                show: dict = "stalked_total", 
                x_values: list[str | int | float] | str | None = None,
                template: str = "{ticker}\n{x_value:%B-%Y}: {y_value:,.2f}",
                font_color: str = "black",
                fontsize: int = 7,
                bg_color: str = "None",
                fontweight: str = "normal",
                label_h_align="center",
                label_v_align="center",
                ubic_etq=(0, 0),
                bg_alpha=1.0,
                edge_color="none",
                show_bbox=True,
                zorder=6,
        ):
            if not ticker:
                return None

            if ticker not in self._bars_data.keys():
                return None

            idxs = self._bar_resolve_x_indices(ticker=ticker, x_values=x_values)

            for idx in idxs:
                x_value = x_ref[idx]
                label = ticker_to_label.get(ticker, ticker)

                # ======================================================
                # stack_total -> total del stack
                # ======================================================
                if show == "stack_total":
                    x, y_anchor, total_value, sign = self._bar_get_stack_total_anchor(
                        idx=idx,
                        ref_ticker=ticker
                    )

                    if x is None:
                        continue

                    text = self._bar_format_template(
                        template=template,
                        ticker=ticker,
                        x_value=x_value,
                        y_value=None,
                        total_value=total_value,
                        label=label
                    )

                    if sign == "positive":
                        va = "bottom"
                        ubic_etq = (ubic_etq[0], ubic_etq[1] + 5)
                    else:
                        va = "top"
                        ubic_etq = (ubic_etq[0], ubic_etq[1] - 10)

                    self.etiqueta_valor(
                        x_value = x,
                        y_value = y_anchor,
                        label = text,
                        ubic_etq=ubic_etq,
                        bg_color=bg_color,
                        font_color=font_color,
                        fontsize=fontsize,
                        fontweight=fontweight,
                        bg_alpha=bg_alpha,
                        edge_color=edge_color,
                        show_bbox=show_bbox,
                        zorder=zorder,
                        label_h_align=label_h_align,
                        label_v_align=label_v_align,
                    )

                    continue

                # ======================================================
                # bar_tag -> centro de barra / segmento
                # ======================================================
                rect, mode = self._bar_get_rect_for_index(
                    bars_entry=self._bars_data[ticker],
                    idx=idx
                )

                if rect is None:
                    continue

                h = rect.get_height()
                if h is None or np.isnan(h) or abs(h) == 0:
                    continue

                x = rect.get_x() + rect.get_width() / 2.0
                y = rect.get_y() + rect.get_height() / 2.0

                text = self._bar_format_template(
                    template=template,
                    ticker=ticker,
                    x_value=x_value,
                    y_value=h,
                    total_value=None,
                    label=label
                )

                self.etiqueta_valor(
                        x_value = x,
                        y_value = y,
                        label = text,
                        ubic_etq=ubic_etq,
                        bg_color=bg_color,
                        font_color=font_color,
                        fontsize=fontsize,
                        fontweight=fontweight,
                        bg_alpha=bg_alpha,
                        edge_color=edge_color,
                        show_bbox=show_bbox,
                        zorder=zorder,
                        label_h_align=label_h_align,
                        label_v_align=label_v_align,
                    )

        for _key, cfg in tag_dict.items():
            _control(**tag_dict[_key])
            
class BoxW_tags():
    def _box_whiskers_label_generate(
        self,
        control_dict: dict = None,
    ) -> None:
        
        if control_dict is None:
            return None
        df = self._df
        columns = df.columns.tolist()
        # una vez validado la información generar los puntos en base a las variables de control
        def _generate(
                ticker,
                x_values: list[str | float | int] | str = "last",
                template: str = "{y_value:,.2f}",
                font_color: str = None,
                fontsize: int = 7,
                bg_color: str = "None",
                show: str = "dot",       # dot = solo punto | dot_tag = punto + etiqueta | tag = solo etiqueta):
                dot_color: str = None,
                dot_size: int = 30,
                dot_zorder: int = 5,
                fontweight: str = "normal",
                label_h_align="center",
                label_v_align="center",
                ubic_etq=(20, 0),
                bg_alpha=1.0,
                edge_color="none",
                show_bbox=True,
                zorder=6,
        ):
            # Validar que es un ticker valido
            if ticker not in columns:
                raise ValueError(f"El ticker {ticker} no es una columna disponible en el dataframe")
            
            # sacar el valor z de la serie para el caso de box
            z_value = columns.index(ticker) + 1
            
            # obtener los valores referenciales en formato de list of tuple
            xyz_pairs = []
            if isinstance(x_values, str) and x_values == "last":
                last_x_value = df.tail(1)
                last_x_value = last_x_value.index.tolist()[0]
                last_value_y = df.loc[last_x_value, ticker].item()
                xyz_pairs.append((last_x_value, last_value_y, z_value))
            elif isinstance(x_values, list):
                for i in x_values: 
                    if isinstance(i, str) and i == "last":
                        last_x_value = df.tail(1)
                        last_x_value = last_x_value.index.tolist()[0]
                        last_value_y = df.loc[last_x_value, ticker].item()
                        xyz_pairs.append((last_x_value, last_value_y, z_value))
                        continue

                    _val_x = i
                    _val_y = df.loc[i, ticker].item()
                    xyz_pairs.append((_val_x, _val_y, z_value))
            
            # con los pares xy generarlo en el grafico
            for pair in xyz_pairs:
                x, y, z = pair
                _ticker_label_color = [dd for dd in self._ticker_label_color if dd[0] == ticker]
                if "tag" in show:
                    font_color = _ticker_label_color[0][2] if font_color is None else font_color
                    self.etiqueta_valor(
                        label=template.format(x_value=x, y_value=y, ticker=ticker),
                        x_value=z,          # datetime real para texto "Mar 26: 4.3"
                        y_value=y,
                        ubic_etq=ubic_etq,
                        bg_color=bg_color,
                        font_color=font_color,
                        fontsize=fontsize,
                        fontweight=fontweight,
                        bg_alpha=bg_alpha,
                        edge_color=edge_color,
                        show_bbox=show_bbox,
                        zorder=zorder,
                        label_h_align=label_h_align,
                        label_v_align=label_v_align,
                        )
                
                if "dot" in show:
                    dot_color = _ticker_label_color[0][2] if dot_color is None else dot_color
                    self.punto_valor(
                        x_value=z,
                        y_value=y,
                        color=dot_color,
                        size=dot_size,
                        zorder=dot_zorder
                    )

        for ti in control_dict.keys():
            _temp_controls = control_dict[ti]
            _generate(**_temp_controls)
        
@dataclass
class Graph_mtplt(Graph_base, Line_tags, Bar_tags, BoxW_tags):

    def graph_line(
        self,
        # --- Configuración del grafico
        figsize: tuple[float, float] = (6.00, 5.00),                        # Tamaño del grafico configuración general es (6,4.8) --> tamaño estandard
        # --- Configuración de los elementos adicionales del grafico
        titles: dict | None = None,                                         # titulo de la grafica
        source: list[str] | str | None = None,                                          # Fuente de datos del grafico
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
        El dataframe es tratado como preparado

        Ejemplo:
        indice        |    PX_LAST-SPX    |   PX_LAST-IBEX    |   PX_LAST-NASDAQ  |
        ene.-26 |    7200           |   9200            |   11000           |

        mar.-26 |    7300           |   9300            |   11100           |

        abr.-26 |    7400           |   9400            |   11200           |

        Se asume que el indice del dataframe es el eje x (numerico, fechas, categorico) y las columnas son las series a graficar
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
        hlines = hlines if hlines is not None else dict()

        # --- 7. Generación del gráfico y el plot en caso no exista
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        # --- 8. Agregar titulos globales
        self.set_titles(**titles)
        if source:
            self.add_source(source)

        # --- 9. Manejo del eje x
        db = self._prep_x_axis(dataframe=db, **x_axis)

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
        self._prep_y_axis(**y_axis)

        # -- 13. Agregar lineas horizontales
        self.lineas_horizontales(**hlines)
        
        # -- 14. Agregar guias horizontales
        if show_hguide:
            self.guias_horizontales(mostrar_cero=False)
            

        # --- 15. Agregar leyenda
        self.add_legend(**legend)

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

    def graph_bar(
            self,
            # --- Configuración del grafico
            figsize: tuple[float, float] = (6.00, 5.00),

            # --- Configuración de los elementos adicionales del grafico
            titles: dict | None = None,
            source: list[str] | str | None = None,

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
            bar_tags: dict | None = None,

            # --- Configuración Leyenda
            legend: dict | None = None,

            # --- Configuración lineas horizontales
            hlines: dict | None = None,

            # --- Mostrar guias horizontales
            show_hguide: bool = False
        ) -> None:
            """
            Gráfico de barras siguiendo la misma estructura de graph_line.

            Modos:
            - last: snapshot / categorías en el índice
            - time: series de tiempo
            - auto:
                * 1 ticker  -> time
                * >1 ticker -> time si grouped/stacked, de lo contrario last
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
            legend = legend if legend is not None else dict()
            hlines = hlines if hlines is not None else dict()
            bar_labels = bar_labels if bar_labels is not None else dict()
            bar_tags = bar_tags if bar_tags is not None else dict()


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
            if source:
                self.add_source(source)

            bars_data = {}

            # ==========================================================
            # MODE: TIME
            # ==========================================================
            if bar_mode == "time":
                # preparar eje x usando helper base (igual lógica que graph_line)
                db = self._prep_x_axis(dataframe=db, **x_axis)
                
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
            self._prep_y_axis(**y_axis)

            # --- 11. Agregar lineas horizontales
            self.lineas_horizontales(**hlines)

            # --- 12. Agregar guias horizontales
            if show_hguide:
                self.guias_horizontales(mostrar_cero=False)

            # --- 13. Agregar leyenda
            if "show" not in legend:
                if bar_mode == "last":
                    legend["show"] = len(tickers) > 1 and (grouped or stacked)
                else:
                    legend["show"] = len(tickers) > 1

            self.add_legend(**legend)

            if bar_labels:
                self._bar_value_label_generate_dict(label_dict=bar_labels)

            if bar_tags:
                self._bar_tag_generate_dict(tag_dict=bar_tags)


            # --- 14. Ajuste de layout igual que graph_line
            if self._x_axis_mode == "bbg":
                self._fig.subplots_adjust(
                    left=0.15,
                    right=0.93,
                    top=0.80,
                    bottom=0.21
                )

    def graph_box_whiskers(
        self,
        # --- Configuración del gráfico ---
        figsize: tuple[float, float] = (6.00, 5.00),
        # --- Configuración de elementos adicionales ---
        titles: dict | None = None,
        source: str | list[str] | None = None,
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
        Grafica box & whiskers por columna.

        Supuesto principal:
        - dataframe.index = fechas
        - dataframe.columns = series (ej. múltiplos P/E)

        Cada caja resume la distribución histórica de una columna.

        Nuevas opciones:
        - show_range_tags: muestra etiquetas en el whisker superior/inferior
        - show_last_value: muestra el último valor histórico de cada serie
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

        # --- 7. Generación del gráfico y el plot en caso no exista
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        # --- 8. Agregar titulos globales
        self.set_titles(**titles)
        if source:
            self.add_source(source)

        # --- 9. Manejo del eje x
        db = self._prep_x_axis(dataframe=db, **x_axis)
        
        #overide el eje a categorico para este tipo de grafico
        self._x_axis_mode = "categorical"

        # --- 10. preparar datos para el boxplot
        data_plot = [db[t].dropna().values for t in tickers]

        # --- 11. Funciones de ayuda para los elementos del boxplot
        def _median(
                color: str = "#222222",
                lw: float = 1.5,
        ):
            return locals()
        
        def _whisker(
                color: str = "#6E6E6E",
                lw: float = 0.5,
        ):
            return locals()

        def _cap(
                color: str = "#6E6E6E",
                lw: float = 0.5,
        ):
            return locals()

        def _box(
                color: str = "#6E6E6E",
                lw: float = 0.5,
        ):
            return locals()

        def _fliers(
                marker: str = "o",
                markersize: float = 3.5,
                markerfacecolor: str = "#999999",
                markeredgecolor: str = "#999999",
                alpha: float = 0.85,
        ):
            return locals()         
        
        def _mean(
                color: str = "#404040",
                lw: float = 0.5,
                linestyle: str = "--"
        ):
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
        self.lineas_horizontales(**hlines)

        if show_hguide:
            self.guias_horizontales(mostrar_cero=False)

        self._prep_y_axis(**y_axis)

        # source
        if isinstance(source, str):
            self.add_source(source, color="#454444")
        elif isinstance(source, list) and len(source) > 1:
            self.add_source(source, fontsize=5, color="#454444")
        elif isinstance(source, list) and len(source) <= 1:
            self.add_source(source, color="#454444")

