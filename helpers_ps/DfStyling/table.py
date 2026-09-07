from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from typing import NotRequired, TypedDict, TypeAlias

from pandas import DataFrame
from pandas.io.formats.style import Styler

from .selectors import (
    get_column_header_selectors,
    get_header_selector,
    get_index_selector,
    get_index_value_selectors,
)
from .utils import (
    apply_table_styles,
    ensure_styler,
    style_dict_to_css,
)


# ---------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------

StylerLike: TypeAlias = DataFrame | Styler
CSSProperties: TypeAlias = Mapping[str, str]

ColumnTarget: TypeAlias = Hashable | Sequence[Hashable]
IndexTarget: TypeAlias = Hashable | Sequence[Hashable]


# ---------------------------------------------------------------------
# Typed configurations
# ---------------------------------------------------------------------

class HeaderStyleConfig(TypedDict):
    """
    Configuration for styling selected column headers.

    Attributes
    ----------
    columns : Hashable | Sequence[Hashable]
        Column label or collection of column labels to style.

    styles : Mapping[str, str]
        CSS properties applied to the selected headers.

    level : int, optional
        Header level to style. If omitted, the final column-header level
        is used.
    """

    columns: ColumnTarget
    styles: CSSProperties
    level: int


class IndexStyleConfig(TypedDict):
    """
    Configuration for styling selected row-index values.

    Attributes
    ----------
    values : Hashable | Sequence[Hashable]
        Index value or collection of index values to style.

    level : int | str
        Zero-based index level or index-level name containing the target
        values.

    styles : Mapping[str, str]
        CSS properties applied to matching index cells.

    parent : tuple[Hashable, ...], optional
        Optional path containing the values of preceding index levels.
        This distinguishes repeated labels across different sections.
    """

    values: IndexTarget
    level: int | str
    styles: CSSProperties
    parent: NotRequired[tuple[Hashable, ...]]


# ---------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------

def _apply_selector_styles(
    styler: Styler,
    selectors: Sequence[str],
    styles: CSSProperties,
) -> Styler:
    """
    Apply CSS properties to a collection of selectors.

    Parameters
    ----------
    styler : pandas.io.formats.style.Styler
        Styler to modify.

    selectors : Sequence[str]
        CSS selectors receiving the styles.

    styles : Mapping[str, str]
        CSS properties to apply.

    Returns
    -------
    pandas.io.formats.style.Styler
        Updated Styler object.
    """
    if not selectors or not styles:
        return styler

    css = style_dict_to_css(styles)

    return apply_table_styles(
        styler,
        list(selectors),
        css,
    )


# ---------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------

