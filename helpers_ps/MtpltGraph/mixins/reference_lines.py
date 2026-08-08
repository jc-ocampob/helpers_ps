from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Self

class ReferenceLinesMixin:
    """
    Provide horizontal and vertical guides and reference line utilities
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

        Parameters
        ----------
        mostrar_cero:
            Whether to add a highlighted horizontal line at y=0.
        side:
            Axis side where guides should be applied. Use 'left', 'right', or 'both'.
        ax:
            Explicit Matplotlib axis to apply guides to. If provided, side is ignored
            for axis selection.
        linestyle:
            Grid line style.
        linewidth:
            Grid line width.
        color:
            Grid line color.
        alpha:
            Grid line transparency.
        zero_color:
            Color of the zero line. If None, uses color.
        zero_linestyle:
            Style of the zero line. If None, uses linestyle.
        zero_linewidth:
            Width of the zero line.
        zero_alpha:
            Transparency of the zero line. If None, uses alpha.
        zorder:
            Drawing order of the guide lines.

        Returns
        -------
        Graph_base
            Current graph object.
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


    def vertical_guides():
        ...


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

        This method supports standard numeric, datetime, categorical, and
        Bloomberg-style x-axis modes. It is intended to be used as a chainable
        public helper after a chart has been created.

        Parameters
        ----------
        x_values:
            X-axis value or values where vertical lines should be drawn.
            If None, no lines are added.
        linestyle:
            Matplotlib line style used for the reference lines.
        linewidth:
            Width of the reference lines.
        color:
            Color of the reference lines.
        alpha:
            Transparency of the reference lines.
        ymin:
            Lower vertical bound of the line in axis-relative coordinates.
        ymax:
            Upper vertical bound of the line in axis-relative coordinates.
        labels:
            Optional label or list of labels for legend integration.
        zorder:
            Drawing order of the reference lines.

        Returns
        -------
        Graph_base
            The current graph object.
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
        Add one or more horizontal reference lines to one y-axis.

        Parameters
        ----------
        y_values:
            Y-axis value or values where horizontal lines should be drawn.
            If None, no lines are added.
        linestyle:
            Matplotlib line style used for the reference lines.
        linewidth:
            Width of the reference lines.
        color:
            Color of the reference lines.
        alpha:
            Transparency of the reference lines.
        side:
            Axis side where lines should be added. Use 'left' or 'right'.
        ax:
            Explicit Matplotlib axis to use. If provided, side is ignored for
            axis selection.
        label:
            Optional legend label. Applied only to the first line to avoid duplicates.
        zorder:
            Drawing order of the reference lines.

        Returns
        -------
        Graph_base
            Current graph object.
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
