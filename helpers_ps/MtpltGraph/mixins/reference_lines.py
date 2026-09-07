from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Self

class ReferenceLinesMixin:
    """
    Reference line and guide utilities.

    This mixin provides helpers for adding grid-style guides,
    horizontal reference lines, and vertical reference lines to charts.

    Features
    --------
    - Horizontal guide lines on the left, right, or both y-axes.
    - Vertical guide lines on the x-axis.
    - Horizontal reference levels.
    - Vertical reference events and markers.
    - Support for datetime, categorical, numeric, and Bloomberg-style axes.

    Notes
    -----
    Guide methods are intended to improve readability, while reference
    line methods are intended to highlight specific levels, dates,
    events, thresholds, or targets.
    """

    def horizontal_guides(
        self,
        mostrar_cero: bool = True,
        side: str = "left",
        ax=None,
        linestyle: str = "--",
        linewidth: float = 0.5,
        color: str = "gray",
        alpha: float = 0.35,
        zero_color: str | None = None,
        zero_linestyle: str | None = None,
        zero_linewidth: float = 0.8,
        zero_alpha: float | None = None,
        zorder: int = 0,
    ):
        """
        Add horizontal guide lines to one or both y-axes.

        This method enables y-axis grid lines and optionally highlights
        the zero level using a separate style. It can be applied to the
        left axis, right axis, both axes, or an explicitly provided axis.

        Parameters
        ----------
        mostrar_cero : bool, default True
            Whether to draw an emphasized horizontal line at y=0.

        side : {"left", "right", "both"}, default "left"
            Axis side where guides should be applied.

        ax : matplotlib.axes.Axes or None, optional
            Explicit axis where guides should be applied. When provided,
            `side` is ignored.

        linestyle : str, default "--"
            Guide line style.

        linewidth : float, default 0.5
            Guide line width.

        color : str, default "gray"
            Guide line color.

        alpha : float, default 0.35
            Guide line transparency.

        zero_color : str or None, optional
            Color of the zero reference line. If omitted, `color`
            is used.

        zero_linestyle : str or None, optional
            Style of the zero reference line. If omitted,
            `linestyle` is used.

        zero_linewidth : float, default 0.8
            Width of the zero reference line.

        zero_alpha : float or None, optional
            Transparency of the zero reference line. If omitted,
            `alpha` is used.

        zorder : int, default 0
            Drawing order of the guides.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Examples
        --------
        Standard horizontal guides:

        >>> (
        ...     graph
        ...     .horizontal_guides()
        ... )

        Guides on both axes:

        >>> (
        ...     graph
        ...     .horizontal_guides(
        ...         side="both"
        ...     )
        ... )

        Custom zero line:

        >>> (
        ...     graph
        ...     .horizontal_guides(
        ...         zero_color="black",
        ...         zero_linewidth=1.5
        ...     )
        ... )
        """
        
        if ax is not None:
            axes = [ax]

        elif side == "left":
            axes = [self._ax]

        elif side == "right":
            if getattr(self, "_right_ax", None) is None:
                raise RuntimeError("No right axis exists for the active chart.")
            axes = [self._right_ax]

        elif side == "both":
            axes = [self._ax]

            if getattr(self, "_right_ax", None) is not None:
                axes.append(self._right_ax)

        else:
            raise ValueError("side must be 'left', 'right', or 'both'.")

        for target_ax in axes:
            if target_ax is None:
                continue

            target_ax.yaxis.grid(
                True,
                linestyle=linestyle,
                linewidth=linewidth,
                color=color,
                alpha=alpha,
                zorder=zorder,
            )

            target_ax.set_axisbelow(True)

            if mostrar_cero:
                target_ax.axhline(
                    0,
                    color=zero_color if zero_color is not None else color,
                    linestyle=zero_linestyle if zero_linestyle is not None else linestyle,
                    linewidth=zero_linewidth,
                    alpha=zero_alpha if zero_alpha is not None else alpha,
                    zorder=zorder,
                )

        return self


    def vertical_guides(
        self,
        side: str = "bottom",
        ax=None,
        linestyle: str = "--",
        linewidth: float = 0.5,
        color: str = "gray",
        alpha: float = 0.35,
        zorder: int = 0,
    ):
        """
        Add vertical guide lines to the chart.

        This method enables x-axis grid lines that span the plotting area.
        Vertical guides are useful for improving date alignment and visual
        comparison across observations.

        Parameters
        ----------
        side : {"bottom", "top", "both"}, default "bottom"
            Included for API consistency. Currently guides are applied
            to the selected axis.

        ax : matplotlib.axes.Axes or None, optional
            Explicit axis where guides should be applied. When omitted,
            the active chart axis is used.

        linestyle : str, default "--"
            Guide line style.

        linewidth : float, default 0.5
            Guide line width.

        color : str, default "gray"
            Guide line color.

        alpha : float, default 0.35
            Guide line transparency.

        zorder : int, default 0
            Drawing order of the guides.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Examples
        --------
        Standard vertical guides:

        >>> (
        ...     graph
        ...     .vertical_guides()
        ... )

        Heavier vertical guides:

        >>> (
        ...     graph
        ...     .vertical_guides(
        ...         linewidth=1,
        ...         alpha=0.5
        ...     )
        ... )
        """

        target_ax = self._ax if ax is None else ax

        if target_ax is None:
            raise RuntimeError(
                "No axis available. Create a chart before adding guides."
            )

        target_ax.xaxis.grid(
            True,
            linestyle=linestyle,
            linewidth=linewidth,
            color=color,
            alpha=alpha,
            zorder=zorder,
        )

        target_ax.set_axisbelow(True)

        return self


    def vertical_lines(
        self: Self,
        x_values: list[float | str | pd.Timestamp] | float | str | pd.Timestamp | None = None,
        linestyle: str | None = None,
        linewidth: float = 0.5,
        color: str = "gray",
        alpha: float = 1.0,
        ymin: float = 0.0,
        ymax: float = 1.0,
        labels: list[str] | str | None = None,
        zorder: int = 4,
    ) -> Self:
        """
        Add one or more vertical reference lines to the active axis.

        This method draws vertical lines at specific x-axis locations.
        It supports numeric, datetime, categorical, and Bloomberg-style
        axes and is commonly used to highlight events, regime changes,
        earnings releases, policy meetings, or rebalance dates.

        Parameters
        ----------
        x_values : scalar, list-like, or None
            X-axis value or values where reference lines should be drawn.

        linestyle : str or None, optional
            Matplotlib line style used for the reference lines.

        linewidth : float, default 0.5
            Width of the reference lines.

        color : str, default "gray"
            Color of the reference lines.

        alpha : float, default 1.0
            Transparency of the reference lines.

        ymin : float, default 0.0
            Lower extent of the line in axis-relative coordinates.

        ymax : float, default 1.0
            Upper extent of the line in axis-relative coordinates.

        labels : str, list[str], or None, optional
            Optional legend labels associated with the reference lines.

        zorder : int, default 4
            Drawing order of the reference lines.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Examples
        --------
        Single event date:

        >>> (
        ...     graph
        ...     .vertical_lines("2023-03-10")
        ... )

        Multiple event dates:

        >>> (
        ...     graph
        ...     .vertical_lines(
        ...         [
        ...             "2020-03-01",
        ...             "2022-06-15"
        ...         ]
        ...     )
        ... )

        Vertical line with legend entry:

        >>> (
        ...     graph
        ...     .vertical_lines(
        ...         "2024-01-01",
        ...         color="red",
        ...         label="Portfolio Launch"
        ...     )
        ... )
        """
        
        if x_values is None:
            return self

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("No active axis found. Create a chart before adding vertical lines.")

        if not isinstance(x_values, (list, tuple, set)):
            x_values = [x_values]
        else:
            x_values = list(x_values)

        if labels is None:
            labels = [None] * len(x_values)
        elif isinstance(labels, str):
            labels = [labels] + [None] * (len(x_values) - 1)
        else:
            labels = list(labels)
            if len(labels) < len(x_values):
                labels = labels + [None] * (len(x_values) - len(labels))

        mode = self._x_axis_mode

        for i, x in enumerate(x_values):
            label = labels[i] if i < len(labels) else None

            if mode == "bbg":
                x_plot = self._coerce_to_bbg_x(x)

            elif mode == "datetime":
                try:
                    x_conv = pd.to_datetime(x)
                except Exception:
                    x_conv = x

                x_plot = self._ax.convert_xunits(x_conv)

                if np.ndim(x_plot) > 0:
                    x_plot = np.asarray(x_plot).item()

            elif mode == "categorical":
                x_plot = x

                if isinstance(x, str):
                    xticklabels = [tick.get_text() for tick in self._ax.get_xticklabels()]

                    if x in xticklabels:
                        x_plot = xticklabels.index(x)

            else:
                x_plot = x

            self._ax.axvline(
                x=x_plot,
                ymin=ymin,
                ymax=ymax,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                alpha=alpha,
                label=label,
                zorder=zorder,
            )

        return self


    def horizontal_lines(
        self,
        y_values: list[float] | float | None = None,
        linestyle: str | None = None,
        linewidth: float = 0.5,
        color: str = "gray",
        alpha: float = 1.0,
        side: str = "left",
        ax=None,
        label: str | None = None,
        zorder: int = 4,
    ):
        """
        Add one or more horizontal reference lines.

        This method draws horizontal lines at specified y-axis values.
        Reference levels are commonly used to indicate targets,
        averages, thresholds, caps, floors, or policy ranges.

        Parameters
        ----------
        y_values : float, list[float], or None
            Y-axis value or values where reference lines should be drawn.

        linestyle : str or None, optional
            Matplotlib line style used for the reference lines.

        linewidth : float, default 0.5
            Width of the reference lines.

        color : str, default "gray"
            Color of the reference lines.

        alpha : float, default 1.0
            Transparency of the reference lines.

        side : {"left", "right"}, default "left"
            Axis side where the reference lines should be added.

        ax : matplotlib.axes.Axes or None, optional
            Explicit axis where reference lines should be added.
            When provided, `side` is ignored.

        label : str or None, optional
            Optional legend label associated with the first
            reference line.

        zorder : int, default 4
            Drawing order of the reference lines.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Examples
        --------
        Single reference level:

        >>> (
        ...     graph
        ...     .horizontal_lines(100)
        ... )

        Multiple levels:

        >>> (
        ...     graph
        ...     .horizontal_lines(
        ...         [80, 100, 120]
        ...     )
        ... )

        Target level with legend:

        >>> (
        ...     graph
        ...     .horizontal_lines(
        ...         100,
        ...         color="green",
        ...         label="Target"
        ...     )
        ... )
        """
        
        if y_values is None:
            return self

        if ax is not None:
            target_ax = ax

        elif side == "right":
            if getattr(self, "_right_ax", None) is None:
                raise RuntimeError("No right axis exists for the active chart.")
            target_ax = self._right_ax

        elif side == "left":
            target_ax = self._ax

        else:
            raise ValueError("side must be either 'left' or 'right'.")

        if target_ax is None:
            raise RuntimeError("No axis available. Create a chart before adding lines.")

        if isinstance(y_values, (int, float)):
            y_values = [y_values]

        for i, y in enumerate(y_values):
            target_ax.axhline(
                y,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                alpha=alpha,
                label=label if i == 0 else None,
                zorder=zorder,
            )

        return self
