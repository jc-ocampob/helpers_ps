from __future__ import annotations

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


def build_border_css(
    position: str,
    styles: dict | None = None,
) -> str:
    """
    Build border CSS.
    """

    final_styles = merge_styles(
        DEFAULT_LINE_STYLE,
        styles,
    )

    return (
        f"border-{position}: "
        f"{final_styles['width']} "
        f"{final_styles['style']} "
        f"{final_styles['color']}"
    )


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