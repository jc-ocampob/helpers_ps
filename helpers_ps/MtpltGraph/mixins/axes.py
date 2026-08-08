from __future__ import annotations
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator
import matplotlib.dates as mdates
from ..config_models import XAxisConfig, YAxisConfig, coerce_config, config_to_dict


class AxesMixin:
    """
    Provides x-axis and y-axis preparation utilities.
    """
    def prep_x_axis_config(
        self,
        dataframe: pd.DataFrame | None = None,
        config: XAxisConfig | dict | None = None,
    ) -> pd.DataFrame:
        cfg = coerce_config(config, XAxisConfig)
        kwargs = config_to_dict(cfg)
        return self.prep_x_axis(
            dataframe=dataframe,
            **kwargs,
        )


    def prep_y_axis_config(
        self,
        config: YAxisConfig | dict | None = None,
    ):
        cfg = coerce_config(config, YAxisConfig)
        kwargs = config_to_dict(cfg)
        return self.prep_y_axis(**kwargs)


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


    def _resolve_line_axes(self, axis_map: dict[str, str]):
        left_ax = self._ax
        right_ax = getattr(self, "_right_ax", None)

        needs_right_axis = any(
            side == "right"
            for side in axis_map.values()
        )

        if needs_right_axis and right_ax is None:
            right_ax = left_ax.twinx()

        self._right_ax = right_ax
        self._right_axis_enabled = right_ax is not None

        return left_ax, right_ax


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
        tick_values: list | tuple | pd.Index | np.ndarray | None = None,
        tick_labels: list[str] | tuple[str, ...] | None = None,
        tick_label_map: dict | None = None,
        rotation: float = 0,
        ha: str = "center",
        label_color: str | None = None,
        show_years: bool = True,
    ) -> pd.DataFrame:
        """
        Prepare the x-axis format, ticks, labels, limits, and internal metadata.

        This method detects whether the DataFrame index is datetime-like, numeric,
        or categorical, and applies the appropriate x-axis formatting. It supports
        automatic tick selection through `tick_step`, explicit tick selection through
        `tick_values`, and custom label replacement through `tick_labels` or
        `tick_label_map`.

        Parameters
        ----------
        dataframe : pandas.DataFrame or None, optional
            DataFrame used to configure the x-axis. If None, the active internal
            DataFrame `_df` is used.
        bbg_format : bool, default False
            Whether to use the Bloomberg-style x-axis format for datetime indexes.
        tick_step : int, default 6
            Step used to determine the frequency of visible x-axis tick labels when
            `tick_values` is not provided.
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
        tick_values : list, tuple, pandas.Index, numpy.ndarray, or None, optional
            Explicit x-axis values to display as ticks. Values should match the
            DataFrame index for datetime, numeric, or categorical axes. In
            Bloomberg-style mode, datetime values are mapped to internal positions.
        tick_labels : list[str], tuple[str, ...], or None, optional
            Explicit labels to use for `tick_values`. Must have the same length as
            the resolved tick positions.
        tick_label_map : dict or None, optional
            Mapping used to rename selected tick labels. Keys are matched against
            original index values and stringified labels.
        rotation : float, default 0
            Rotation applied to x-axis tick labels.
        ha : str, default "center"
            Horizontal alignment of x-axis tick labels.
        label_color : str or None, optional
            Optional color applied to x-axis tick labels.
        show_years : bool, default True
            Whether to draw year labels in Bloomberg-style mode.

        Returns
        -------
        pandas.DataFrame
            DataFrame after applying the optional x-axis limits.

        Notes
        -----
        The method updates internal x-axis metadata such as `_x_axis_mode`,
        `_x_axis_fechas`, `_x_vals`, `_months`, `_years`, and `_x_axis_metadata`.
        """

        # -------------------------------------------------
        # 1. Basic validation
        # -------------------------------------------------
        if dataframe is None:
            dataframe = self._df

        if dataframe is None:
            raise ValueError("No dataframe was provided and `self._df` is None.")

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("`dataframe` must be a pandas DataFrame.")

        if dataframe.empty:
            raise ValueError("Cannot prepare x-axis because the dataframe is empty.")

        if tick_step is None:
            tick_step = 1

        if not isinstance(tick_step, int):
            raise TypeError("`tick_step` must be an integer.")

        if tick_step <= 0:
            raise ValueError("`tick_step` must be greater than zero.")

        dataframe = dataframe.copy()

        # -------------------------------------------------
        # 2. Apply limits before detecting index type
        # -------------------------------------------------
        if lim is not None:
            if not isinstance(lim, tuple) or len(lim) != 2:
                raise ValueError("`lim` must be a tuple with two values: (start, end).")

            start_value_x, end_value_x = lim

            if start_value_x is not None:
                dataframe = dataframe.loc[dataframe.index >= start_value_x].copy()

            if end_value_x is not None:
                dataframe = dataframe.loc[dataframe.index <= end_value_x].copy()

            if dataframe.empty:
                raise ValueError("The dataframe is empty after applying `lim`.")

        x_index = dataframe.index

        is_datetime = pd.api.types.is_datetime64_any_dtype(x_index)
        is_numeric = pd.api.types.is_numeric_dtype(x_index)

        fechas = None
        x_vals = None

        tick_label_map = {} if tick_label_map is None else tick_label_map

        # -------------------------------------------------
        # 3. Helpers
        # -------------------------------------------------
        def _as_list(value):
            if value is None:
                return None
            if isinstance(value, pd.Index):
                return value.tolist()
            if isinstance(value, np.ndarray):
                return value.tolist()
            if isinstance(value, (list, tuple)):
                return list(value)
            return [value]

        def _format_tick_label(value, axis_mode: str):
            if axis_mode in {"datetime", "bbg"}:
                try:
                    dt = pd.to_datetime(value)
                    date_format = fmt if fmt is not None else "%b-%y"
                    label = dt.strftime(date_format)
                except Exception:
                    label = str(value)

            elif axis_mode == "numeric":
                num_format = fmt if fmt is not None else ",.0f"
                try:
                    label = f"{value:{num_format}}"
                except Exception:
                    label = str(value)

            else:
                label = str(value)

            if value in tick_label_map:
                return tick_label_map[value]

            if str(value) in tick_label_map:
                return tick_label_map[str(value)]

            if label in tick_label_map:
                return tick_label_map[label]

            return label

        def _validate_tick_labels(resolved_positions, resolved_labels):
            if resolved_labels is None:
                return

            if len(resolved_positions) != len(resolved_labels):
                raise ValueError(
                    "`tick_labels` must have the same length as the resolved tick positions."
                )

        def _style_x_ticks():
            tick_params = {
                "axis": "x",
                "labelsize": fontsize,
            }

            if label_color is not None:
                tick_params["colors"] = label_color

            self._ax.tick_params(**tick_params)

            for label in self._ax.get_xticklabels():
                label.set_rotation(rotation)
                label.set_ha(ha)

                if label_color is not None:
                    label.set_color(label_color)

        # -------------------------------------------------
        # 4. Bloomberg-style datetime axis
        # -------------------------------------------------
        if bbg_format and is_datetime:
            fechas = pd.Index(pd.Series(x_index).dropna().sort_values().unique())

            if len(fechas) == 0:
                raise ValueError("Datetime index only contains NaT values.")

            date_to_position = {
                pd.Timestamp(date): position
                for position, date in enumerate(fechas)
            }

            x_vals = pd.Index(x_index).map(
                lambda value: date_to_position.get(pd.Timestamp(value), np.nan)
            ).to_numpy(dtype=float)

            if np.isnan(x_vals).any():
                raise ValueError(
                    "Some x-axis dates could not be mapped to Bloomberg-style positions."
                )

            self._months_years(fechas)

            if tick_values is not None:
                raw_tick_values = _as_list(tick_values)

                tick_positions = []
                tick_source_values = []

                for value in raw_tick_values:
                    try:
                        dt_value = pd.Timestamp(value)
                    except Exception:
                        dt_value = value

                    if dt_value in date_to_position:
                        tick_positions.append(date_to_position[dt_value])
                        tick_source_values.append(dt_value)
                    elif isinstance(value, (int, float, np.integer, np.floating)):
                        position = int(value)
                        if 0 <= position < len(fechas):
                            tick_positions.append(position)
                            tick_source_values.append(fechas[position])
                    else:
                        raise ValueError(
                            f"`tick_values` contains a value not found in the x-axis: {value}"
                        )

                tick_positions = np.asarray(tick_positions, dtype=float)

            else:
                periods = pd.Series(fechas).dt.to_period("M")
                month_change = periods.ne(periods.shift())
                month_idx = np.where(month_change.to_numpy())[0]

                tick_positions = month_idx[::tick_step]
                tick_source_values = [fechas[i] for i in tick_positions]

            if tick_labels is not None:
                final_labels = list(tick_labels)
            else:
                final_labels = [
                    _format_tick_label(value, "bbg")
                    for value in tick_source_values
                ]

                # Preserve your Bloomberg-style month abbreviation default
                if fmt is None and tick_values is None:
                    final_labels = [self._months[int(i)] for i in tick_positions]

            _validate_tick_labels(tick_positions, final_labels)

            self._ax.set_xticks(tick_positions)
            self._ax.set_xticklabels(final_labels, fontsize=fontsize)

            if show_years:
                self._years_xaxis(
                    y_offset=year_y_offset,
                    fontsize=fontsize,
                )

            _style_x_ticks()

            self._x_axis_mode = "bbg"
            self._x_axis_fechas = fechas

        # -------------------------------------------------
        # 5. Regular datetime axis
        # -------------------------------------------------
        elif is_datetime:
            x_vals = x_index.to_numpy()
            self._x_axis_mode = "datetime"

            if tick_values is not None:
                raw_tick_values = _as_list(tick_values)
                tick_positions = [pd.to_datetime(value) for value in raw_tick_values]

                if tick_labels is not None:
                    final_labels = list(tick_labels)
                else:
                    final_labels = [
                        _format_tick_label(value, "datetime")
                        for value in tick_positions
                    ]

                _validate_tick_labels(tick_positions, final_labels)

                self._ax.set_xticks(tick_positions)
                self._ax.set_xticklabels(final_labels, fontsize=fontsize)

            else:
                x_axis_format = fmt if fmt is not None else "%b-%y"
                locator = mdates.MonthLocator(interval=tick_step)
                formatter = mdates.DateFormatter(x_axis_format)

                self._ax.xaxis.set_major_locator(locator)
                self._ax.xaxis.set_major_formatter(formatter)

            _style_x_ticks()

        # -------------------------------------------------
        # 6. Numeric axis
        # -------------------------------------------------
        elif is_numeric:
            x_vals = x_index.to_numpy()
            self._x_axis_mode = "numeric"

            if tick_values is not None:
                tick_positions = np.asarray(_as_list(tick_values))

                if tick_labels is not None:
                    final_labels = list(tick_labels)
                else:
                    final_labels = [
                        _format_tick_label(value, "numeric")
                        for value in tick_positions
                    ]

            else:
                tick_idx = np.arange(0, len(x_vals), tick_step)
                tick_positions = x_vals[tick_idx]

                if tick_labels is not None:
                    final_labels = list(tick_labels)
                else:
                    final_labels = [
                        _format_tick_label(value, "numeric")
                        for value in tick_positions
                    ]

            _validate_tick_labels(tick_positions, final_labels)

            self._ax.set_xticks(tick_positions)
            self._ax.set_xticklabels(final_labels, fontsize=fontsize)
            _style_x_ticks()

        # -------------------------------------------------
        # 7. Categorical axis
        # -------------------------------------------------
        else:
            categories = x_index.astype(str).to_numpy()
            x_vals = np.arange(len(categories), dtype=float)

            category_to_position = {
                category: position
                for position, category in enumerate(categories)
            }

            self._x_axis_mode = "categorical"
            self._x_axis_fechas = None

            if tick_values is not None:
                raw_tick_values = _as_list(tick_values)

                tick_positions = []
                tick_source_values = []

                for value in raw_tick_values:
                    if isinstance(value, (int, np.integer)):
                        position = int(value)
                        if 0 <= position < len(categories):
                            tick_positions.append(position)
                            tick_source_values.append(categories[position])
                        else:
                            raise ValueError(
                                f"`tick_values` contains an out-of-range position: {value}"
                            )

                    elif str(value) in category_to_position:
                        tick_positions.append(category_to_position[str(value)])
                        tick_source_values.append(str(value))

                    else:
                        raise ValueError(
                            f"`tick_values` contains a category not found in the x-axis: {value}"
                        )

                tick_positions = np.asarray(tick_positions, dtype=float)

            else:
                tick_positions = np.arange(0, len(categories), tick_step, dtype=float)
                tick_source_values = [categories[int(i)] for i in tick_positions]

            if tick_labels is not None:
                final_labels = list(tick_labels)
            else:
                final_labels = [
                    _format_tick_label(value, "categorical")
                    for value in tick_source_values
                ]

            _validate_tick_labels(tick_positions, final_labels)

            self._ax.set_xticks(tick_positions)
            self._ax.set_xticklabels(final_labels, fontsize=fontsize)
            _style_x_ticks()

        # -------------------------------------------------
        # 8. Store metadata
        # -------------------------------------------------
        self._x_vals = x_vals

        self._x_axis_metadata = {
            "mode": self._x_axis_mode,
            "fechas": self._x_axis_fechas,
            "x_vals": self._x_vals,
            "tick_step": tick_step,
            "tick_values": tick_values,
            "tick_labels": tick_labels,
            "tick_label_map": tick_label_map,
            "fmt": fmt,
            "fontsize": fontsize,
            "rotation": rotation,
            "ha": ha,
            "label_color": label_color,
            "bbg_format": bbg_format,
            "lim": lim,
        }

        # -------------------------------------------------
        # 9. Layout adjustment
        # -------------------------------------------------
        if self._x_axis_mode == "bbg":
            self._fig.subplots_adjust(
                left=0.15,
                right=0.93,
                top=0.80,
                bottom=0.21,
            )
        else:
            self._fig.subplots_adjust(
                left=0.15,
                right=0.93,
                top=0.80,
                bottom=0.18,
            )

        return dataframe


    def prep_y_axis(
        self,
        lim: tuple[float, float] | None = None,
        fmt: str | None = None,
        fontsize: float = 7,
        tick_step: int | None = None,
        label: str | None = None,
        label_fontsize: float | None = None,
        label_color: str | None = None,
        tick_color: str | None = None,
        spine_color: str | None = None,
        margins_x: float | None = 0.01,
        side: str | None = None,
        ax=None,
    ):
        """
        Prepare and format a y-axis.

        This method formats a target y-axis with limits, tick label formatting,
        tick styling, axis label styling, spine color, and optional tick spacing.

        It can be used for the active axis, the left axis, the right axis, or an
        explicitly provided Matplotlib axis. Grid lines are intentionally handled
        by horizontal_guides() to keep responsibilities separated.

        Parameters
        ----------
        lim:
            Lower and upper y-axis limits.
        fmt:
            Numeric format string used for y-axis labels. If None, ',.0f' is used.
        fontsize:
            Font size used for y-axis tick labels.
        tick_step:
            Fixed interval between y-axis ticks.
        label:
            Optional y-axis label.
        label_fontsize:
            Font size used for the y-axis label. If None, uses fontsize.
        label_color:
            Color used for the y-axis label.
        tick_color:
            Color used for y-axis tick labels and tick marks.
        spine_color:
            Color used for the y-axis spine.
        margins_x:
            X-axis margin passed to the target axis. If None, margins are not changed.
        side:
            Optional side reference. Use 'left' or 'right'. If None, the method
            formats the active axis unless ax is provided.
        ax:
            Explicit Matplotlib axis to format. This takes priority over side.

        Returns
        -------
        Graph_base
            Current graph object.
        """
        # -------------------------------------------------
        # 1. Resolve target axis
        # -------------------------------------------------
        if ax is not None:
            target_ax = ax

        elif side == "right":
            if getattr(self, "_right_ax", None) is None:
                raise RuntimeError("No right axis exists for the active chart.")
            target_ax = self._right_ax

        elif side == "left":
            target_ax = self._ax

        else:
            target_ax = self._ax

        if target_ax is None:
            raise RuntimeError(
                "No axis available. Create a chart before formatting the y-axis."
            )

        # -------------------------------------------------
        # 2. Resolve side
        # -------------------------------------------------
        if side is None:
            if getattr(self, "_right_ax", None) is target_ax:
                resolved_side = "right"
            else:
                resolved_side = "left"
        else:
            resolved_side = side

        if resolved_side not in {"left", "right"}:
            raise ValueError("side must be either 'left', 'right', or None.")

        spine_name = "right" if resolved_side == "right" else "left"

        # -------------------------------------------------
        # 3. Limits and margins
        # -------------------------------------------------
        if lim is not None:
            target_ax.set_ylim(*lim)

        if margins_x is not None:
            target_ax.margins(x=margins_x)

        # -------------------------------------------------
        # 4. Tick formatter
        # -------------------------------------------------
        fmt = fmt if fmt is not None else ",.0f"

        target_ax.yaxis.set_major_formatter(
            FuncFormatter(lambda x, pos: f"{x:{fmt}}")
        )

        # -------------------------------------------------
        # 5. Tick params
        # Important:
        # Do not pass colors=None to Matplotlib.
        # -------------------------------------------------
        tick_params = {
            "axis": "y",
            "labelsize": fontsize,
        }

        final_tick_color = tick_color if tick_color is not None else label_color

        if final_tick_color is not None:
            tick_params["colors"] = final_tick_color

        target_ax.tick_params(**tick_params)

        # -------------------------------------------------
        # 6. Tick locator
        # -------------------------------------------------
        if tick_step is not None:
            target_ax.yaxis.set_major_locator(MultipleLocator(tick_step))

        # -------------------------------------------------
        # 7. Axis label
        # Important:
        # Do not force color=None.
        # -------------------------------------------------
        if label is not None:
            label_kwargs = {
                "fontsize": label_fontsize if label_fontsize is not None else fontsize,
            }

            final_label_color = label_color if label_color is not None else final_tick_color

            if final_label_color is not None:
                label_kwargs["color"] = final_label_color

            target_ax.set_ylabel(label, **label_kwargs)

        # -------------------------------------------------
        # 8. Spine color
        # Important:
        # Do not force color=None.
        # -------------------------------------------------
        final_spine_color = spine_color if spine_color is not None else final_tick_color

        if final_spine_color is not None:
            target_ax.spines[spine_name].set_color(final_spine_color)

        return self

