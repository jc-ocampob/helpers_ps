from __future__ import annotations

from collections.abc import Sequence
from dataclasses import fields
from typing import Any, Self

import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator

from ..models import (
    DistCurveConfig,
    DistCurveLike,
    DistSeriesConfig,
    DistSeriesDict,
    DistSeriesLike,
    DistStat,
    XAxisConfig,
    coerce_configs,
    config_to_dict,
    normalize_curve_specs,
)
from ..tags._colors import PALETA_COLORES

_DIST_LABELS = {
    "norm": "Normal",
    "t": "t de Student",
    "lognorm": "Lognormal",
    "expon": "Exponencial",
    "gamma": "Gamma",
    "beta": "Beta",
    "laplace": "Laplace",
    "logistic": "Logística",
    "skewnorm": "Skew-normal",
    "genextreme": "GEV",
    "cauchy": "Cauchy",
    "kde": "KDE",
}

_PARAM_SYMBOLS = {
    "norm": {"loc": "μ", "scale": "σ"},
}

_VALID_STATS = {"density", "count", "probability"}

_FIT_LINESTYLES = ["-", "-.", ":", (0, (5, 1))]
_KNOWN_LINESTYLES = ["--", (0, (1, 1)), (0, (3, 1, 1, 1))]

# ---------------------------------------------------------------------------
# Curve styling
# ---------------------------------------------------------------------------
# Keys that define WHAT is drawn (not how); they are only valid inside the
# curve dictionary itself.
_CURVE_STRUCTURE_KEYS = {"dist", "params", "fit_kwargs", "bw_method"}

# Keys that define HOW a curve looks.
_CURVE_STYLE_KEYS = {
    "color",
    "linewidth",
    "linestyle",
    "alpha",
    "zorder",
    "label",           # fixed legend text
    "label_template",  # legend text built with {fields}
    "legend",          # False -> hide from the legend
    "param_fmt",       # number format used by {params}
    "param_sep",       # separator used by {params}
    "fill",            # True or dict(color, alpha, zorder, hatch)
    "line_kwargs",     # extra kwargs for Axes.plot (marker, ...)
}
_CURVE_STYLE_ALIASES = {"c": "color", "lw": "linewidth", "ls": "linestyle"}
_FILL_KEYS = {"color", "alpha", "zorder", "hatch"}

# Extra X-axis styling keys accepted (as dictionary keys) in addition to
# the fields of XAxisConfig. They are removed before XAxisConfig
# validation, so they work without modifying that dataclass.
_DIST_XAXIS_EXTRAS = (
    "fontweight",
    "fontstyle",
    "tick_color",
    "spine_color",
    "axis_label",
    "axis_label_fontsize",
    "axis_label_color",
)


def _normalize_curve_style(
    style: dict[str, Any] | None,
    *,
    where: str,
    allow_structure: bool = False,
) -> dict[str, Any]:
    """Validate a curve-style dictionary and resolve key aliases."""
    if style is None:
        return {}
    if not isinstance(style, dict):
        raise TypeError(f"{where} must be a dictionary or None.")
    allowed = set(_CURVE_STYLE_KEYS)
    if allow_structure:
        allowed |= _CURVE_STRUCTURE_KEYS
    output: dict[str, Any] = {}
    for key, value in style.items():
        key = _CURVE_STYLE_ALIASES.get(key, key)
        if key not in allowed:
            raise ValueError(
                f"Unknown key {key!r} in {where}. Allowed keys: "
                f"{', '.join(sorted(allowed | set(_CURVE_STYLE_ALIASES)))}."
            )
        output[key] = value
    fill = output.get("fill")
    if isinstance(fill, dict):
        unknown = set(fill) - _FILL_KEYS
        if unknown:
            raise ValueError(
                f"Unknown key(s) {sorted(unknown)} in 'fill' of "
                f"{where}. Allowed keys: {', '.join(sorted(_FILL_KEYS))}."
            )
    elif fill is not None and not isinstance(fill, bool):
        raise TypeError(
            f"'fill' in {where} must be a boolean, a dictionary or None."
        )
    line_kwargs = output.get("line_kwargs")
    if line_kwargs is not None and not isinstance(line_kwargs, dict):
        raise TypeError(f"'line_kwargs' in {where} must be a dictionary.")
    template = output.get("label_template")
    if template is not None and not isinstance(template, str):
        raise TypeError(f"'label_template' in {where} must be a string.")
    return output


