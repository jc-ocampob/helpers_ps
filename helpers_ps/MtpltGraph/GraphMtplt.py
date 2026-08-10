from __future__ import annotations

import matplotlib.patheffects as path_effects
import numpy as np
import pandas as pd
from typing import Self
from .models import (
    XAxisConfig,
    YAxisConfig,
    LegendConfig,
    FigureTitle,
    FigureSubtitle,
    FigureSource,
    coerce_configs,
)

from .tags._colors import PALETA_COLORES

from .base import GraphBase
from .tags import (
    LineTags,
    BoxWTags,
    BarTags,
    PieTags
)
from .charts import (
    LineChartMixin,
    BarChartMixin
)


class GraphMtplt(

    # Tag management
    GraphBase,
    LineTags,
    BarTags,
    PieTags,
    BoxWTags,

    # Chart graphing
    LineChartMixin,
    BarChartMixin
):
    """
    High-level Matplotlib chart builder for institutional reporting.

    This class combines the base plotting utilities with chart-specific mixins
    for line, bar, pie, and box-and-whisker charts. It is designed to provide a
    consistent API for creating presentation-ready graphs using one or multiple
    pandas DataFrames.

    The class manages internal figure, axis, dataframe, x-axis, bar, and legend
    metadata so that chart methods can share common formatting, annotation, and
    layout logic.

    Parameters
    ----------
    dataframe : pandas.DataFrame, list[pandas.DataFrame], or None, optional
        Dataset used by the chart methods. A single DataFrame is internally
        converted into a list to keep a consistent dataframe selection interface.

    Attributes
    ----------
    dataframe : list[pandas.DataFrame] or None
        DataFrame collection available for plotting.
    _fig : matplotlib.figure.Figure or None
        Current Matplotlib figure.
    _ax : matplotlib.axes.Axes or None
        Active Matplotlib axis.
    _axes : matplotlib.axes.Axes or array-like or None
        Axis collection when using subplots.
    _df : pandas.DataFrame or None
        Active DataFrame selected for the current chart.
    _ticker_label_color : list[tuple]
        Internal mapping of ticker, display label, and color used by legends
        and annotations.
    """

    def __init__(self, dataframe: pd.DataFrame | list[pd.DataFrame] | None = None):
        """
        Initialize the chart builder with one or multiple DataFrames.

        Parameters
        ----------
        dataframe : pandas.DataFrame, list[pandas.DataFrame], or None, optional
            DataFrame or list of DataFrames used as input data for the chart methods.
            If a single DataFrame is provided, it is converted into a one-element
            list to standardize dataframe selection by index.

        Notes
        -----
        This initializer also resets all internal plotting metadata, including the
        active figure, axes, selected dataframe, x-axis configuration, bar metadata,
        and custom legend handles.
        """
        self.dataframe = [dataframe] if isinstance(dataframe, pd.DataFrame) else dataframe



    def graph_pie(
        self,
        figsize: tuple[float, float] = (6.00, 5.00),
        title: dict | FigureTitle | None = None,
        subtitle: dict | FigureSubtitle | None = None,
        source: dict | FigureSource | None = None,
        df_index: int = 0,
        tickers: list[str] | str = "all",
        labels: list[str] | tuple[str, ...] | dict | None = None,
        colors: list[str] | tuple[str, ...] | str | dict = PALETA_COLORES,
        donut_width: float | None = None,
        startangle: float = 90,
        counterclock: bool = False,
        autopct: str | None = "%1.1f%%",
        pctdistance: float = 0.72,
        labeldistance: float = 1.05,
        textprops: dict | None = None,
        wedgeprops: dict | None = None,
        legend: dict | LegendConfig | None = None,
        sort_values: bool = False,
        normalize: bool = True,
        text_edge_color: str | None = None,
        text_edge_width: float = 0.0,
        label_color: str = "black",
        autopct_color: str = "white",
    ) -> Self:
        """
        Create an institutional pie or donut chart from one selected DataFrame column.

        This method interprets the DataFrame index as the pie categories and the
        selected column as the pie values. Therefore, only one column can be used.

        Parameters
        ----------
        figsize : tuple[float, float], default (6.00, 5.00)
            Figure size in inches.
        title : dict, FigureTitle, or None, optional
            Figure-level title configuration passed to ``add_title``.
        subtitle : dict, FigureSubtitle, or None, optional
            Figure-level subtitle configuration passed to ``add_subtitle``.
        source : dict, FigureSource, or None, optional
            Figure-level source configuration passed to ``add_source``.
        df_index : int, default 0
            Index of the DataFrame to use when multiple DataFrames are available.
        tickers : str or list[str], default "all"
            Column to use as pie values. If "all" is used, the selected DataFrame
            must contain exactly one column. If a list is used, it must contain
            exactly one valid column.
        labels : list[str], tuple[str, ...], dict, or None, optional
            Labels used for the pie categories. If None, labels are generated from
            the DataFrame index. If a dictionary is provided, keys are matched
            against index category values or their string representation.
        colors : list[str], tuple[str, ...], str, or dict, default PALETA_COLORES
            Colors assigned to pie categories. If a dictionary is provided, keys are
            matched against index category values or their string representation.
        donut_width : float or None, optional
            Width of the donut ring. If provided, the pie chart is rendered as a
            donut chart.
        startangle : float, default 90
            Starting angle of the pie chart.
        counterclock : bool, default False
            Whether segments are drawn counterclockwise.
        autopct : str or None, default "%1.1f%%"
            Format string for percentage labels. Use None to hide them.
        pctdistance : float, default 0.72
            Radial distance of percentage labels from the center.
        labeldistance : float, default 1.05
            Radial distance of category labels from the center.
        textprops : dict or None, optional
            Text properties passed to Matplotlib pie labels.
        wedgeprops : dict or None, optional
            Wedge properties passed to Matplotlib pie segments.
        legend : dict, LegendConfig, or None, optional
            Legend configuration. If ``show=True``, a legend is displayed.
        sort_values : bool, default False
            Whether to sort categories in descending order before plotting.
        normalize : bool, default True
            Whether Matplotlib should normalize values to sum to one.
        text_edge_color : str or None, optional
            Stroke color applied to labels and percentage texts.
        text_edge_width : float, default 0.0
            Stroke width applied to labels and percentage texts.
        label_color : str, default "black"
            Color used for category labels.
        autopct_color : str, default "white"
            Color used for percentage labels.

        Returns
        -------
        Self
            The chart object, allowing chained calls.

        Raises
        ------
        TypeError
            If the selected dataframe is not a pandas DataFrame or if the input
            configuration types are invalid.
        ValueError
            If the selected DataFrame is empty, if more than one column is selected,
            if the selected column has no numeric values, if the selected column is
            not found, or if the index contains duplicated category labels.
        """

        # -------------------------------------------------
        # 1. Select dataframe and active AxisState
        # -------------------------------------------------
        db = self._select_df(df_idx=df_index)
        state = self._ensure_active_state()

        if db is None or not isinstance(db, pd.DataFrame):
            raise TypeError("`dataframe` must be a pandas DataFrame.")

        if db.empty:
            raise ValueError("Cannot create a pie chart from an empty DataFrame.")

        # -------------------------------------------------
        # 2. Resolve the selected value column
        # -------------------------------------------------
        if isinstance(tickers, str):
            if tickers == "all":
                if len(db.columns) != 1:
                    raise ValueError(
                        "`graph_pie()` requires exactly one value column. "
                        "Pass `tickers='column_name'` or provide a one-column DataFrame."
                    )
                value_column = db.columns[0]
            else:
                value_column = tickers

        elif isinstance(tickers, (list, tuple, set)):
            tickers_list = list(tickers)
            if len(tickers_list) != 1:
                raise ValueError(
                    "`graph_pie()` only supports one value column. "
                    "Pass a single column name in `tickers`."
                )
            value_column = tickers_list[0]

        else:
            raise TypeError(
                "`tickers` must be 'all', a string column name, or a one-item list."
            )

        if value_column not in db.columns:
            raise ValueError(f"Column not found in dataframe: {value_column}")

        # -------------------------------------------------
        # 3. Build category-value series
        # -------------------------------------------------
        serie = pd.to_numeric(db[value_column], errors="coerce")
        serie = serie.replace([np.inf, -np.inf], np.nan).dropna()

        if serie.empty:
            raise ValueError(
                f"The selected column `{value_column}` has no numeric values to plot."
            )

        if serie.index.has_duplicates:
            raise ValueError(
                "`graph_pie()` requires a unique DataFrame index because the index "
                "is used as pie categories and metadata keys."
            )

        if sort_values:
            serie = serie.sort_values(ascending=False)

        plot_categories = serie.index.tolist()
        plot_keys = [str(category) for category in plot_categories]

        # -------------------------------------------------
        # 4. Resolve labels from index categories
        # -------------------------------------------------
        if labels is None:
            plot_labels = [str(category) for category in plot_categories]

        elif isinstance(labels, dict):
            plot_labels = [
                labels.get(category, labels.get(str(category), str(category)))
                for category in plot_categories
            ]

        elif isinstance(labels, (list, tuple)):
            label_list = list(labels)
            if len(label_list) < len(plot_categories):
                plot_labels = label_list + [
                    str(category)
                    for category in plot_categories[len(label_list):]
                ]
            else:
                plot_labels = label_list[:len(plot_categories)]

        else:
            raise TypeError(
                "`labels` must be None, a list, a tuple, or a dictionary keyed by index category."
            )

        # -------------------------------------------------
        # 5. Resolve colors from index categories
        # -------------------------------------------------
        if isinstance(colors, str):
            plot_colors = [colors for _ in plot_categories]

        elif isinstance(colors, dict):
            plot_colors = [
                colors.get(
                    category,
                    colors.get(
                        str(category),
                        PALETA_COLORES[i % len(PALETA_COLORES)],
                    ),
                )
                for i, category in enumerate(plot_categories)
            ]

        elif isinstance(colors, (list, tuple)):
            color_list = list(colors)
            plot_colors = [
                color_list[i]
                if i < len(color_list)
                else PALETA_COLORES[i % len(PALETA_COLORES)]
                for i in range(len(plot_categories))
            ]

        else:
            plot_colors = [
                PALETA_COLORES[i % len(PALETA_COLORES)]
                for i in range(len(plot_categories))
            ]

        # -------------------------------------------------
        # 6. Store metadata in AxisState
        # -------------------------------------------------
        state.series_config = [
            {
                "ticker": value_column,
                "label": str(value_column),
                "color": plot_colors[0] if plot_colors else None,
                "axis_side": "left",
            }
        ]

        state.axis_map = {value_column: "left"}

        state.ticker_label_color = [
            (plot_keys[i], plot_labels[i], plot_colors[i])
            for i in range(len(plot_keys))
        ]

        state.x_axis_mode = "categorical"
        state.x_axis_fechas = None
        state.x_vals = np.arange(len(plot_categories), dtype=float)
        state.x_axis_metadata = {
            "mode": "categorical",
            "chart_type": "pie",
            "value_column": value_column,
            "categories": plot_categories,
            "labels": plot_labels,
        }

        # -------------------------------------------------
        # 7. Coerce configs
        # -------------------------------------------------
        configs = coerce_configs(
            title=(title, FigureTitle),
            subtitle=(subtitle, FigureSubtitle),
            source=(source, FigureSource),
            legend=(legend, LegendConfig),
        )

        title_cfg = configs["title"] if title is not None else None
        subtitle_cfg = configs["subtitle"] if subtitle is not None else None
        source_cfg = configs["source"] if source is not None else None
        legend_cfg = configs["legend"] if legend is not None else {}

        textprops = textprops if textprops is not None else {}
        wedgeprops = wedgeprops if wedgeprops is not None else {}

        if donut_width is not None:
            wedgeprops["width"] = donut_width

        # -------------------------------------------------
        # 8. Create figure if needed
        # -------------------------------------------------
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        self._ax.clear()

        if title_cfg is not None:
            self.add_title(**title_cfg)

        if subtitle_cfg is not None:
            self.add_subtitle(**subtitle_cfg)

        if source_cfg is not None:
            self.add_source(**source_cfg)

        # -------------------------------------------------
        # 9. Draw pie
        # -------------------------------------------------
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

        # -------------------------------------------------
        # 10. Store pie metadata in AxisState
        # -------------------------------------------------
        total = serie.sum()

        state.pie_data = {
            plot_keys[i]: {
                "category": plot_categories[i],
                "label": plot_labels[i],
                "color": plot_colors[i],
                "column": value_column,
                "wedge": pie_out[0][i],
                "value": serie.iloc[i],
                "pct": (serie.iloc[i] / total * 100.0) if total else 0.0,
            }
            for i in range(len(plot_keys))
        }

        # -------------------------------------------------
        # 11. Style labels and percentages
        # -------------------------------------------------
        if len(pie_out) > 1:
            for txt in pie_out[1]:
                txt.set_color(label_color)

        if len(pie_out) > 2:
            for txt in pie_out[2]:
                txt.set_color(autopct_color)
                txt.set_fontweight("bold")

        self._ax.axis("equal")

        if text_edge_color is not None and text_edge_width and text_edge_width > 0:
            if len(pie_out) > 1:
                for txt in pie_out[1]:
                    txt.set_path_effects([
                        path_effects.withStroke(
                            linewidth=text_edge_width,
                            foreground=text_edge_color,
                        )
                    ])

            if len(pie_out) > 2:
                for txt in pie_out[2]:
                    txt.set_path_effects([
                        path_effects.withStroke(
                            linewidth=text_edge_width,
                            foreground=text_edge_color,
                        )
                    ])

        # -------------------------------------------------
        # 12. Legend
        # -------------------------------------------------
        if legend_cfg.get("show", False):
            legend_config = legend_cfg.copy()
            legend_config.pop("show", None)

            if "loc" not in legend_config:
                legend_config["loc"] = "center left"

            if "bbox_to_anchor" not in legend_config:
                legend_config["bbox_to_anchor"] = (1.02, 0.5)

            self._ax.legend(
                pie_out[0],
                plot_labels,
                **legend_config,
            )

        # -------------------------------------------------
        # 13. Layout adjustment
        # -------------------------------------------------
        self._fig.subplots_adjust(
            left=0.08,
            right=0.88,
            top=0.80,
            bottom=0.18,
        )

        return self


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
    ) -> Self:

        """
        Create an institutional box-and-whisker chart from selected DataFrame columns.

        This method creates a distribution chart for one or multiple series,
        supporting customized box, median, whisker, cap, flier, and mean styles.
        It also supports range labels, mean labels, point annotations, horizontal
        reference lines, axis formatting, source notes, titles, legends, and
        horizontal guide lines.

        Parameters
        ----------
        figsize : tuple[float, float], default (6.00, 5.00)
            Figure size in inches.
        titles : dict or None, optional
            Configuration passed to `add_titles` to define chart titles and subtitles.
        source : dict or None, optional
            Configuration passed to `add_source` to display the data source note.
        df_index : int, default 0
            Index of the DataFrame to use when multiple DataFrames are available.
        tickers : list[str] or str, default "all"
            Columns to include in the boxplot. Use `"all"` to include every column.
        labels : list[str], str, or None, optional
            Display labels for each selected series. If not provided, column names
            are used.
        colors : list[str] or str, default PALETA_COLORES
            Fill colors assigned to each box.
        box_face_alpha : float, default 0.5
            Transparency applied to box fill colors.
        box_config : dict or None, optional
            General Matplotlib boxplot configuration, such as whisker range,
            mean visibility, outlier visibility, widths, notch, and orientation.
        box_style : dict or None, optional
            Styling configuration for box borders.
        median_style : dict or None, optional
            Styling configuration for median lines.
        whisker_style : dict or None, optional
            Styling configuration for whisker lines.
        cap_style : dict or None, optional
            Styling configuration for whisker caps.
        flier_style : dict or None, optional
            Styling configuration for outlier markers.
        mean_style : dict or None, optional
            Styling configuration for mean lines or markers.
        y_axis : dict or None, optional
            Configuration passed to `prep_y_axis`.
        x_axis : dict or None, optional
            Configuration passed to `prep_x_axis`.
        range_tag_high : dict or None, optional
            Configuration for labels shown at the upper whisker values.
        range_tag_low : dict or None, optional
            Configuration for labels shown at the lower whisker values.
        mean_tag : dict or None, optional
            Configuration for labels shown at the mean values.
        legend : dict or None, optional
            Legend configuration passed to `add_legend`.
        tag_dot : dict or None, optional
            Configuration for additional boxplot annotations.
        hlines : dict or None, optional
            Horizontal reference line configuration passed to `horizontal_lines`.
        show_hguide : bool, default False
            Whether to display horizontal guide lines.

        Returns
        -------
        None
            The chart is drawn on the active Matplotlib axis.

        Notes
        -----
        The x-axis is forced to categorical mode because box-and-whisker charts
        represent distributions by category rather than continuous x-axis values.
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
        self.add_titles(**titles)
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
            Build the default style dictionary for median lines in the boxplot.

            Returns
            -------
            dict
                Local style parameters to be passed as `medianprops` to Matplotlib.
            """
            return locals()
        
        def _whisker(
                color: str = "#6E6E6E",
                lw: float = 0.5,
        ):
            """
            Build the default style dictionary for whisker lines in the boxplot.

            Returns
            -------
            dict
                Local style parameters to be passed as `whiskerprops` to Matplotlib.
            """
            return locals()

        def _cap(
                color: str = "#6E6E6E",
                lw: float = 0.5,
        ):
            """
            Build the default style dictionary for whisker caps in the boxplot.

            Returns
            -------
            dict
                Local style parameters to be passed as `capprops` to Matplotlib.
            """
            return locals()

        def _box(
                color: str = "#6E6E6E",
                lw: float = 0.5,
        ):
            """
            Build the default style dictionary for box borders in the boxplot.

            Returns
            -------
            dict
                Local style parameters to be passed as `boxprops` to Matplotlib.
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
            Build the default style dictionary for outlier markers in the boxplot.

            Returns
            -------
            dict
                Local style parameters to be passed as `flierprops` to Matplotlib.
            """
            return locals()         
        
        def _mean(
                color: str = "#404040",
                lw: float = 0.5,
                linestyle: str = "--"
        ):
            """
            Build the default style dictionary for mean indicators in the boxplot.

            Returns
            -------
            dict
                Local style parameters to be passed as `meanprops` to Matplotlib.
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
            Build the default configuration dictionary for the Matplotlib boxplot.

            Returns
            -------
            dict
                Boxplot configuration parameters, including whisker range, visibility
                options, width, notch setting, and orientation.
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
            Build the default configuration dictionary for statistic value labels.

            This helper defines the visual and formatting parameters used to annotate
            whisker values or mean values on the box-and-whisker chart.

            Returns
            -------
            dict
                Label configuration parameters used by `tag`.
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
                    self.tag(
                        x_value=x_low,
                        y_value=y_low,
                        label=f"{y_low:{range_tag_low_fmt}}",
                        **range_tag_low
                    )

                if range_tag_high_show:
                    self.tag(
                        x_value=x_high,
                        y_value=y_high,
                        label=f"{y_high:{range_tag_high_fmt}}",
                        **range_tag_high
                    )
                
                if mean_tag_show:
                    self.tag(
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
            self.horizontal_guides(mostrar_cero=False)

        self.config_yaxis(**y_axis)

        self.add_legend(**legend)

        return self