def style_table(
    obj: StylerLike,
    font_family: str | None = None,
    font_size: str | int | float | None = None,
    text_color: str | None = None,
    background_color: str | None = None,
    text_align: str | None = None,
    header_styles: CSSProperties | None = None,
    index_styles: CSSProperties | None = None,
    data_styles: CSSProperties | None = None,
    column_header_styles: Sequence[HeaderStyleConfig] | None = None,
    row_index_styles: Sequence[IndexStyleConfig] | None = None,
    show_index_names: bool = True,
) -> Styler:
    """
    Configure the general appearance of a DataFrame table.

    The function applies global typography and table colors, default
    styles for column headers and row-index cells, and targeted styles
    for selected column headers or index values.

    Sparse MultiIndex rendering is preserved. Targeted row-index styles
    are applied to the physical HTML cells that represent each visible
    sparse MultiIndex label.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object to modify.

    font_family : str | None, default None
        CSS font family applied to header, index, and data cells.

        Examples include ``"Arial"``, ``"Calibri"``, and
        ``"'Aptos', sans-serif"``.

    font_size : str | int | float | None, default None
        Font size applied to header, index, and data cells.

        Numeric values are interpreted as pixels. String values may use
        any valid CSS unit, such as ``"10px"``, ``"0.8rem"``, or
        ``"9pt"``.

    text_color : str | None, default None
        Default CSS text color applied to the complete table.

    background_color : str | None, default None
        Default CSS background color applied to header, index, and data
        cells.

    text_align : str | None, default None
        Default CSS text alignment.

        Common values include ``"left"``, ``"center"``, and ``"right"``.

    header_styles : Mapping[str, str] | None, default None
        Default CSS properties applied to all column-header cells.

    index_styles : Mapping[str, str] | None, default None
        Default CSS properties applied to all row-index cells.

    data_styles : Mapping[str, str] | None, default None
        Default CSS properties applied to all data cells.

    column_header_styles : Sequence[HeaderStyleConfig] | None, default None
        Targeted styling rules for selected column headers.

        Each configuration must contain ``"columns"`` and ``"styles"``.
        The optional ``"level"`` key identifies a specific header level.

    row_index_styles : Sequence[IndexStyleConfig] | None, default None
        Targeted styling rules for selected row-index values.

        Each configuration must contain ``"values"``, ``"level"``, and
        ``"styles"``.
    
    show_index_names : bool, default True
        Whether DataFrame index-level names are displayed.

        If ``False``, index names such as ``"Metric"``, ``"Period"``,
        and ``"Rating"`` are hidden without modifying the underlying
        DataFrame index names.

    Returns
    -------
    pandas.io.formats.style.Styler
        Styler containing the table configuration.

    Examples
    --------
    Apply basic typography.

    >>> styled = style_table(
    ...     obj=df,
    ...     font_family="Arial",
    ...     font_size=10,
    ...     text_align="center",
    ... )

    Apply targeted header and index colors.

    >>> styled = style_table(
    ...     obj=df,
    ...     font_family="Arial",
    ...     font_size="10px",
    ...     header_styles={
    ...         "color": "white",
    ...         "font-weight": "bold",
    ...     },
    ...     column_header_styles=[
    ...         {
    ...             "columns": ["1M", "2M", "3M"],
    ...             "level": 0,
    ...             "styles": {
    ...                 "background-color": "#3075DB",
    ...             },
    ...         },
    ...     ],
    ...     row_index_styles=[
    ...         {
    ...             "values": "Δ Yield",
    ...             "level": 0,
    ...             "styles": {
    ...                 "background-color": "#B7331F",
    ...                 "color": "white",
    ...             },
    ...         },
    ...     ],
    ... )
    """
    styler = ensure_styler(obj)

    if not isinstance(show_index_names, bool):
        raise TypeError(
            "show_index_names must be a boolean."
        )

    if not show_index_names:
        styler = styler.hide(
            axis="index",
            names=True,
        )

    general_styles: dict[str, str] = {}

    if font_family is not None:
        general_styles["font-family"] = font_family

    if font_size is not None:
        general_styles["font-size"] = (
            f"{font_size}px"
            if isinstance(font_size, (int, float))
            else font_size
        )

    if text_color is not None:
        general_styles["color"] = text_color

    if background_color is not None:
        general_styles["background-color"] = background_color

    if text_align is not None:
        general_styles["text-align"] = text_align

    styler = _apply_selector_styles(
        styler=styler,
        selectors=[
            "th.col_heading",
            "th.row_heading",
            "td",
        ],
        styles=general_styles,
    )

    if header_styles is not None:
        styler = _apply_selector_styles(
            styler=styler,
            selectors=get_header_selector(),
            styles=header_styles,
        )

    if index_styles is not None:
        styler = _apply_selector_styles(
            styler=styler,
            selectors=get_index_selector(),
            styles=index_styles,
        )

    if data_styles is not None:
        styler = _apply_selector_styles(
            styler=styler,
            selectors=["td"],
            styles=data_styles,
        )

    if column_header_styles is not None:
        for config in column_header_styles:
            selectors = get_column_header_selectors(
                df=styler.data,
                columns=config["columns"],
                header_level=config.get("level"),
            )

            styler = _apply_selector_styles(
                styler=styler,
                selectors=selectors,
                styles=config["styles"],
            )

    if row_index_styles is not None:
        for config in row_index_styles:
            selectors = get_index_value_selectors(
                df=styler.data,
                values=config["values"],
                level=config["level"],
                parent=config.get("parent"),
            )

            styler = _apply_selector_styles(
                styler=styler,
                selectors=selectors,
                styles=config["styles"],
            )

    return styler