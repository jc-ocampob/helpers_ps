from __future__ import annotations

from .constants import (
    DEFAULT_HIGHLIGHT_STYLE,
)

from .selectors import (
    get_row_selectors,
    get_column_selectors,
    get_cell_selector,
)

from .utils import (
    ensure_styler,
    merge_styles,
    style_dict_to_css,
    build_border_css,
    apply_table_styles,
)


def style_cell(
    obj,
    row,
    column,
    styles,
):
    """
    Apply one or more CSS styles to a single cell.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object.

    row : hashable
        Row label identifying the target row.
        For MultiIndex rows, provide the full tuple.

    column : hashable
        Column label identifying the target column.
        For MultiIndex columns, provide the full tuple.

    styles : dict
        Dictionary containing CSS style properties.

    Returns
    -------
    pandas.io.formats.style.Styler
        Updated Styler object.

    Examples
    --------
    Bold a single cell.

    >>> style_cell(
    ...     df,
    ...     row="Total",
    ...     column="YTD",
    ...     styles={
    ...         "font-weight": "bold"
    ...     }
    ... )

    Highlight a MultiIndex cell.

    >>> style_cell(
    ...     df,
    ...     row=("Fixed Income", "Government"),
    ...     column=("Performance", "YTD"),
    ...     styles={
    ...         "background-color": "yellow"
    ...     }
    ... )
    """

    styler = ensure_styler(
        obj
    )

    selector = (
        get_cell_selector(
            styler.data,
            row,
            column,
        )
    )

    css = style_dict_to_css(
        styles
    )

    return apply_table_styles(
        styler,
        [selector],
        css,
    )


def style_cells(
    obj,
    rows,
    columns,
    styles,
):
    """
    Apply one or more CSS styles to a group of cells.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object.

    rows : iterable
        Collection of row labels.

    columns : iterable
        Collection of column labels.

    styles : dict
        CSS properties to apply.

    Returns
    -------
    pandas.io.formats.style.Styler

    Examples
    --------
    Highlight a block of cells.

    >>> style_cells(
    ...     df,
    ...     rows=["Total", "Benchmark"],
    ...     columns=["YTD", "1Y"],
    ...     styles={
    ...         "background-color": "#FFF2CC"
    ...     }
    ... )
    """

    styler = ensure_styler(obj)

    css = style_dict_to_css(styles)

    selectors = []

    for row in rows:
        for column in columns:

            selectors.append(
                get_cell_selector(
                    styler.data,
                    row,
                    column,
                )
            )

    return apply_table_styles(
        styler,
        selectors,
        css,
    )


def border_cell(
    obj,
    row,
    column,
    position="top",
    width="1px",
    color="black",
    line_style="solid",
):
    """
    Add a border to a single cell.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler

    row : hashable
        Row label.

    column : hashable
        Column label.

    position : {"top", "bottom", "left", "right"}, default "top"
        Border position.

    width : str, default "1px"
        Border width.

    color : str, default "black"
        Border color.

    line_style : str, default "solid"
        CSS border style.

    Returns
    -------
    pandas.io.formats.style.Styler

    Examples
    --------
    Add a top border.

    >>> border_cell(
    ...     df,
    ...     row="Total",
    ...     column="YTD",
    ...     position="top"
    ... )

    Add a thick red border.

    >>> border_cell(
    ...     df,
    ...     row="Total",
    ...     column="YTD",
    ...     position="bottom",
    ...     width="3px",
    ...     color="red"
    ... )
    """
    return style_cell(
        obj=obj,
        row=row,
        column=column,
        styles={
            f"border-{position}":
            f"{width} {line_style} {color}"
        },
    )


def border_cells(
    obj,
    rows,
    columns,
    position="top",
    width="1px",
    color="black",
    line_style="solid",
):
    """
    Add borders to multiple cells.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler

    rows : iterable
        Collection of row labels.

    columns : iterable
        Collection of column labels.

    position : {"top", "bottom", "left", "right"}, default "top"

    width : str, default "1px"

    color : str, default "black"

    line_style : str, default "solid"

    Returns
    -------
    pandas.io.formats.style.Styler

    Examples
    --------
    Add a bottom border to a summary section.

    >>> border_cells(
    ...     df,
    ...     rows=["Total"],
    ...     columns=["YTD", "1Y", "3Y"],
    ...     position="bottom"
    ... )
    """
    return style_cells(
        obj=obj,
        rows=rows,
        columns=columns,
        styles={
            f"border-{position}":
            f"{width} {line_style} {color}"
        },
    )


def highlight_rows(
    obj,
    rows,
    styles=None,
    include_index=True,
    index_level=None,
):
    """
    Highlight one or more rows.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler

    rows : hashable | iterable
        Row label(s) to highlight.

    styles : dict, optional
        CSS properties that override the default highlight style.

    include_index : bool, default True
        Whether row index labels should receive the same style.

    index_level : int, optional
        Maximum MultiIndex level to style.

    Returns
    -------
    pandas.io.formats.style.Styler

    Examples
    --------
    Highlight a total row.

    >>> highlight_rows(
    ...     df,
    ...     rows="Total"
    ... )

    Highlight multiple rows.

    >>> highlight_rows(
    ...     df,
    ...     rows=["Benchmark", "Total"]
    ... )

    Highlight a MultiIndex row.

    >>> highlight_rows(
    ...     df,
    ...     rows=("Fixed Income", "Total")
    ... )
    """

    styler = ensure_styler(obj)

    selectors = get_row_selectors(
        styler.data,
        rows,
        include_index=include_index,
        index_level=index_level,
    )

    css = style_dict_to_css(
        merge_styles(
            DEFAULT_HIGHLIGHT_STYLE,
            styles,
        )
    )

    return apply_table_styles(
        styler,
        selectors,
        css,
    )


