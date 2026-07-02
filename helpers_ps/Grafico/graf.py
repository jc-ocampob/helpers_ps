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
import matplotlib.patheffects as path_effects
from helpers_ps.Config.var_globs import PALETA_COLORES
from importlib.resources import files

# -----------------------
# Setteo de parametros iniciales
# -----------------------

warnings.filterwarnings("ignore")

# Register Inter font with matplotlib


# Rebuild font cache
fm._load_fontmanager(try_read_cache=False)

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

    # Meta data de leyenda
    _custom_legend_handles: list = None

    def __post_init__(self):
        self.dataframe = [self.dataframe] if isinstance(self.dataframe, pd.DataFrame) else self.dataframe

    # funcion para poder actualizar el metadata hacia _meta_data
    def _set_axis(self, ax_index: int = 0) -> None:
        """
        Select active axis when working with multiple subplots.

        Guarda la metadata del eje actual antes de cambiar al nuevo eje,
        incluyendo custom legend handles por subplot.
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
                "ticker_label_color": None,
                "custom_legend_handles": []
            }
            for i, ax in enumerate(self._axes)
        }

        # Metadata activa del primer eje
        self._custom_legend_handles = []

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
        """
        Función para poder agregar titulos y subtitulos a las gráficas

        Parameters
        -----------
        title: str | None
            Titulo principal de la grafica
        title_font_size: int
            Tamaño de fuente del titulo principal
        subtitle: str | None
            Subtitulo de la grafica
        subtitle_font_size: int
            Tamaño de fuente del subtitulo
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
        Agrega la fuente al grafico

        Parameters
        -----------
        text: str | list | None
            Texto de la fuente. Puede ser un string o una lista de strings (como máximo 3 elementos en la lista).
        x: float
            Posición horizontal de la fuente en coordenadas de la figura (0 a 1).
        y: float
            Posición vertical de la fuente en coordenadas de la figura (0 a 1).
        fontsize: float
            Tamaño de fuente de la fuente.
        color: str
            Color del texto de la fuente.
        line_spacing: float
            Espaciado entre líneas de la fuente.
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
        Función para agregar leyenda a la gráfica si se llama de despues de ingresar nuevos scatters y elementos a la leyenda estos se graficaran en la leyenda.

        Parameters
        -----------
        show: bool
            Indica si se debe mostrar la leyenda o no.
        loc: str
            Ubicación de la leyenda.
        bbox_to_anchor: tuple
            Ancla para la posición de la leyenda.
        ncol: int
            Número de columnas en la leyenda.
        fontsize: int
            Tamaño de fuente de la leyenda.
        frameon: bool
            Indica si se debe mostrar el marco de la leyenda.
        edgecolor: str
            Color del borde de la leyenda.
        facecolor: str
            Color de fondo de la leyenda.
        framealpha: float
            Transparencia del marco de la leyenda.
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

    # =========================
    # Metodos de la figura general
    # =========================
    def show(self) -> None:
        """
        Funcion para mostrar la figura.
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
        Guarda la figura actual en un dict de buffers en memoria como BytesIO. Esto permite almacenar múltiples figuras en memoria sin escribirlas en disco.

        Parameters
        -----------
        dir: dict
            Diccionario donde se guardará la figura. Por defecto es el diccionario global 'buffers'.
        name: str
            Nombre con el que se guardará la figura en el diccionario.
        dpi: int
            Resolución de la imagen guardada.
        reset_buffers: bool
            Indica si se deben reiniciar los buffers y metadata de la clase después de guardar la figura.
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
        Agrega título y subtítulo a nivel de figura.

        Este método limpia el título propio del eje activo y agrega el título
        principal y subtítulo usando coordenadas relativas a la figura. Esto
        permite mantener una ubicación consistente para todos los gráficos.

        Parameters
        ----------
        title : str or None, default None
            Título principal del gráfico. Si es ``None`` o vacío, no se agrega
            título principal.

        title_font_size : int, default 12
            Tamaño de fuente del título principal.

        subtitle : str or None, default None
            Subtítulo del gráfico. Si es ``None`` o vacío, no se agrega subtítulo.

        subtitle_font_size : int, default 9
            Tamaño de fuente del subtítulo.

        Returns
        -------
        None
            Modifica la figura activa agregando texto a nivel de figura.

        Examples
        --------
        ```python
        g.set_titles(
            title="Evolución del S&P 500",
            subtitle="Índice en puntos"
        )
        ```
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
        Dibujar guías horizontales en el eje y del gráfico activo. Se puede elegir si mostrar o no la línea en y=0.
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
        Función para agregar etiquetas a los graficos que maneja de manera automatica cualquier tipo de eje x
        
        Parameters
        -----------
        x_value: float | str | datetime
            Valor en el eje x donde se colocará la etiqueta.
        y_value: float
            Valor en el eje y donde se colocará la etiqueta.
        label: str
            Texto de la etiqueta.
        label_h_align: str
            Alineación horizontal del texto de la etiqueta ('left', 'center', 'right').
        label_v_align: str
            Alineación vertical del texto de la etiqueta ('top', 'center', 'bottom').
        ubic_etq: tuple
            Desplazamiento de la etiqueta en puntos (x_offset, y_offset) desde (x_value, y_value).
        fontsize: int
            Tamaño de la fuente del texto de la etiqueta.
        fontweight: str
            Peso de la fuente del texto de la etiqueta.
        font_color: str
            Color del texto de la etiqueta.
        bg_color: str
            Color de fondo de la etiqueta.
        bg_alpha: float
            Transparencia del fondo de la etiqueta (0.0 a 1.0).
        edge_color: str
            Color del borde del fondo de la etiqueta.
        show_bbox: bool
            Indica si se debe mostrar el fondo de la etiqueta.
        text_edge_color: str | None
            Color del borde del texto de la etiqueta para mejorar la legibilidad sobre fondos ocupados. Si es None, no se aplica borde.
        text_edge_width: float
            Ancho del borde del texto de la etiqueta. Si es 0, no se aplica borde.
        zorder: int
            Orden de apilamiento de la etiqueta en el gráfico. Valores más altos se dibujan encima de valores más bajos.
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
        Función para agregar un punto en el gráfico que maneja de manera automatica cualquier tipo de eje x

        Parameters
        -----------
        x_value: float | str | datetime
            Valor en el eje x donde se colocará el punto.
        y_value: float
            Valor en el eje y donde se colocará el punto.
        color: str
            Color del punto.
        size: float
            Tamaño del punto.
        zorder: int
            Orden de apilamiento del punto en el gráfico. Valores más altos se dibujan encima de valores más bajos.
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
        Función para agregar un sombreado vertical en el gráfico que maneja de manera automatica cualquier tipo de eje x.

        Parameters
        -----------
        periods: list[tuple] | tuple
            Lista de tuplas (start, end) que definen los periodos a sombrear. Cada tupla puede contener valores de fecha, string o numéricos.
        color: str
            Color del sombreado.
        alpha: float
            Transparencia del sombreado (0.0 a 1.0).
        zorder: int
            Orden de apilamiento del sombreado en el gráfico. Valores más altos se dibujan encima de valores más bajos.
        label: str | None
            Etiqueta para el sombreado, que puede aparecer en la leyenda.
        hatch: str | None
            Patrón de sombreado (hatch) para el área sombreada.
        ymin: float
            Valor mínimo en el eje y para el sombreado.
        ymax: float
            Valor máximo en el eje y para el sombreado.
        clip_to_xlim: bool
            Indica si el sombreado debe recortarse a los límites actuales del eje x.
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
            Devuelve todos los rectángulos válidos asociados a la categoría idx.
            Funciona para barras simples, grouped y stacked.
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
            Obtiene los bordes izquierdo y derecho reales del cluster de barras
            para la categoría idx.
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
        Función para agregar líneas horizontales en el gráfico.

        Parameters
        -----------
        y_values: list[float] | float | None
            Lista de valores y donde se dibujarán las líneas horizontales. Si es un solo valor, se convertirá en una lista.
        linestyle: str | None
            Estilo de línea para las líneas horizontales (por ejemplo, '-', '--', '-.', ':'). Si es None, se usará el estilo predeterminado.
        linewidth: float
            Ancho de línea para las líneas horizontales.
        color: str
            Color de las líneas horizontales.
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
        Función para agregar recesiones a la gráfica. Se puede elegir el país y si se desea obtener el DataFrame de recesiones en lugar de graficarlas.

        Parameters
        -----------
        country: str
            Nombre del país para el cual se desean agregar las recesiones. Por defecto es "United States".
        data_frame: bool
            Si es True, la función devolverá un DataFrame con las recesiones en lugar de graficarlas. Por defecto es False.
        controles: dict
            Diccionario de controles para personalizar el sombreado de las recesiones. Herada todos los parametros de shade_x. Por defecto es None, lo que aplicará color gris y alpha 0.3.
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
                tag :{
                    loc_offset: offset para el tag relativo al punto original
                    font_color: color de la fuente
                    font_size: tamaño de la fuente
                    bg_color: color de fondo del tag
                }
                    
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

        if not hasattr(self, "_custom_legend_handles"):
            self._custom_legend_handles = []

        existing_labels = {h.get_label() for h in self._custom_legend_handles}

        
        # una vez validado la información generar los puntos en base a las variables de control

        def _generate(
                ticker,
                x_values: list[str | float | int] | str = "last",
                show: str = "dot",
                template: str = "{ticker}\n{x_value:%B-%Y}: {y_value:,.2f}",
                tag: dict | None = None,
                dot: dict | None = None,
                legend_label: str | None = None,
        ):

            # Validar que es un ticker valido
            if ticker not in df.columns:
                raise ValueError(f"El ticker {ticker} no es una columna disponible en el dataframe")
            
            tag = dict() if tag is None else tag.copy()
            dot = dict() if dot is None else dot.copy()
            
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

                dot_color = dot.get("color")

                if dot_color is None:
                    dot_color = _ticker_label_color[0][2]

                if legend_label is not None and legend_label not in existing_labels:
                    self._custom_legend_handles.append(
                        Line2D(
                            [0],
                            [0],
                            marker="o",
                            linestyle="None",
                            color="none",
                            markerfacecolor=dot_color,
                            markeredgecolor=dot_color,
                            markersize=np.sqrt(dot.get("size", 30)),
                            label=legend_label,
                        )
                    )
                    existing_labels.add(legend_label)

                if "tag" in show:
                    if tag.get("font_color") is None:
                        tag["font_color"] = _ticker_label_color[0][2]
                    self.etiqueta_valor(
                        label=template.format(x_value=x, y_value=y, ticker=ticker),
                        x_value=x,          # datetime real para texto "Mar 26: 4.3"
                        y_value=y,
                        **tag
                        )
                
                if "dot" in show:
                    if dot.get("color") is None:
                        dot["color"] = _ticker_label_color[0][2]
                    self.punto_valor(
                        x_value=x,
                        y_value=y,
                        **dot
                    )

        for ti in control_dict.keys():
            _temp_controls = control_dict[ti]
            _generate(**_temp_controls)

class Bar_tags:
    """
    Mixin con utilidades para agregar etiquetas, tags y anotaciones sobre gráficos de barras.

    Esta clase depende de metadata generada previamente por `graph_bar`, principalmente:
    - self._bars_data: almacena los objetos BarContainer/rectángulos por ticker.
    - self._bars_x_reference: almacena los valores originales del eje x.
    - self._ticker_label_color: relación ticker, etiqueta visible y color.

    Soporta barras:
    - simples
    - agrupadas
    - stacked con componentes positivos y negativos
    - modo time
    - modo last/categórico
    """

    def _bar_x_key_normalize(self, value):
        """
        Normaliza valores del eje x para comparaciones consistentes.

        Convierte fechas compatibles a `pd.Timestamp`. Si no puede convertir el valor,
        lo transforma a string. Esto permite comparar de forma robusta fechas, strings
        y categorías al resolver `x_values`.

        Parameters
        ----------
        value : Any
            Valor del eje x a normalizar.

        Returns
        -------
        pd.Timestamp | str
            Valor normalizado.
        """
        try:
            if isinstance(value, (pd.Timestamp, np.datetime64)):
                return pd.Timestamp(value)
            return pd.Timestamp(value)
        except Exception:
            return str(value)

    def _bar_resolve_x_indices(self, ticker: str, x_values) -> list:
        """
        Resuelve valores del eje x a posiciones enteras dentro del gráfico de barras.

        Soporta:
        - "all": todas las posiciones.
        - "last": última barra no vacía del ticker.
        - lista/tupla/set: valores específicos del índice original.

        Parameters
        ----------
        ticker : str
            Columna/ticker objetivo.
        x_values : str | list | tuple | set
            Valores a resolver. Puede ser "all", "last" o una colección de valores.

        Returns
        -------
        list[int]
            Lista de posiciones enteras del eje x.

        Raises
        ------
        ValueError
            Si no existe metadata de barras o si `x_values` tiene formato inválido.
        """
        if not hasattr(self, "_bars_x_reference"):
            raise ValueError(
                "No existe self._bars_x_reference. Guarda la referencia del eje x dentro de graph_bar."
            )

        x_ref = list(self._bars_x_reference)
        x_ref_norm = [self._bar_x_key_normalize(v) for v in x_ref]

        if x_values is None:
            x_values = "last"

        if x_values == "all":
            return list(range(len(x_ref)))

        if x_values == "last":
            bars_entry = self._bars_data.get(ticker)

            if bars_entry is None:
                return []

            for idx in range(len(x_ref) - 1, -1, -1):
                rect, _mode = self._bar_get_rect_for_index(
                    bars_entry=bars_entry,
                    idx=idx
                )

                if rect is None:
                    continue

                h = rect.get_height()

                if h is not None and not np.isnan(h) and abs(h) > 0:
                    return [idx]

            return [len(x_ref) - 1] if len(x_ref) > 0 else []

        if not isinstance(x_values, (list, tuple, set)):
            raise ValueError(
                "x_values debe ser 'all', 'last' o una lista/tupla/set de fechas/categorías."
            )

        requested = {self._bar_x_key_normalize(v) for v in x_values}

        return [
            i for i, v in enumerate(x_ref_norm)
            if v in requested
        ]

    def _bar_get_rect_for_index(self, bars_entry: dict, idx: int):
        """
        Obtiene el rectángulo asociado a un ticker y una posición del eje x.

        Para barras grouped/simples retorna directamente el rectángulo.
        Para barras stacked revisa primero el segmento positivo y luego el negativo.

        Parameters
        ----------
        bars_entry : dict
            Entrada de `self._bars_data` para un ticker.
        idx : int
            Posición del eje x.

        Returns
        -------
        tuple
            `(rect, mode)` donde:
            - rect es el Rectangle de matplotlib o None.
            - mode es "grouped" o "stacked".
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

            if (
                rect_pos is not None
                and h_pos is not None
                and not np.isnan(h_pos)
                and abs(h_pos) > 0
            ):
                return rect_pos, "stacked"

            if (
                rect_neg is not None
                and h_neg is not None
                and not np.isnan(h_neg)
                and abs(h_neg) > 0
            ):
                return rect_neg, "stacked"

            return None, "stacked"

        # --- grouped / single
        if idx < len(bars_obj):
            return bars_obj[idx], "grouped"

        return None, "grouped"

    def _bar_get_stack_total_anchor(self, idx: int, ref_ticker: str):
        """
        Calcula la posición de anclaje para etiquetar el total de un stack.

        Suma todos los componentes positivos y negativos de una posición.
        El ancla se coloca arriba del stack positivo si el total es positivo,
        o abajo del stack negativo si el total es negativo.

        Parameters
        ----------
        idx : int
            Posición del eje x.
        ref_ticker : str
            Ticker usado como referencia para obtener la posición x del stack.

        Returns
        -------
        tuple
            `(x, y_anchor, total_value, sign)` donde:
            - x: posición horizontal del stack.
            - y_anchor: punto vertical donde se ancla el tag.
            - total_value: suma total del stack.
            - sign: "positive" o "negative".
        """
        if ref_ticker not in self._bars_data:
            return None, None, None, None

        total_value = 0.0
        top_positive = 0.0
        bottom_negative = 0.0

        ref_rect, ref_mode = self._bar_get_rect_for_index(
            self._bars_data[ref_ticker],
            idx
        )

        if ref_rect is None:
            return None, None, None, None

        if ref_mode != "stacked":
            raise ValueError(
                "El total del stack solo aplica cuando el gráfico es stacked."
            )

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
                    top_positive = max(
                        top_positive,
                        rect_pos.get_y() + rect_pos.get_height()
                    )

            if rect_neg is not None:
                h = rect_neg.get_height()

                if h is not None and not np.isnan(h):
                    total_value += h
                    bottom_negative = min(
                        bottom_negative,
                        rect_neg.get_y() + rect_neg.get_height()
                    )

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
        Formatea el texto de una etiqueta/tag de barras.

        Placeholders disponibles:
        - {ticker}
        - {label}
        - {x_value}
        - {y_value}
        - {total_value}

        Parameters
        ----------
        template : str
            Template de texto.
        ticker : str
            Ticker original.
        x_value : Any
            Valor original del eje x.
        y_value : float | None
            Valor de la barra o segmento.
        total_value : float | None
            Total del stack, si aplica.
        label : str | None
            Etiqueta visible asociada al ticker.

        Returns
        -------
        str
            Texto formateado.
        """
        return template.format(
            ticker=ticker,
            label=label if label is not None else ticker,
            x_value=x_value,
            y_value=y_value,
            total_value=total_value
        )

    def _bar_label_generate_dict(self, label_dict: dict | None = None) -> None:
        """
        Genera etiquetas y tags sobre barras usando una única configuración tipo dict.

        Esta función reemplaza y combina:
        - `_bar_value_label_generate_dict`
        - `_bar_tag_generate_dict`

        Tipos soportados mediante `show`:
        - "value_label":
            Etiqueta numérica estándar.
            En barras grouped/simples se ubica al final de la barra.
            En barras stacked se ubica al centro del segmento.
        - "bar_tag":
            Tag libre al centro de la barra o segmento.
        - "stack_total":
            Tag sobre el total del stack. Solo aplica para gráficos stacked.

        Estructura esperada:
        {
            "etiqueta_1": dict(
                ticker="PX_LAST-SPX INDEX",
                x_values="last",                    # "last", "all" o lista de valores
                show="value_label",                 # value_label | bar_tag | stack_total
                template="{y_value:,.1f}",
                tag=dict(
                    fontsize=7,
                    font_color="black",
                    fontweight="normal",
                    bg_color="white",
                    edge_color="#D9D9D9",
                    show_bbox=True,
                    ubic_etq=(0, 5),
                    zorder=7
                )
            )
        }

        Parameters
        ----------
        label_dict : dict | None
            Diccionario de configuración de etiquetas/tags.

        Returns
        -------
        None
        """
        if not label_dict:
            return None

        if not hasattr(self, "_bars_data") or not self._bars_data:
            raise ValueError(
                "No existe self._bars_data. Ejecuta graph_bar antes de usar este helper."
            )

        ticker_to_label = {}

        if hasattr(self, "_ticker_label_color") and self._ticker_label_color is not None:
            for t, lbl, _c in self._ticker_label_color:
                ticker_to_label[t] = lbl

        x_ref = list(self._bars_x_reference)

        def _safe_offset(tag: dict, default: tuple[float, float]) -> tuple[float, float]:
            """
            Obtiene `ubic_etq` de forma segura.
            """
            ubic = tag.get("ubic_etq", default)

            if ubic is None:
                return default

            return ubic

        def _control(
            ticker: str | None = None,
            show: str = "value_label",
            x_values: list[str | int | float] | str | None = "last",
            template: str = "{y_value:,.2f}",
            tag: dict | None = None,
        ):
            """
            Procesa una entrada individual del diccionario de configuración.
            """
            if not ticker:
                return None

            if ticker not in self._bars_data:
                return None

            tag = dict() if tag is None else tag.copy()

            idxs = self._bar_resolve_x_indices(
                ticker=ticker,
                x_values=x_values
            )

            for idx in idxs:
                x_value = x_ref[idx]
                label = ticker_to_label.get(ticker, ticker)

                # ======================================================
                # 1. TAG SOBRE TOTAL DEL STACK
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
                        tag["label_v_align"] = tag.get("label_v_align", "bottom")
                        ox, oy = _safe_offset(tag, (0, 5))
                        tag["ubic_etq"] = (ox, abs(oy))
                    else:
                        tag["label_v_align"] = tag.get("label_v_align", "top")
                        ox, oy = _safe_offset(tag, (0, -5))
                        tag["ubic_etq"] = (ox, -abs(oy))

                    self.etiqueta_valor(
                        x_value=x,
                        y_value=y_anchor,
                        label=text,
                        **tag
                    )

                    continue

                # ======================================================
                # 2. VALUE LABEL O BAR TAG SOBRE BARRA / SEGMENTO
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
                y_segment_center = rect.get_y() + rect.get_height() / 2.0
                y_end = rect.get_y() + rect.get_height()

                text = self._bar_format_template(
                    template=template,
                    ticker=ticker,
                    x_value=x_value,
                    y_value=h,
                    total_value=None,
                    label=label
                )

                # ------------------------------------------------------
                # 2A. Etiqueta numérica estándar
                # ------------------------------------------------------
                if show == "value_label":
                    # stacked: centro del segmento
                    if mode == "stacked":
                        ox, oy = _safe_offset(tag, (0, 0))
                        tag["ubic_etq"] = (ox, oy)

                        self.etiqueta_valor(
                            x_value=x,
                            y_value=y_segment_center,
                            label=text,
                            **tag
                        )

                    # grouped/single: final de la barra
                    else:
                        if h >= 0:
                            tag["label_v_align"] = tag.get("label_v_align", "bottom")
                            ox, oy = _safe_offset(tag, (0, 3))
                            tag["ubic_etq"] = (ox, abs(oy))
                        else:
                            tag["label_v_align"] = tag.get("label_v_align", "top")
                            ox, oy = _safe_offset(tag, (0, -3))
                            tag["ubic_etq"] = (ox, -abs(oy))

                        self.etiqueta_valor(
                            x_value=x,
                            y_value=y_end,
                            label=text,
                            **tag
                        )

                    continue

                # ------------------------------------------------------
                # 2B. Tag libre al centro de barra / segmento
                # ------------------------------------------------------
                if show == "bar_tag":
                    ox, oy = _safe_offset(tag, (0, 0))
                    tag["ubic_etq"] = (ox, oy)

                    self.etiqueta_valor(
                        x_value=x,
                        y_value=y_segment_center,
                        label=text,
                        **tag
                    )

                    continue

                raise ValueError(
                    "show debe ser uno de: 'value_label', 'bar_tag', 'stack_total'."
                )

        for _key, cfg in label_dict.items():
            _control(**cfg)

    # ---------------------------------------------------------------------
    # Backward compatibility wrappers
    # ---------------------------------------------------------------------
    def _bar_value_label_generate_dict(self, label_dict: dict | None = None) -> None:
        """
        Wrapper de compatibilidad para código antiguo.

        Convierte internamente cada entrada a `show='value_label'` y delega
        la ejecución a `_bar_label_generate_dict`.

        Parameters
        ----------
        label_dict : dict | None
            Configuración antigua de etiquetas de valor.

        Returns
        -------
        None
        """
        if not label_dict:
            return None

        new_dict = {}

        for k, cfg in label_dict.items():
            cfg_new = cfg.copy()
            cfg_new.setdefault("show", "value_label")
            new_dict[k] = cfg_new

        return self._bar_label_generate_dict(new_dict)

    def _bar_tag_generate_dict(self, tag_dict: dict | None = None) -> None:
        """
        Wrapper de compatibilidad para código antiguo.

        Mantiene la lógica antigua de `bar_tags`, pero delega el trabajo a
        `_bar_label_generate_dict`.

        Si una entrada no trae `show`, se asume `show='bar_tag'`.

        Parameters
        ----------
        tag_dict : dict | None
            Configuración antigua de tags de barras.

        Returns
        -------
        None
        """
        if not tag_dict:
            return None

        new_dict = {}

        for k, cfg in tag_dict.items():
            cfg_new = cfg.copy()
            cfg_new.setdefault("show", "bar_tag")
            new_dict[k] = cfg_new

        return self._bar_label_generate_dict(new_dict)

class Pie_tags():

    def _pie_format_template(
        self,
        template: str,
        ticker: str,
        value: float,
        pct: float,
        label: str | None = None,
    ) -> str:

        return template.format(
            ticker=ticker,
            label=label if label is not None else ticker,
            value=value,
            pct=pct,
        )

    def _pie_get_anchor(
        self,
        ticker: str,
        radius: float = 0.7,
    ):

        if not hasattr(self, "_pie_data"):
            raise ValueError(
                "No existe self._pie_data. Ejecuta graph_pie antes de usar este helper."
            )

        if ticker not in self._pie_data:
            return None

        wedge = self._pie_data[ticker]["wedge"]

        theta = (wedge.theta1 + wedge.theta2) / 2.0
        theta_rad = np.deg2rad(theta)

        x = radius * np.cos(theta_rad)
        y = radius * np.sin(theta_rad)

        return x, y

    def _pie_value_label_generate_dict(
        self,
        label_dict: dict | None = None,
    ) -> None:

        if not label_dict:
            return

        if not hasattr(self, "_pie_data"):
            raise ValueError(
                "No existe self._pie_data. Ejecuta graph_pie antes de usar este helper."
            )

        ticker_to_label = {}

        if hasattr(self, "_ticker_label_color"):
            for t, lbl, _c in self._ticker_label_color:
                ticker_to_label[t] = lbl

        def _control(
            ticker: str | None = None,
            template: str = "{pct:.1f}%",
            radius: float = 0.65,
            font_color: str = "black",
            fontsize: int = 8,
            bg_color: str = "None",
            fontweight: str = "normal",
            label_h_align="center",
            label_v_align="center",
            ubic_etq=(0, 0),
            bg_alpha=1.0,
            edge_color="none",
            show_bbox=True,
            text_edge_color: str | None = None,
            text_edge_width: float = 0.0,
            zorder=6,
        ):

            if not ticker:
                return

            if ticker not in self._pie_data:
                return

            value = self._pie_data[ticker]["value"]
            pct = self._pie_data[ticker]["pct"]

            label = ticker_to_label.get(ticker, ticker)

            x, y = self._pie_get_anchor(
                ticker=ticker,
                radius=radius,
            )

            text = self._pie_format_template(
                template=template,
                ticker=ticker,
                value=value,
                pct=pct,
                label=label,
            )

            self.etiqueta_valor(
                x_value=x,
                y_value=y,
                label=text,
                ubic_etq=ubic_etq,
                bg_color=bg_color,
                font_color=font_color,
                fontsize=fontsize,
                fontweight=fontweight,
                bg_alpha=bg_alpha,
                edge_color=edge_color,
                show_bbox=show_bbox,
                text_edge_color=text_edge_color,
                text_edge_width=text_edge_width,
                zorder=zorder,
                label_h_align=label_h_align,
                label_v_align=label_v_align,
            )

        for _, cfg in label_dict.items():
            _control(**cfg)

    def _pie_tag_generate_dict(
        self,
        tag_dict: dict | None = None,
    ) -> None:

        if not tag_dict:
            return

        if not hasattr(self, "_pie_data"):
            raise ValueError(
                "No existe self._pie_data. Ejecuta graph_pie antes de usar este helper."
            )

        ticker_to_label = {}

        if hasattr(self, "_ticker_label_color"):
            for t, lbl, _c in self._ticker_label_color:
                ticker_to_label[t] = lbl

        def _control(
            ticker: str | None = None,
            template: str = "{label}\n{pct:.1f}%",
            radius: float = 1.15,
            font_color: str = "black",
            fontsize: int = 8,
            bg_color: str = "white",
            fontweight: str = "normal",
            label_h_align="center",
            label_v_align="center",
            ubic_etq=(0, 0),
            bg_alpha=1.0,
            edge_color="#BFBFBF",
            show_bbox=True,
            text_edge_color: str | None = None,
            text_edge_width: float = 0.0,
            zorder=7,
        ):

            if not ticker:
                return

            if ticker not in self._pie_data:
                return

            value = self._pie_data[ticker]["value"]
            pct = self._pie_data[ticker]["pct"]

            label = ticker_to_label.get(ticker, ticker)

            x, y = self._pie_get_anchor(
                ticker=ticker,
                radius=radius,
            )

            text = self._pie_format_template(
                template=template,
                ticker=ticker,
                value=value,
                pct=pct,
                label=label,
            )

            self.etiqueta_valor(
                x_value=x,
                y_value=y,
                label=text,
                ubic_etq=ubic_etq,
                bg_color=bg_color,
                font_color=font_color,
                fontsize=fontsize,
                fontweight=fontweight,
                bg_alpha=bg_alpha,
                edge_color=edge_color,
                show_bbox=show_bbox,
                text_edge_color=text_edge_color,
                text_edge_width=text_edge_width,
                zorder=zorder,
                label_h_align=label_h_align,
                label_v_align=label_v_align,
            )

        for _, cfg in tag_dict.items():
            _control(**cfg)

class BoxW_tags():
    def _box_whiskers_label_generate(
        self,
        control_dict: dict = None,
    ) -> None:
        
        if control_dict is None:
            return None

        df = self._df
        columns = df.columns.tolist()

        # ---------------------------------------------------------
        # Custom legend handles para puntos de box & whiskers
        # ---------------------------------------------------------
        if not hasattr(self, "_custom_legend_handles"):
            self._custom_legend_handles = []

        existing_labels = {h.get_label() for h in self._custom_legend_handles}

        def _generate(
                ticker,
                x_values: list[str | float | int] | str = "last",
                show: str = "dot",       # dot | tag | dot_tag
                template: str = "{y_value:,.2f}",
                tag: dict | None = None,
                dot: dict | None = None,
                legend_label: str | None = None,
                legend_marker: str = "o",
        ):
            """
            Genera puntos y/o etiquetas sobre un box & whiskers.

            Estructura esperada:
            {
                "grupo_1": {
                    "ticker": "SPX",
                    "x_values": "last",
                    "show": "dot_tag",
                    "template": "{y_value:,.1f}",
                    "legend_label": "Último valor",
                    "dot": {
                        "color": "#E4572E",
                        "size": 45,
                        "zorder": 8
                    },
                    "tag": {
                        "ubic_etq": (20, 0),
                        "fontsize": 7,
                        "bg_color": "white",
                        "edge_color": "#D9D9D9",
                        "show_bbox": True
                    }
                }
            }
            """

            # -----------------------------------------------------
            # Validaciones
            # -----------------------------------------------------
            if ticker not in columns:
                raise ValueError(f"El ticker {ticker} no es una columna disponible en el dataframe")
            
            tag = dict() if tag is None else tag.copy()
            dot = dict() if dot is None else dot.copy()

            # Posición categórica del boxplot
            z_value = columns.index(ticker) + 1

            # Color base del ticker
            _ticker_label_color = [dd for dd in self._ticker_label_color if dd[0] == ticker]

            if len(_ticker_label_color) == 0:
                raise ValueError(f"No se encontró metadata de color para el ticker {ticker}")

            ticker_color = _ticker_label_color[0][2]

            # -----------------------------------------------------
            # Defaults heredados para tag y dot
            # -----------------------------------------------------
            if tag.get("font_color") is None:
                tag["font_color"] = ticker_color

            if dot.get("color") is None:
                dot["color"] = ticker_color

            if dot.get("size") is None:
                dot["size"] = 30

            if dot.get("zorder") is None:
                dot["zorder"] = 5

            # -----------------------------------------------------
            # Handle artificial para leyenda, sin tocar punto_valor
            # -----------------------------------------------------
            if legend_label is not None and legend_label not in existing_labels:

                self._custom_legend_handles.append(
                    Line2D(
                        [0],
                        [0],
                        marker=legend_marker,
                        linestyle="None",
                        color="none",
                        markerfacecolor=dot.get("color"),
                        markeredgecolor=dot.get("color"),
                        markersize=np.sqrt(dot.get("size", 30)),
                        label=legend_label,
                    )
                )

                existing_labels.add(legend_label)

            # -----------------------------------------------------
            # Resolver pares x/y/z
            # -----------------------------------------------------
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

            else:
                raise ValueError("x_values debe ser 'last' o una lista de valores del índice.")

            # -----------------------------------------------------
            # Graficar puntos y/o etiquetas
            # -----------------------------------------------------
            for pair in xyz_pairs:
                x, y, z = pair

                if "tag" in show:
                    self.etiqueta_valor(
                        label=template.format(
                            x_value=x,
                            y_value=y,
                            ticker=ticker
                        ),
                        x_value=z,
                        y_value=y,
                        **tag
                    )

                if "dot" in show:
                    self.punto_valor(
                        x_value=z,
                        y_value=y,
                        **dot
                    )

        for ti in control_dict.keys():
            _temp_controls = control_dict[ti]
            _generate(**_temp_controls)
        
@dataclass
class Graph_mtplt(Graph_base, Line_tags, Bar_tags, Pie_tags, BoxW_tags):

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
        Grafico de torta/donut para una foto puntual del dataframe.

        x_value:
        - "last": usa la ultima fila disponible
        - cualquier valor del indice: usa esa fila
        - entero fuera del indice: usa posicion iloc
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
        source = source if source is not None else dict()

        # --- 7. Generación del gráfico y el plot en caso no exista
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        # --- 8. Agregar titulos globales
        self.set_titles(**titles)
        self.add_source(**source)

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
        self.horizontal_lines(**hlines)

        if show_hguide:
            self.guias_horizontales(mostrar_cero=False)

        self._prep_y_axis(**y_axis)

        self.add_legend(**legend)
