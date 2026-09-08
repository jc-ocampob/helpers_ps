from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.patheffects as path_effects
from typing import Self

class AnnotationMixin:
    """
    Annotation and highlighting primitives.

    This mixin contains methods used to add visual emphasis and explanatory
    elements to charts, including labels, markers, and shaded regions.

    Methods
    -------
    tag
        Add text annotations at specific coordinates.

    dot
        Add highlighted point markers.

    shade_x
        Add shaded vertical regions along the x-axis.

    shade_y
        Add shaded horizontal regions along the y-axis.
    """

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
        show_bbox: bool = False,
        text_edge_color: str | None = None,
        text_edge_width: float = 0.0,
        zorder: int = 6,
    ) -> Self:
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
        Self
            Returns the chart instance for method chaining.

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

        return self


    def dot(
        self,
        x_value,
        y_value,
        color: str = "red",
        size: float = 30,
        zorder: float = 5,
        *,
        marker: str = "o",
        markersize: float | None = None,
        marker_color: str | None = None,
        marker_edgecolor: str | None = None,
        marker_edgewidth: float = 0.0,
        alpha: float = 1.0,
        clip_on: bool = True,
        label: str | None = None,
        legend: bool = True,
        **scatter_kwargs,
    ) -> Self:
        """
        Add a highlighted point marker to the active chart.

        The method supports datetime, numeric, categorical, and
        Bloomberg-style X-axis modes. When ``label`` is provided, the
        generated scatter artist can also be registered as a custom
        ``"points"`` legend handle.

        Parameters
        ----------
        x_value:
            X-axis value where the marker is placed.

        y_value:
            Y-axis value where the marker is placed.

        color:
            Default marker face color. Used when ``marker_color`` is None.

        size:
            Marker area in points squared, passed to ``Axes.scatter``.

        zorder:
            Drawing order of the marker.

        marker:
            Matplotlib marker style.

        markersize:
            Marker diameter in points. When provided, it is converted to
            scatter area using ``markersize ** 2``.

        marker_color:
            Marker face color. When omitted, ``color`` is used.

        marker_edgecolor:
            Marker edge color.

        marker_edgewidth:
            Marker edge width.

        alpha:
            Marker opacity.

        clip_on:
            Whether the marker is clipped to the active axes.

        label:
            Optional legend label assigned to the marker.

        legend:
            Whether the marker should be registered in the custom
            ``"points"`` legend category when ``label`` is provided.

        **scatter_kwargs:
            Additional keyword arguments passed to ``Axes.scatter``.

        Returns
        -------
        Self
            The current chart instance for method chaining.

        Raises
        ------
        RuntimeError
            If the active axis has not been initialized.

        TypeError
            If a parameter receives an invalid type.

        ValueError
            If numeric parameters are outside their permitted ranges.
        """
        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError(
                "Axis not initialized. Call plot() before dot()."
            )

        if not isinstance(size, (int, float)):
            raise TypeError(
                "'size' must be numeric."
            )

        if size < 0:
            raise ValueError(
                "'size' cannot be negative."
            )

        if (
            markersize is not None
            and not isinstance(markersize, (int, float))
        ):
            raise TypeError(
                "'markersize' must be numeric or None."
            )

        if (
            markersize is not None
            and markersize < 0
        ):
            raise ValueError(
                "'markersize' cannot be negative."
            )

        if not isinstance(marker_edgewidth, (int, float)):
            raise TypeError(
                "'marker_edgewidth' must be numeric."
            )

        if marker_edgewidth < 0:
            raise ValueError(
                "'marker_edgewidth' cannot be negative."
            )

        if not isinstance(alpha, (int, float)):
            raise TypeError(
                "'alpha' must be numeric."
            )

        if not 0 <= alpha <= 1:
            raise ValueError(
                "'alpha' must be between 0 and 1."
            )

        if not isinstance(zorder, (int, float)):
            raise TypeError(
                "'zorder' must be numeric."
            )

        if not isinstance(clip_on, bool):
            raise TypeError(
                "'clip_on' must be a boolean."
            )

        if not isinstance(legend, bool):
            raise TypeError(
                "'legend' must be a boolean."
            )

        if not isinstance(marker, str):
            raise TypeError(
                "'marker' must be a string."
            )

        if not isinstance(color, str):
            raise TypeError(
                "'color' must be a string."
            )

        if (
            marker_color is not None
            and not isinstance(marker_color, str)
        ):
            raise TypeError(
                "'marker_color' must be a string or None."
            )

        if (
            marker_edgecolor is not None
            and not isinstance(marker_edgecolor, str)
        ):
            raise TypeError(
                "'marker_edgecolor' must be a string or None."
            )

        if (
            label is not None
            and not isinstance(label, str)
        ):
            raise TypeError(
                "'label' must be a string or None."
            )

        mode = getattr(
            self,
            "_x_axis_mode",
            None,
        )

        if mode == "bbg":
            x_plot = self._coerce_to_bbg_x(
                x_value
            )

        else:
            x_converted = x_value

            if mode == "datetime":
                try:
                    x_converted = pd.to_datetime(
                        x_value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    x_converted = x_value

            x_plot = self._ax.convert_xunits(
                x_converted
            )

            if np.ndim(x_plot) > 0:
                x_array = np.asarray(x_plot)

                if x_array.size != 1:
                    raise ValueError(
                        "'x_value' must resolve to a single "
                        "X-axis position."
                    )

                x_plot = x_array.item()

        resolved_color = (
            marker_color
            if marker_color is not None
            else color
        )

        resolved_size = (
            float(markersize) ** 2
            if markersize is not None
            else float(size)
        )

        plot_kwargs = {
            "marker": marker,
            "s": resolved_size,
            "color": resolved_color,
            "linewidths": float(marker_edgewidth),
            "alpha": float(alpha),
            "zorder": float(zorder),
            "clip_on": clip_on,
        }

        if marker_edgecolor is not None:
            plot_kwargs["edgecolors"] = (
                marker_edgecolor
            )

        if label is not None:
            plot_kwargs["label"] = label

        protected_kwargs = {
            "marker",
            "s",
            "color",
            "linewidths",
            "alpha",
            "zorder",
            "clip_on",
            "edgecolors",
            "label",
        }

        invalid_overrides = (
            protected_kwargs
            .intersection(scatter_kwargs)
        )

        if invalid_overrides:
            invalid_names = ", ".join(
                sorted(invalid_overrides)
            )

            raise TypeError(
                "The following arguments must be passed "
                "directly to dot() and cannot be provided "
                f"through scatter_kwargs: {invalid_names}."
            )

        plot_kwargs.update(
            scatter_kwargs
        )

        dot_artist = self._ax.scatter(
            x_plot,
            y_value,
            **plot_kwargs,
        )

        if (
            legend
            and label is not None
            and label
            and not label.startswith("_")
        ):
            if not hasattr(self, "_custom_handles"):
                self._custom_handles = {}

            if not hasattr(self, "_custom_handle_labels"):
                self._custom_handle_labels = {}

            if not isinstance(self._custom_handles, dict):
                raise TypeError(
                    "'_custom_handles' must be a dictionary "
                    "organized by legend element type."
                )

            if not isinstance(
                self._custom_handle_labels,
                dict,
            ):
                raise TypeError(
                    "'_custom_handle_labels' must be a "
                    "dictionary organized by legend element type."
                )

            point_handles = (
                self._custom_handles
                .setdefault("points", [])
            )

            point_labels = (
                self._custom_handle_labels
                .setdefault("points", [])
            )

            if label not in point_labels:
                point_handles.append(
                    dot_artist
                )

                point_labels.append(
                    label
                )

        return self


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
    ) -> Self:
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
        Self
            Returns the chart instance for method chaining.

        Raises
        ------
        RuntimeError
            If the active axis has not been initialized.

        Notes
        -----
        When multiple periods are provided and `label` is used, the default label is
        applied only once to avoid duplicate legend entries.

        Examples
        --------
        Shade a recession period:

        >>> (
        ...     graph
        ...     .shade_x(("2020-03-01", "2020-06-30"))
        ... )

        Shade multiple periods:

        >>> (
        ...     graph
        ...     .shade_x([
        ...         ("2020-03-01", "2020-06-30"),
        ...         ("2022-01-01", "2022-03-01")
        ...     ])
        ... )

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

        return self


    def shade_y(
        self,
        period: tuple[float, float],
        color="#B0B0B0",
        alpha=0.25,
        zorder=0,
        label=None,
        hatch=None,
        xmin=0.0,
        xmax=1.0,
        clip_to_ylim=True,
    ) -> Self:
        """
        Add a shaded horizontal region to the active chart.

        This method highlights a y-axis range using a horizontal shaded
        band. It is useful for emphasizing target ranges, confidence bands,
        risk zones, valuation ranges, or threshold levels.

        Parameters
        ----------
        period : tuple[float, float]
            Y-axis range to shade as `(start, end)`.

        color : str, default "#B0B0B0"
            Fill color of the shaded region.

        alpha : float, default 0.25
            Transparency of the shaded region.

        zorder : int, default 0
            Drawing order of the shaded region.

        label : str or None, optional
            Optional legend label.

        hatch : str or None, optional
            Optional hatch pattern.

        xmin : float, default 0.0
            Left horizontal bound in axis-relative coordinates.

        xmax : float, default 1.0
            Right horizontal bound in axis-relative coordinates.

        clip_to_ylim : bool, default True
            Whether to clip the shaded range to the current y-axis limits.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Raises
        ------
        RuntimeError
            If the active axis has not been initialized.
        """

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("No axis found. Call graph_line/graph_bar first.")

        y0, y1 = period

        if y1 < y0:
            y0, y1 = y1, y0

        if clip_to_ylim:
            ylim = self._ax.get_ylim()

            y0 = max(y0, ylim[0])
            y1 = min(y1, ylim[1])

            if y1 <= y0:
                return self

        self._ax.axhspan(
            y0,
            y1,
            xmin=xmin,
            xmax=xmax,
            facecolor=color,
            alpha=alpha,
            zorder=zorder,
            label=label,
            hatch=hatch,
        )

        return self