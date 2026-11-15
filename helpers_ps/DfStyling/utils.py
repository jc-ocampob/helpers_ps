from __future__ import annotations

import math
import re
import warnings
from typing import Any

import pandas as pd
from pandas.io.formats.style import Styler

from .constants import (
    DEFAULT_LINE_STYLE,
)


def ensure_styler(
    obj: pd.DataFrame | Styler,
) -> Styler:
    """
    Return a Styler object.
    """
    if isinstance(obj, Styler):
        return obj

    if isinstance(obj, pd.DataFrame):
        return obj.style

    raise TypeError(
        "obj must be a pandas DataFrame or Styler."
    )


def style_dict_to_css(
    styles: dict[str, Any],
) -> str:
    """
    Convert a style dictionary to CSS.
    """
    return "; ".join(
        f"{key}: {value}"
        for key, value in styles.items()
    )


def merge_styles(
    default_styles: dict,
    custom_styles: dict | None,
) -> dict:
    """
    Merge default and custom styles.
    """
    final_styles = default_styles.copy()

    if custom_styles:
        final_styles.update(custom_styles)

    return final_styles


# CSS names accepted by the border helpers, mapped to the three real options.
_BORDER_OPTION_ALIASES = {
    "width": "width",
    "border-width": "width",
    "border_width": "width",
    "style": "style",
    "line_style": "style",
    "line-style": "style",
    "border-style": "style",
    "border_style": "style",
    "color": "color",
    "border-color": "color",
    "border_color": "color",
}

_PX_WIDTH = re.compile(r"^\s*(\d*\.?\d+)\s*px\s*$", re.IGNORECASE)


def _normalize_border_width(width: Any) -> str:
    """
    Return a CSS border width and warn when it cannot be drawn as asked.

    Browsers draw the borders of a table (``border-collapse: collapse``) in
    whole CSS pixels with a minimum of 1px: ``0.1px``, ``0.5px`` and ``1px``
    look the same and ``1.5px`` is drawn as ``1px``.
    """
    if isinstance(width, bool):
        raise TypeError(
            "width must be a CSS length such as '1px' or a number of pixels."
        )

    if isinstance(width, (int, float)):
        width = f"{width:g}px"

    width = str(width)
    match = _PX_WIDTH.match(width)

    if match:
        value = float(match.group(1))
        drawn = math.floor(value)

        if value > 0 and drawn != value:
            drawn = max(drawn, 1)
            warnings.warn(
                f"Table borders are drawn in whole CSS pixels: "
                f"{width.strip()!r} is drawn as {drawn}px. For a thinner "
                "line raise the table font_size: the sheet scales the table "
                "to its cell, so the text keeps its size and a 1px line "
                "becomes relatively thinner.",
                UserWarning,
                stacklevel=2,
            )

    return width


def build_border_css(
    position: str | None,
    styles: dict | None = None,
) -> str:
    """
    Build border CSS.

    Parameters
    ----------
    position : str | None
        ``"top"``, ``"bottom"``, ``"left"`` or ``"right"``. ``None`` builds
        the shorthand for all four sides (``border: ...``).
    styles : dict | None, default None
        Any of ``"width"``, ``"style"`` (or ``"line_style"``) and
        ``"color"``. The CSS names ``"border-width"``, ``"border-style"`` and
        ``"border-color"`` are accepted too. Missing options use
        ``DEFAULT_LINE_STYLE``. A number is a width in pixels.

    Raises
    ------
    ValueError
        If ``styles`` contains any other key. Unknown keys used to be ignored
        silently, so a typo kept the default line.
    """
    options = dict(DEFAULT_LINE_STYLE)

    for key, value in (styles or {}).items():
        target = _BORDER_OPTION_ALIASES.get(key)

        if target is None:
            raise ValueError(
                f"Unknown border option {key!r}. Valid options are 'width', "
                "'style' (or 'line_style') and 'color'; 'border-width', "
                "'border-style' and 'border-color' are accepted as well. "
                "For any other CSS use style_cells() or apply_styler()."
            )

        options[target] = value

    width = _normalize_border_width(options["width"])
    prop = "border" if position is None else f"border-{position}"

    return f"{prop}: {width} {options['style']} {options['color']}"


def apply_table_styles(
    styler: Styler,
    selectors: list[str],
    css: str,
) -> Styler:
    """
    Apply CSS to selectors.
    """
    table_styles = [
        {
            "selector": selector,
            "props": css,
        }
        for selector in selectors
    ]

    return styler.set_table_styles(
        table_styles,
        overwrite=False,
    )