def highlight_columns(
    obj,
    columns,
    styles=None,
    include_header=True,
    header_level=None,
):
    """
    Highlight one or more columns.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler

    columns : hashable | iterable
        Column labels to highlight.

    styles : dict, optional
        Custom CSS properties.

    include_header : bool, default True
        Whether column headers should be highlighted.

    header_level : int, optional
        Maximum MultiIndex level to style.

    Returns
    -------
    pandas.io.formats.style.Styler

    Examples
    --------
    Highlight YTD and 1Y columns.

    >>> highlight_columns(
    ...     df,
    ...     columns=["YTD", "1Y"]
    ... )

    Highlight a MultiIndex column.

    >>> highlight_columns(
    ...     df,
    ...     columns=("Performance", "YTD")
    ... )
    """

    styler = ensure_styler(obj)

    selectors = get_column_selectors(
        styler.data,
        columns,
        include_header=include_header,
        header_level=header_level,
    )

    css = style_dict_to_css(
        merge_styles(
            DEFAULT_HIGHLIGHT_STYLE,
            styles,
        )
    )

    return apply_table_styles(
        styler,
        selectors,
        css,
    )


def add_row_line(
    obj,
    rows,
    position="bottom",
    include_index=True,
    index_level=None,
    styles=None,
):
    """
    Add a horizontal border to one or more rows.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler

    rows : hashable | iterable
        Row labels to modify.

    position : {"top", "bottom"}, default "bottom"
        Border location.

    include_index : bool, default True
        Include index labels.

    index_level : int, optional
        Maximum index level to affect.

    styles : dict, optional
        Border configuration.

    Returns
    -------
    pandas.io.formats.style.Styler

    Examples
    --------
    Add a separator below a total row.

    >>> add_row_line(
    ...     df,
    ...     rows="Total",
    ...     position="bottom"
    ... )

    Add a thick blue separator.

    >>> add_row_line(
    ...     df,
    ...     rows="Total",
    ...     position="top",
    ...     styles={
    ...         "width": "2px",
    ...         "color": "blue"
    ...     }
    ... )
    """

    styler = ensure_styler(obj)

    selectors = get_row_selectors(
        styler.data,
        rows,
        include_index=include_index,
        index_level=index_level,
    )

    css = build_border_css(
        position=position,
        styles=styles,
    )

    return apply_table_styles(
        styler,
        selectors,
        css,
    )


def add_column_line(
    obj,
    columns,
    position="right",
    include_header=True,
    header_level=None,
    styles=None,
):
    """
    Add a border to one or more columns.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler

    columns : hashable | iterable
        Column labels to modify.

    position : {"left", "right", "top", "bottom"}, default "right"
        Border position.

    include_header : bool, default True
        Include column headers.

    header_level : int, optional
        Maximum header level to affect.

    styles : dict, optional
        Border configuration.

    Returns
    -------
    pandas.io.formats.style.Styler

    Examples
    --------
    Separate performance metrics from risk metrics.

    >>> add_column_line(
    ...     df,
    ...     columns="YTD",
    ...     position="right"
    ... )

    Add a left border to multiple columns.

    >>> add_column_line(
    ...     df,
    ...     columns=["YTD", "1Y"],
    ...     position="left"
    ... )
    """
    
    styler = ensure_styler(obj)
    
    selectors = get_column_selectors(
        styler.data,
        columns,
        include_header=include_header,
        header_level=header_level,
    )

    css = build_border_css(
        position=position,
        styles=styles,
    )

    return apply_table_styles(
        styler,
        selectors,
        css,
    )


def text_color_range (
        value: float, 
        ranges: dict
):
    """
    Apply text color based on value ranges.

    Parameters
    ----------
    value : float
        Value to evaluate.

    ranges : dict
        Dictionary mapping intervals to colors.

        Example::

            {
                (-np.inf, 0): "red",
                (0, 0.10): "orange",
                (0.10, np.inf): "green",
            }

    Returns
    -------
    str
        CSS style string.

    Examples
    --------
    >>> text_color_range(
    ...     0.08,
    ...     {
    ...         (-np.inf, 0): "red",
    ...         (0, 0.05): "orange",
    ...         (0.05, np.inf): "green",
    ...     }
    ... )
    'color: green'
    """
    
    for (low, high), color in ranges.items():
        if low <= value < high:
            return f"color: {color}"

    return ""


def background_color_range (
        value: float, 
        ranges: dict
):
    """
    Apply background color based on value ranges.

    Parameters
    ----------
    value : float
        Value to evaluate.

    ranges : dict
        Dictionary mapping intervals to colors.

    Returns
    -------
    str
        CSS style string.

    Examples
    --------
    >>> background_color_range(
    ...     0.08,
    ...     {
    ...         (-np.inf, 0): "#F4CCCC",
    ...         (0, 0.05): "#FFF2CC",
    ...         (0.05, np.inf): "#D9EAD3",
    ...     }
    ... )
    'background-color: #D9EAD3'
    """
    
    for (low, high), color in ranges.items():
        if low <= value < high:
            return f"background-color: {color}"

    return ""