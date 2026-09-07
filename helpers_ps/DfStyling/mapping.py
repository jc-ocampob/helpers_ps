from __future__ import annotations

from .models import Real, ColorRanges

import pandas as pd

# ---------------------------------------------------------------------
# Range-based conditional styles
# ---------------------------------------------------------------------

def _style_by_range(
    value: Real,
    ranges: ColorRanges,
    css_property: str,
) -> str:
    """
    Build a CSS declaration by matching a numeric value to a range.

    Parameters
    ----------
    value : numbers.Real
        Numeric value to evaluate.

    ranges : Mapping[tuple[Real, Real], str]
        Mapping in which each key is a ``(lower, upper)`` interval and
        each value is the CSS value associated with that interval.
        Intervals use lower-inclusive and upper-exclusive matching:
        ``lower <= value < upper``.

    css_property : str
        CSS property name to return when a matching range is found.

    Returns
    -------
    str
        CSS declaration for the first matching interval. An empty string
        is returned when the value is missing or no interval matches.

    Notes
    -----
    Ranges are evaluated in insertion order. If intervals overlap, the
    first matching interval is used.
    """
    if pd.isna(value):
        return ""

    for (lower, upper), css_value in ranges.items():
        if lower <= value < upper:
            return f"{css_property}: {css_value}"

    return ""


def text_color_by_range(
    value: Real,
    ranges: ColorRanges,
) -> str:
    """
    Select a text color according to the range containing a value.

    Parameters
    ----------
    value : numbers.Real
        Numeric value to evaluate.

    ranges : Mapping[tuple[Real, Real], str]
        Mapping from lower-inclusive, upper-exclusive numeric intervals
        to CSS colors.

    Returns
    -------
    str
        CSS text color declaration. An empty string is returned when the
        value is missing or no interval matches.

    Examples
    --------
    >>> import numpy as np
    >>>
    >>> text_color_by_range(
    ...     0.08,
    ...     {
    ...         (-np.inf, 0): "red",
    ...         (0, 0.05): "orange",
    ...         (0.05, np.inf): "green",
    ...     },
    ... )
    'color: green'
    """
    return _style_by_range(
        value=value,
        ranges=ranges,
        css_property="color",
    )


def background_color_by_range(
    value: Real,
    ranges: ColorRanges,
) -> str:
    """
    Select a background color according to the range containing a value.

    Parameters
    ----------
    value : numbers.Real
        Numeric value to evaluate.

    ranges : Mapping[tuple[Real, Real], str]
        Mapping from lower-inclusive, upper-exclusive numeric intervals
        to CSS colors.

    Returns
    -------
    str
        CSS background color declaration. An empty string is returned
        when the value is missing or no interval matches.

    Examples
    --------
    >>> import numpy as np
    >>>
    >>> background_color_by_range(
    ...     0.08,
    ...     {
    ...         (-np.inf, 0): "#F4CCCC",
    ...         (0, 0.05): "#FFF2CC",
    ...         (0.05, np.inf): "#D9EAD3",
    ...     },
    ... )
    'background-color: #D9EAD3'
    """
    return _style_by_range(
        value=value,
        ranges=ranges,
        css_property="background-color",
    )
