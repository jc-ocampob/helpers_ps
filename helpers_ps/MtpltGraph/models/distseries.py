"""
Series configuration models for distribution (histogram) charts.

Mirrors the conventions used by ``barseries.py`` and ``boxseries.py``:
a dataclass for user input, a TypedDict for the normalized form and a
``*Like`` alias accepting either.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import (
    Any,
    Callable,
    Literal,
    TypeAlias,
    TypedDict,
)

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------
DistStat: TypeAlias = Literal[
    "density",
    "count",
    "probability",
]

DistTagMode: TypeAlias = Literal[
    "observation",
    "value",
    "statistic",
]

DistYFrom: TypeAlias = Literal[
    "auto",
    "hist",
    "curve",
]

DistLineExtent: TypeAlias = Literal[
    "curve",
    "top",
]

DistObservation: TypeAlias = (
    str
    | int
    | float
    | date
    | datetime
    | pd.Timestamp
    | np.datetime64
)

DistObservations: TypeAlias = (
    Literal["first", "last"]
    | DistObservation
    | list[DistObservation]
    | tuple[DistObservation, ...]
    | set[DistObservation]
)

# A curve can be declared as:
#   - a scipy.stats distribution name: "norm", "t", "lognorm", "kde", ...
#   - a dictionary (see DistCurveDict)
#   - a frozen scipy distribution (anything exposing ``.pdf``)
#   - a callable ``pdf(x) -> y``
DistCurveSpec: TypeAlias = (
    str
    | dict[str, Any]
    | Callable[..., Any]
    | Any
)

_VALID_SHOW_TOKENS = {"line", "tag", "dot"}
_STATISTIC_PATTERN = re.compile(
    r"^(mean|median|q1|q3|min|max|p\d+(\.\d+)?)$"
)


def parse_dist_show(show: str) -> set[str]:
    """
    Parse the ``show`` option of a distribution tag.

    ``show`` is any combination of ``"line"``, ``"tag"`` and ``"dot"``
    separated by non-letter characters, e.g. ``"line"``, ``"line_tag"``,
    ``"line_tag_dot"`` or ``"tag+dot"``.
    """
    if not isinstance(show, str):
        raise TypeError("'show' must be a string.")
    tokens = {
        token
        for token in re.split(r"[^a-z]+", show.lower())
        if token
    }
    invalid = tokens - _VALID_SHOW_TOKENS
    if not tokens or invalid:
        raise ValueError(
            "'show' must combine 'line', 'tag' and 'dot' "
            "(for example 'line_tag_dot'). "
            f"Received: {show!r}."
        )
    return tokens


def is_valid_dist_statistic(statistic: Any) -> bool:
    """Return True for 'mean', 'median', 'q1', 'q3', 'min', 'max' or 'p<N>'."""
    if not isinstance(statistic, str):
        return False
    match = _STATISTIC_PATTERN.match(statistic.lower())
    if match is None:
        return False
    if statistic.lower().startswith("p"):
        return 0 <= float(statistic[1:]) <= 100
    return True


def normalize_curve_specs(
    value: Any,
    *,
    field: str,
) -> list[Any] | None:
    """
    Normalize a ``known`` / ``fit`` declaration into a list of curve specs.

    None stays None (meaning "inherit the function-level default"), an
    empty list means "no curves" and a single spec is wrapped in a list.
    """
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        specs = list(value)
    else:
        specs = [value]
    for position, spec in enumerate(specs):
        if isinstance(spec, str):
            if not spec.strip():
                raise ValueError(
                    f"'{field}' contains an empty distribution "
                    f"name at position {position}."
                )
            if field == "known" and spec.strip().lower() == "kde":
                raise ValueError(
                    "'kde' is an estimated curve; use it in 'fit', "
                    "not in 'known'."
                )
            continue
        if isinstance(spec, dict):
            if "dist" not in spec:
                raise ValueError(
                    f"Every dictionary in '{field}' must define "
                    f"'dist'. Invalid item at position {position}."
                )
            if field == "fit" and not isinstance(spec["dist"], str):
                raise TypeError(
                    "'dist' inside 'fit' must be a scipy.stats "
                    "distribution name or 'kde'. Invalid item at "
                    f"position {position}."
                )
            continue
        if field == "fit":
            raise TypeError(
                "'fit' only accepts distribution names or "
                "dictionaries, because the parameters are estimated "
                f"from the data. Invalid item at position {position}."
            )
        if not (hasattr(spec, "pdf") or callable(spec)):
            raise TypeError(
                f"Invalid item at position {position} in '{field}'. "
                "Use a distribution name, a dictionary, a frozen "
                "scipy distribution or a callable pdf(x)."
            )
    return specs


# ---------------------------------------------------------------------------
# TypedDicts
# ---------------------------------------------------------------------------
class DistCurveDict(TypedDict, total=False):
    """
    Configuration of one overlaid curve.

    For ``known`` curves:
        - ``dist``: scipy.stats name ("norm", "t", ...), frozen
          distribution or callable pdf(x).
        - ``params``: dict (``{"loc": 0, "scale": 1}``) or tuple of
          positional parameters. Omitted -> scipy defaults.

    For ``fit`` curves (parameters estimated from the data):
        - ``dist``: scipy.stats name or ``"kde"``.
        - ``fit_kwargs``: extra kwargs for ``dist.fit`` (e.g.
          ``{"floc": 0}``).
        - ``bw_method``: bandwidth for ``"kde"``.

    Style fields are optional.
    """
    dist: Any
    params: dict[str, float] | tuple[float, ...] | list[float]
    fit_kwargs: dict[str, Any]
    bw_method: Any
    label: str | None
    color: str
    linewidth: float
    linestyle: str
    alpha: float
    zorder: float


class DistTagLineDict(TypedDict, total=False):
    """Style of the vertical reference line."""
    extent: DistLineExtent
    color: str
    linestyle: str
    linewidth: float
    alpha: float
    zorder: float


class DistTagLabelDict(TypedDict, total=False):
    """Controls passed directly to ``self.tag()``."""
    ubic_etq: tuple[float, float]
    label_h_align: str
    label_v_align: str
    fontsize: float
    fontweight: str | int
    font_color: str
    bg_color: str
    bg_alpha: float
    edge_color: str
    show_bbox: bool
    text_edge_color: str | None
    text_edge_width: float
    zorder: float


class DistTagDotDict(TypedDict, total=False):
    """Controls passed directly to ``self.dot()`` (without x/y)."""
    color: str
    size: float
    marker: str
    markersize: float
    marker_color: str
    marker_edgecolor: str
    marker_edgewidth: float
    alpha: float
    zorder: float
    clip_on: bool
    label: str
    legend: bool


class DistTagDict(TypedDict, total=False):
    """
    Configuration of one highlighted reference on a distribution.

    How the reference is selected (``mode``):
        - ``"observation"``: ``x_values`` picks observations from the
          DataFrame (``"last"``, ``"first"`` or index labels). The value
          of the series at that label is highlighted.
        - ``"value"``: ``value`` is a literal number (or list) on the
          distribution axis.
        - ``"statistic"``: ``statistic`` is one of ``"mean"``,
          ``"median"``, ``"q1"``, ``"q3"``, ``"min"``, ``"max"`` or
          ``"p<N>"`` (percentile, e.g. ``"p5"``, ``"p95"``).

    If ``mode`` is omitted it is inferred: ``statistic`` -> statistic,
    ``value`` -> value, otherwise observation.

    ``show`` combines ``"line"``, ``"tag"`` and ``"dot"``
    (default ``"line_tag"``).

    ``template`` / ``legend_label`` are formatted with:
    ``{ticker}``, ``{label}``, ``{x_value}``, ``{value}``,
    ``{y_value}`` (alias of value), ``{statistic}``, ``{percentile}``
    (empirical rank 0-100), ``{zscore}`` and ``{density}`` (height used
    to anchor the dot / tag).
    """
    mode: DistTagMode
    x_values: DistObservations
    value: float | list[float] | tuple[float, ...]
    statistic: str | list[str] | tuple[str, ...]
    show: str
    template: str
    legend_label: str | None
    y_from: DistYFrom
    line: DistTagLineDict | None
    tag: DistTagLabelDict | None
    dot: DistTagDotDict | None


class DistSeriesDict(TypedDict):
    """Normalized dictionary representation of one distribution series."""
    ticker: str
    label: str | None
    color: str | None
    hist: bool
    known: list[Any] | None
    fit: list[Any] | None
    tag: list[DistTagDict] | None


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class DistSeriesConfig:
    """
    Configuration for one distribution series.

    Parameters
    ----------
    ticker:
        DataFrame column whose values form the distribution.
    label:
        Display label used by the legend and tags. If None, the ticker
        is used.
    color:
        Histogram color. If None it is assigned from PALETA_COLORES.
    hist:
        Whether to draw the histogram. If False only the curves are
        drawn (at least one curve is then required).
    known:
        Curve(s) of a known distribution drawn over the series. None
        inherits the ``known`` argument of ``graph_dist``; ``[]``
        disables it for this series.
    fit:
        Curve(s) estimated from the series data. None inherits the
        ``fit`` argument of ``graph_dist``; ``[]`` disables it.
    tag:
        Highlighted references (see ``DistTagDict``).
    """
    ticker: str
    label: str | None = None
    color: str | None = None
    hist: bool = True
    known: Any = None
    fit: Any = None
    tag: list[DistTagDict] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.ticker, str):
            raise TypeError("'ticker' must be a string.")
        if not self.ticker.strip():
            raise ValueError("'ticker' cannot be empty.")
        if (
            self.label is not None
            and not isinstance(self.label, str)
        ):
            raise TypeError("'label' must be a string or None.")
        if (
            self.color is not None
            and not isinstance(self.color, str)
        ):
            raise TypeError("'color' must be a string or None.")
        if not isinstance(self.hist, bool):
            raise TypeError("'hist' must be a boolean.")
        normalize_curve_specs(self.known, field="known")
        normalize_curve_specs(self.fit, field="fit")
        if self.tag is None:
            return
        if not isinstance(self.tag, list):
            raise TypeError(
                "'tag' must be a list of dictionaries or None."
            )
        valid_modes = {"observation", "value", "statistic"}
        for position, reference in enumerate(self.tag):
            if not isinstance(reference, dict):
                raise TypeError(
                    "Each item inside 'tag' must be a dictionary. "
                    f"Invalid item at position {position}."
                )
            mode = reference.get(
                "mode",
                (
                    "statistic" if "statistic" in reference
                    else "value" if "value" in reference
                    else "observation"
                ),
            )
            if mode not in valid_modes:
                raise ValueError(
                    "'mode' must be 'observation', 'value' or "
                    f"'statistic'. Invalid item at position {position}."
                )
            if mode == "value" and "value" not in reference:
                raise ValueError(
                    "A reference with mode='value' must define "
                    f"'value'. Invalid item at position {position}."
                )
            if mode == "statistic":
                if "statistic" not in reference:
                    raise ValueError(
                        "A reference with mode='statistic' must "
                        f"define 'statistic'. Invalid item at "
                        f"position {position}."
                    )
                stats = reference["statistic"]
                stats = (
                    list(stats)
                    if isinstance(stats, (list, tuple))
                    else [stats]
                )
                for statistic in stats:
                    if not is_valid_dist_statistic(statistic):
                        raise ValueError(
                            "'statistic' must be 'mean', 'median', "
                            "'q1', 'q3', 'min', 'max' or 'p<N>' "
                            f"(0 <= N <= 100). Invalid item at "
                            f"position {position}: {statistic!r}."
                        )
            if "show" in reference:
                parse_dist_show(reference["show"])
            template = reference.get("template")
            if (
                template is not None
                and not isinstance(template, str)
            ):
                raise TypeError(
                    "'template' must be a string. Invalid item at "
                    f"position {position}."
                )
            y_from = reference.get("y_from", "auto")
            if y_from not in {"auto", "hist", "curve"}:
                raise ValueError(
                    "'y_from' must be 'auto', 'hist' or 'curve'. "
                    f"Invalid item at position {position}."
                )
            for key in ("line", "tag", "dot"):
                style = reference.get(key)
                if style is not None and not isinstance(style, dict):
                    raise TypeError(
                        f"'{key}' inside a distribution reference "
                        "must be a dictionary or None. Invalid item "
                        f"at position {position}."
                    )


DistSeriesLike: TypeAlias = (
    DistSeriesConfig
    | DistSeriesDict
)