def _get_scipy_dist(name: str):
    """Return a continuous scipy.stats distribution by name."""
    try:
        from scipy import stats
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "graph_dist() needs scipy to draw known/fitted "
            "distributions. Install it with 'pip install scipy'."
        ) from exc
    distribution = getattr(stats, name, None)
    if distribution is None or not hasattr(distribution, "pdf"):
        raise ValueError(
            f"'{name}' is not a continuous distribution available "
            "in scipy.stats."
        )
    return distribution


def _param_names(distribution) -> list[str]:
    """Names of the positional parameters of a scipy distribution."""
    shapes = getattr(distribution, "shapes", None)
    names = (
        [item.strip() for item in shapes.split(",")]
        if shapes
        else []
    )
    return names + ["loc", "scale"]


def _format_params(
    name: str,
    params: dict[str, Any],
    fmt: str = ".3g",
    sep: str = ", ",
) -> str:
    symbols = _PARAM_SYMBOLS.get(name, {})
    parts = []
    for key, value in params.items():
        try:
            parts.append(f"{symbols.get(key, key)}={float(value):{fmt}}")
        except (TypeError, ValueError):
            continue
    return sep.join(parts)


class DistChartMixin:
    """
    Provides distribution-chart construction logic for GraphMtplt.

    The chart draws one histogram per series and, optionally, curves on
    top of it: curves of a *known* distribution (parameters given by
    the user) and curves *estimated* from the data of each series
    (maximum-likelihood fit or kernel density).
    """

    # ------------------------------------------------------------------
    # Series normalization
    # ------------------------------------------------------------------
    def _normalize_dist_series(
        self,
        dataframe: pd.DataFrame,
        series: Sequence[DistSeriesLike] | None,
        known: Any,
        fit: Any,
    ) -> list[DistSeriesDict]:
        """
        Normalize and validate distribution-series configurations.

        If series is None, all numeric DataFrame columns are included
        using their default configuration. ``known`` / ``fit`` act as
        defaults for every series that does not define its own.
        """
        if series is None:
            series = [
                DistSeriesConfig(ticker=str(column))
                for column in dataframe.columns
                if pd.api.types.is_numeric_dtype(dataframe[column])
            ]
        if not series:
            raise ValueError(
                "'series' cannot be empty. "
                "Use None to plot all numeric DataFrame columns."
            )

        default_known = normalize_curve_specs(known, field="known")
        default_fit = normalize_curve_specs(fit, field="fit")

        normalized: list[DistSeriesConfig] = []
        for position, item in enumerate(series):
            if isinstance(item, DistSeriesConfig):
                config = item
            elif isinstance(item, dict):
                try:
                    config = DistSeriesConfig(**item)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "Invalid distribution-series configuration "
                        f"at position {position}: {item}."
                    ) from exc
            else:
                raise TypeError(
                    "Each item in 'series' must be a dictionary "
                    "or a DistSeriesConfig instance."
                )
            if config.ticker not in dataframe.columns:
                raise KeyError(
                    f"Ticker '{config.ticker}' was not found "
                    "in the selected DataFrame."
                )
            normalized.append(config)

        tickers = [config.ticker for config in normalized]
        if len(tickers) != len(set(tickers)):
            raise ValueError(
                "Duplicated tickers are not allowed in 'series'."
            )
        if not PALETA_COLORES:
            raise ValueError("PALETA_COLORES cannot be empty.")

        output: list[DistSeriesDict] = []
        for position, config in enumerate(normalized):
            known_specs = normalize_curve_specs(
                config.known, field="known"
            )
            fit_specs = normalize_curve_specs(
                config.fit, field="fit"
            )
            resolved = DistSeriesDict(
                **{
                    field.name: getattr(config, field.name)
                    for field in fields(config)
                }
            )
            resolved["label"] = config.label or config.ticker
            resolved["color"] = config.color or PALETA_COLORES[
                position % len(PALETA_COLORES)
            ]
            resolved["known"] = (
                known_specs if known_specs is not None
                else default_known
            ) or []
            resolved["fit"] = (
                fit_specs if fit_specs is not None
                else default_fit
            ) or []
            if (
                not resolved["hist"]
                and not resolved["known"]
                and not resolved["fit"]
            ):
                raise ValueError(
                    f"Series '{config.ticker}' has hist=False and no "
                    "curves. Add 'known' or 'fit' curves, or set "
                    "hist=True."
                )
            output.append(resolved)
        return output

    def _dist_series_values(
        self,
        dataframe: pd.DataFrame,
        ticker: str,
    ) -> pd.Series:
        """Return the finite numeric observations of one column."""
        values = pd.to_numeric(
            dataframe[ticker],
            errors="coerce",
        )
        values = values.replace([np.inf, -np.inf], np.nan).dropna()
        if values.empty:
            raise ValueError(
                f"Ticker '{ticker}' contains no finite numeric "
                "observations."
            )
        return values

    # ------------------------------------------------------------------
    # Curves
    # ------------------------------------------------------------------
    def _compute_dist_curve(
        self,
        *,
        raw_spec: Any,
        kind: str,
        values: np.ndarray,
        grid: np.ndarray,
        scale: float,
        series_ticker: str,
        series_label: str,
        series_color: str,
        lw: float,
        prefix_label: bool,
        curve_index: int = 0,
    ) -> dict[str, Any]:
        """
        Evaluate one curve over ``grid`` and resolve its style.

        ``kind`` is ``"known"`` or ``"fit"``. The returned dictionary
        contains the data and the resolved style, ready to be plotted.

        The style comes from the curve itself (dictionary or
        ``DistCurveConfig``) on top of the built-in defaults.
        """
        if isinstance(raw_spec, DistCurveConfig):
            raw_spec = raw_spec.to_dict()
        if isinstance(raw_spec, str):
            spec: dict[str, Any] = {"dist": raw_spec}
        elif isinstance(raw_spec, dict):
            spec = dict(raw_spec)
        else:
            spec = {"dist": raw_spec}
        spec = _normalize_curve_style(
            spec,
            where=f"a '{kind}' curve dictionary",
            allow_structure=True,
        )

        dist = spec["dist"]
        params: dict[str, Any] = {}
        name = "custom"
        extra_fields: dict[str, Any] = {}

        if kind == "fit":
            name = dist.strip().lower()
            if name == "kde":
                from scipy.stats import gaussian_kde

                kde = gaussian_kde(
                    values,
                    bw_method=spec.get("bw_method"),
                )
                y_values = kde(grid)
                extra_fields["bandwidth"] = float(kde.factor)
            else:
                distribution = _get_scipy_dist(name)
                estimated = distribution.fit(
                    values,
                    **(spec.get("fit_kwargs") or {}),
                )
                params = dict(
                    zip(_param_names(distribution), estimated)
                )
                y_values = distribution(*estimated).pdf(grid)
        elif isinstance(dist, str):
            name = dist.strip().lower()
            distribution = _get_scipy_dist(name)
            raw_params = spec.get("params")
            if isinstance(raw_params, dict):
                frozen = distribution(**raw_params)
                params = dict(raw_params)
            elif isinstance(raw_params, (list, tuple)):
                frozen = distribution(*raw_params)
                params = dict(
                    zip(_param_names(distribution), raw_params)
                )
            elif raw_params is None:
                frozen = distribution()
                if not getattr(distribution, "shapes", None):
                    params = {"loc": 0.0, "scale": 1.0}
            else:
                raise TypeError(
                    "'params' must be a dictionary, a tuple/list "
                    "or None."
                )
            y_values = frozen.pdf(grid)
        elif hasattr(dist, "pdf"):
            name = getattr(
                getattr(dist, "dist", None),
                "name",
                "custom",
            )
            y_values = dist.pdf(grid)
        elif callable(dist):
            name = getattr(dist, "__name__", "custom")
            y_values = dist(grid)
        else:
            raise TypeError(
                "'dist' must be a scipy.stats name, a frozen "
                "distribution or a callable pdf(x)."
            )

        y_values = np.asarray(y_values, dtype=float)
        if y_values.shape != grid.shape:
            raise ValueError(
                "The curve must return one value per grid point."
            )
        y_values = y_values * scale

        # ---- resolve style ------------------------------------------
        if kind == "known":
            base_style = {
                "color": "#222222",
                "linestyle": _KNOWN_LINESTYLES[
                    curve_index % len(_KNOWN_LINESTYLES)
                ],
            }
        else:
            base_style = {
                "color": series_color,
                "linestyle": _FIT_LINESTYLES[
                    curve_index % len(_FIT_LINESTYLES)
                ],
            }
        base_style.update(
            {
                "linewidth": lw,
                "alpha": 1.0,
                "zorder": 3,
                "legend": True,
                "param_fmt": ".3g",
                "param_sep": ", ",
                "fill": None,
                "line_kwargs": {},
            }
        )
        style = dict(base_style)
        for key, value in spec.items():
            if key in _CURVE_STRUCTURE_KEYS:
                continue
            if key == "line_kwargs":
                style["line_kwargs"] = {
                    **style["line_kwargs"],
                    **(value or {}),
                }
            else:
                style[key] = value

        # ---- legend text --------------------------------------------
        pretty = _DIST_LABELS.get(name, name)
        kind_text = "ajustada" if kind == "fit" else "teórica"
        params_text = _format_params(
            name,
            params,
            fmt=str(style["param_fmt"]),
            sep=str(style["param_sep"]),
        )
        if style.get("label") is not None:
            label = str(style["label"])
        elif style.get("label_template") is not None:
            template_fields: dict[str, Any] = {
                "series": series_label,
                "ticker": series_ticker,
                "dist": pretty,
                "dist_key": name,
                "kind": kind_text,
                "params": params_text,
                "n": int(len(values)),
                **extra_fields,
                **params,
            }
            if "loc" in params:
                template_fields.setdefault("mu", params["loc"])
            if "scale" in params:
                template_fields.setdefault("sigma", params["scale"])
            try:
                label = style["label_template"].format(**template_fields)
            except KeyError as exc:
                raise ValueError(
                    f"Unknown field {exc} in label_template "
                    f"{style['label_template']!r} for the '{name}' "
                    f"curve. Available fields: "
                    f"{', '.join(sorted(template_fields))}."
                ) from exc
            except (ValueError, TypeError, IndexError) as exc:
                raise ValueError(
                    "Invalid label_template "
                    f"{style['label_template']!r} for the '{name}' "
                    "curve."
                ) from exc
        else:
            base = "KDE" if name == "kde" else f"{pretty} {kind_text}"
            label = f"{base} ({params_text})" if params_text else base
            if prefix_label:
                label = f"{series_label}: {label}"
        if not style["legend"]:
            label = "_nolegend_"

        fill = style["fill"]
        fill_options = None
        if fill:
            fill_options = {} if fill is True else dict(fill)

        return {
            "kind": kind,
            "name": name,
            "params": params,
            "label": label,
            "x": grid,
            "y": y_values,
            "color": style["color"],
            "linestyle": style["linestyle"],
            "linewidth": float(style["linewidth"]),
            "alpha": float(style["alpha"]),
            "zorder": float(style["zorder"]),
            "fill": fill_options,
            "line_kwargs": dict(style["line_kwargs"]),
        }

    # ------------------------------------------------------------------
    # X axis
    # ------------------------------------------------------------------
    def _resolve_dist_xaxis(
        self,
        x_axis: XAxisConfig | dict[str, Any] | None,
    ) -> tuple[dict[str, Any], set[str], dict[str, Any]]:
        """
        Normalize the ``x_axis`` argument of ``graph_dist``.

        Returns
        -------
        config:
            Full XAxisConfig converted to a dictionary.
        explicit:
            Keys the user actually set (different from the XAxisConfig
            defaults). Used for options whose XAxisConfig default would
            be wrong on a value axis, such as ``fmt`` and ``tick_step``.
        extras:
            Additional style keys (see ``_DIST_XAXIS_EXTRAS``).
        """
        extras: dict[str, Any] = {}
        explicit: set[str] = set()
        if isinstance(x_axis, dict):
            raw = dict(x_axis)
            for key in _DIST_XAXIS_EXTRAS:
                if key in raw:
                    extras[key] = raw.pop(key)
            explicit = set(raw)
            x_axis = raw
        elif x_axis is not None:
            for key in _DIST_XAXIS_EXTRAS:
                value = getattr(x_axis, key, None)
                if value is not None:
                    extras[key] = value
        configs = coerce_configs(x_axis=(x_axis, XAxisConfig))
        config = config_to_dict(configs["x_axis"])
        if x_axis is not None and not isinstance(x_axis, dict):
            defaults = config_to_dict(XAxisConfig())
            explicit = {
                key
                for key, value in config.items()
                if key not in defaults or defaults[key] != value
            }
        return config, explicit, extras

    def _apply_dist_xaxis(
        self,
        *,
        x_axis_config: dict[str, Any],
        explicit: set[str],
        extras: dict[str, Any],
        grid: np.ndarray,
    ) -> dict[str, Any]:
        """
        Format the distribution (value) axis using the shared X-axis
        configuration.

        Supported XAxisConfig fields: ``fmt``, ``tick_step``,
        ``tick_values``, ``tick_labels``, ``tick_label_map``,
        ``fontsize``, ``rotation``, ``ha``, ``va``, ``label_color`` and
        ``lim``. Fields that only make sense for date axes
        (``bbg_format``, ``show_years``) are rejected when explicitly
        requested.

        Extra dictionary keys: ``fontweight``, ``fontstyle``,
        ``tick_color``, ``spine_color``, ``axis_label``,
        ``axis_label_fontsize`` and ``axis_label_color``.
        """
        ax = self._ax
        if "bbg_format" in explicit and x_axis_config.get("bbg_format"):
            raise ValueError(
                "'bbg_format' is not applicable to a distribution "
                "axis, which is numeric."
            )
        if "show_years" in explicit and x_axis_config.get("show_years"):
            raise ValueError(
                "'show_years' is not applicable to a distribution "
                "axis, which is numeric."
            )

        fontsize = x_axis_config.get("fontsize")
        fontsize = 8 if fontsize is None else fontsize
        rotation = x_axis_config.get("rotation") or 0
        ha = x_axis_config.get("ha") or "center"
        va = x_axis_config.get("va") or "top"
        label_color = x_axis_config.get("label_color")
        fmt = x_axis_config.get("fmt") if "fmt" in explicit else None
        tick_step = (
            x_axis_config.get("tick_step")
            if "tick_step" in explicit
            else None
        )
        tick_values = x_axis_config.get("tick_values")
        tick_labels = x_axis_config.get("tick_labels")
        tick_label_map = x_axis_config.get("tick_label_map") or {}
        lim = x_axis_config.get("lim") if "lim" in explicit else None

        if tick_step is not None and (
            not isinstance(tick_step, (int, float)) or tick_step <= 0
        ):
            raise ValueError(
                "'tick_step' must be a positive number. On a "
                "distribution axis it is expressed in axis units."
            )
        if lim is not None and (
            not isinstance(lim, (tuple, list)) or len(lim) != 2
        ):
            raise ValueError("'lim' must be a tuple (min, max).")

        def _label(value: float) -> str:
            if fmt is not None:
                try:
                    text = f"{value:{fmt}}"
                except (ValueError, TypeError):
                    text = str(value)
            else:
                text = f"{value:g}"
            for key in (value, str(value), text):
                if key in tick_label_map:
                    return str(tick_label_map[key])
            return text

        if tick_values is not None:
            positions = np.asarray(
                tick_values.tolist()
                if hasattr(tick_values, "tolist")
                else list(tick_values),
                dtype=float,
            )
            if tick_labels is not None:
                labels = [str(label) for label in tick_labels]
                if len(labels) != len(positions):
                    raise ValueError(
                        "'tick_labels' must have the same length as "
                        "'tick_values'."
                    )
            else:
                labels = [_label(value) for value in positions]
            ax.set_xticks(positions)
            ax.set_xticklabels(labels)
        else:
            if tick_labels is not None:
                raise ValueError(
                    "'tick_labels' requires 'tick_values' on a "
                    "distribution axis."
                )
            if tick_step is not None:
                ax.xaxis.set_major_locator(MultipleLocator(tick_step))
            if fmt is not None or tick_label_map:
                ax.xaxis.set_major_formatter(
                    FuncFormatter(lambda value, _pos: _label(value))
                )

        if lim is not None:
            ax.set_xlim(lim[0], lim[1])

        tick_params: dict[str, Any] = {
            "axis": "x",
            "labelsize": fontsize,
        }
        tick_color = extras.get("tick_color")
        if tick_color is None:
            tick_color = label_color
        if tick_color is not None:
            tick_params["color"] = tick_color
        if label_color is not None:
            tick_params["labelcolor"] = label_color
        ax.tick_params(**tick_params)

        fontweight = extras.get("fontweight")
        fontstyle = extras.get("fontstyle")
        for tick_label in ax.get_xticklabels():
            tick_label.set_rotation(rotation)
            tick_label.set_ha(ha)
            tick_label.set_va(va)
            if fontweight is not None:
                tick_label.set_fontweight(fontweight)
            if fontstyle is not None:
                tick_label.set_fontstyle(fontstyle)

        spine_color = extras.get("spine_color")
        if spine_color is not None:
            ax.spines["bottom"].set_color(spine_color)

        axis_label = extras.get("axis_label")
        if axis_label is not None:
            label_kwargs: dict[str, Any] = {}
            if extras.get("axis_label_fontsize") is not None:
                label_kwargs["fontsize"] = extras["axis_label_fontsize"]
            if extras.get("axis_label_color") is not None:
                label_kwargs["color"] = extras["axis_label_color"]
            ax.set_xlabel(axis_label, **label_kwargs)

        return {
            "mode": "numeric",
            "chart_type": "distribution",
            "fmt": fmt,
            "tick_step": tick_step,
            "tick_values": tick_values,
            "tick_labels": tick_labels,
            "tick_label_map": tick_label_map,
            "fontsize": fontsize,
            "rotation": rotation,
            "ha": ha,
            "va": va,
            "label_color": label_color,
            "lim": lim,
            "x_vals": grid,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def graph_dist(
        self,
        series: Sequence[DistSeriesLike] | None = None,
        df_index: int = 0,
        bins: int | str | Sequence[float] = "auto",
        stat: DistStat = "density",
        common_bins: bool = True,
        hist_alpha: float = 0.45,
        hist_edgecolor: str | None = "white",
        hist_linewidth: float = 0.4,
        hist_style: dict[str, Any] | None = None,
        known: DistCurveLike | Sequence[DistCurveLike] | None = None,
        fit: DistCurveLike | Sequence[DistCurveLike] | None = None,
        curve_points: int = 400,
        x_range: tuple[float | None, float | None] | None = None,
        lw: float = 1.6,
        x_axis: dict[str, Any] | XAxisConfig | None = None,
    ) -> Self:
        """
        Add a distribution chart (histogram + optional curves).

        Each series is a DataFrame column. References (last value, a
        chosen observation, a literal value or a statistic) are
        highlighted through the ``tag`` entry of each series, just like
        the line tags.

        Parameters
        ----------
        series:
            Distribution-series configurations (dictionaries or
            ``DistSeriesConfig``). None plots every numeric column.
        df_index:
            Position of the DataFrame stored in the graph object.
        bins:
            Anything accepted by ``numpy.histogram_bin_edges``: an
            integer, a rule such as ``"auto"`` / ``"fd"`` or explicit
            edges.
        stat:
            ``"density"`` (area 1), ``"count"`` or ``"probability"``
            (bar heights sum to 1). Curves are rescaled accordingly.
        common_bins:
            Use the same bin edges for all series (recommended when
            comparing distributions).
        hist_alpha, hist_edgecolor, hist_linewidth:
            Histogram bar styling.
        hist_style:
            Extra keyword arguments passed to ``Axes.hist`` (for
            example ``{"histtype": "step"}``).
        known:
            Default curve(s) of a *known* distribution applied to every
            series without its own ``known``. Each curve is a string,
            a dictionary or a ``DistCurveConfig`` (style included)::

                known="norm"                            # N(0, 1)
                known={"dist": "norm",
                       "params": {"loc": 0.0, "scale": 0.01},
                       "color": "#C00000", "lw": 2.2, "ls": "--",
                       "label_template": "N(μ={mu:.1%}, σ={sigma:.1%})"}
                known=[DistCurveConfig("t", params=(4, 0, 0.01),
                                       legend=False)]

        fit:
            Default curve(s) *estimated from each series*, applied to
            every series without its own ``fit``. Same format as
            ``known``; strings, dictionaries and ``DistCurveConfig`` can
            be mixed in one list, like ``series``::

                fit=["norm",
                     {"dist": "t", "color": "#2E7D32", "ls": "-."},
                     {"dist": "kde", "fill": True,
                      "label_template": "KDE (bw={bandwidth:.2f})"}]
                fit={"dist": "lognorm", "fit_kwargs": {"floc": 0}}

        Curve keys (dictionary or ``DistCurveConfig``)
        ----------------------------------------------
        What is drawn: ``dist``, ``params`` (known), ``fit_kwargs``
        (fit) and ``bw_method`` (kde).

        How it looks: ``color`` (``c``), ``linewidth`` (``lw``),
        ``linestyle`` (``ls``), ``alpha``, ``zorder``, ``label``,
        ``label_template``, ``legend`` (False hides it), ``param_fmt``,
        ``param_sep``, ``fill`` (True or ``{"color", "alpha",
        "zorder", "hatch"}``) and ``line_kwargs`` (extra ``Axes.plot``
        arguments).

        ``label_template`` fields: ``{series}``, ``{ticker}``,
        ``{dist}`` (pretty name), ``{dist_key}`` (scipy name),
        ``{kind}`` (ajustada / teórica), ``{params}`` (all parameters
        as text, formatted with ``param_fmt`` / ``param_sep``), ``{n}``,
        every parameter by name (``{loc}``, ``{scale}``, ``{df}``...),
        ``{mu}`` / ``{sigma}`` (aliases of loc / scale) and
        ``{bandwidth}`` (kde).

        curve_points:
            Number of points used to evaluate the curves.
        x_range:
            Optional ``(min, max)`` of the distribution axis data.
            Either side may be None to use the data limit.
        lw:
            Default line width of the curves (overridden by the
            ``linewidth`` / ``lw`` of a curve).
        x_axis:
            Shared X-axis configuration (dictionary or ``XAxisConfig``)
            applied to the distribution axis, like in the other charts.
            Supported fields: ``fmt`` (number format, e.g. ``".1%"``),
            ``tick_step`` (in axis units), ``tick_values``,
            ``tick_labels``, ``tick_label_map``, ``fontsize``,
            ``rotation``, ``ha``, ``va``, ``label_color`` and ``lim``
            (view limits; use ``x_range`` to restrict the data).
            When given as a dictionary it also accepts ``fontweight``,
            ``fontstyle``, ``tick_color``, ``spine_color``,
            ``axis_label``, ``axis_label_fontsize`` and
            ``axis_label_color``.
        Returns
        -------
        Self
            The current graph instance.
        """
        if not isinstance(df_index, int):
            raise TypeError("'df_index' must be an integer.")
        if stat not in _VALID_STATS:
            raise ValueError(
                "'stat' must be 'density', 'count' or 'probability'."
            )
        if not isinstance(common_bins, bool):
            raise TypeError("'common_bins' must be a boolean.")
        if not isinstance(hist_alpha, (int, float)):
            raise TypeError("'hist_alpha' must be numeric.")
        if not 0 <= hist_alpha <= 1:
            raise ValueError("'hist_alpha' must be between 0 and 1.")
        if not isinstance(curve_points, int) or curve_points < 20:
            raise ValueError(
                "'curve_points' must be an integer >= 20."
            )
        if not isinstance(lw, (int, float)) or lw <= 0:
            raise ValueError("'lw' must be a positive number.")
        if x_range is not None and (
            not isinstance(x_range, (tuple, list))
            or len(x_range) != 2
        ):
            raise ValueError(
                "'x_range' must be a tuple (min, max)."
            )

        dataframe = self._select_df(df_idx=df_index)
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "The selected object must be a pandas DataFrame."
            )
        if dataframe.empty:
            raise ValueError(
                "Cannot create a distribution chart from an "
                "empty DataFrame."
            )

        x_axis_config, x_axis_explicit, x_axis_extras = (
            self._resolve_dist_xaxis(x_axis)
        )

        series_config = self._normalize_dist_series(
            dataframe=dataframe,
            series=series,
            known=known,
            fit=fit,
        )
        observations = {
            item["ticker"]: self._dist_series_values(
                dataframe,
                item["ticker"],
            )
            for item in series_config
        }

        # ---- shared grid / bins ------------------------------------
        pooled = np.concatenate(
            [
                values.to_numpy(dtype=float)
                for values in observations.values()
            ]
        )
        range_low = None if x_range is None else x_range[0]
        range_high = None if x_range is None else x_range[1]
        data_low = (
            float(pooled.min()) if range_low is None
            else float(range_low)
        )
        data_high = (
            float(pooled.max()) if range_high is None
            else float(range_high)
        )
        if data_high <= data_low:
            raise ValueError(
                "The distribution axis has no width. Check the data "
                "or 'x_range'."
            )
        hist_range = (data_low, data_high)

        def _edges(array: np.ndarray) -> np.ndarray:
            if isinstance(bins, (list, tuple, np.ndarray, pd.Index)):
                return np.asarray(bins, dtype=float)
            return np.histogram_bin_edges(
                array,
                bins=bins,
                range=hist_range,
            )

        shared_edges = _edges(pooled) if common_bins else None
        padding = (
            0.0
            if x_range is not None
            else 0.05 * (data_high - data_low)
        )
        grid = np.linspace(
            data_low - padding,
            data_high + padding,
            curve_points,
        )

        if not hasattr(self, "_ax") or self._ax is None:
            self.plot()
        ax = self._ax

        # ---- draw ----------------------------------------------------
        multiple_series = len(series_config) > 1
        dist_data: dict[str, dict[str, Any]] = {}
        for item in series_config:
            ticker = item["ticker"]
            values = observations[ticker]
            array = values.to_numpy(dtype=float)
            edges = shared_edges if common_bins else _edges(array)
            bin_width = float(np.mean(np.diff(edges)))
            if stat == "count":
                scale = len(array) * bin_width
            elif stat == "probability":
                scale = bin_width
            else:
                scale = 1.0

            heights = None
            patches = None
            if item["hist"]:
                hist_kwargs: dict[str, Any] = {
                    "bins": edges,
                    "color": item["color"],
                    "alpha": float(hist_alpha),
                    "edgecolor": hist_edgecolor,
                    "linewidth": hist_linewidth,
                    "label": item["label"],
                    "zorder": 2,
                }
                if stat == "density":
                    hist_kwargs["density"] = True
                elif stat == "probability":
                    hist_kwargs["weights"] = np.full(
                        len(array),
                        1.0 / len(array),
                    )
                if hist_style:
                    hist_kwargs.update(hist_style)
                heights, _, patches = ax.hist(array, **hist_kwargs)

            curves: list[dict[str, Any]] = []
            for kind, specs in (
                ("fit", item["fit"]),
                ("known", item["known"]),
            ):
                for curve_index, raw_spec in enumerate(specs):
                    curve = self._compute_dist_curve(
                        raw_spec=raw_spec,
                        kind=kind,
                        values=array,
                        grid=grid,
                        scale=scale,
                        series_ticker=ticker,
                        series_label=item["label"],
                        series_color=item["color"],
                        lw=float(lw),
                        prefix_label=multiple_series,
                        curve_index=curve_index,
                    )
                    (line,) = ax.plot(
                        curve["x"],
                        curve["y"],
                        color=curve["color"],
                        linestyle=curve["linestyle"],
                        linewidth=curve["linewidth"],
                        alpha=curve["alpha"],
                        zorder=curve["zorder"],
                        label=curve["label"],
                        **curve["line_kwargs"],
                    )
                    curve["artist"] = line
                    if curve["fill"] is not None:
                        fill = curve["fill"]
                        curve["fill_artist"] = ax.fill_between(
                            curve["x"],
                            0.0,
                            curve["y"],
                            color=fill.get("color", curve["color"]),
                            alpha=float(fill.get("alpha", 0.15)),
                            zorder=float(
                                fill.get("zorder", curve["zorder"] - 0.5)
                            ),
                            hatch=fill.get("hatch"),
                            linewidth=0,
                            label="_nolegend_",
                        )
                    curves.append(curve)

            dist_data[ticker] = {
                "series": values,
                "values": array,
                "label": item["label"],
                "color": item["color"],
                "edges": np.asarray(edges, dtype=float),
                "heights": (
                    None if heights is None
                    else np.asarray(heights, dtype=float)
                ),
                "patches": patches,
                "curves": curves,
                "stat": stat,
            }

        # ---- metadata ------------------------------------------------
        state = self._ensure_active_state()
        state.dataframe_idx = df_index
        state.dataframe = dataframe
        state.series_config = series_config
        state.axis_map = {
            item["ticker"]: "left"
            for item in series_config
        }
        state.ticker_label_color = [
            (item["ticker"], item["label"], item["color"])
            for item in series_config
        ]
        state.dist_data = dist_data
        state.x_axis_mode = "numeric"
        state.x_axis_fechas = None
        state.x_vals = grid
        axis_metadata = self._apply_dist_xaxis(
            x_axis_config=x_axis_config,
            explicit=x_axis_explicit,
            extras=x_axis_extras,
            grid=grid,
        )
        axis_metadata["stat"] = stat
        axis_metadata["tickers"] = [
            item["ticker"] for item in series_config
        ]
        state.x_axis_metadata = axis_metadata
        self._df = dataframe
        self._ticker_label_color = state.ticker_label_color

        self._apply_dist_tags(
            series_config=series_config,
            dist_data=dist_data,
        )
        self._ax = ax
        return self
