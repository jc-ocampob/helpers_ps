from __future__ import annotations

from pandas.io.formats.style import Styler

from .constants import DEFAULT_HIGHLIGHT_STYLE
from .selectors import (
    get_cell_selector,
    get_column_selectors,
    get_row_selectors,
    get_row_line_selectors
)
from .utils import (
    apply_table_styles,
    build_border_css,
    ensure_styler,
    merge_styles,
    style_dict_to_css,
)


# ---------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------

from .models import (
    StylerLike,
    Label,
    CSSProperties,
    LabelCollection,
    BorderPosition,
    BorderLineStyle,
    OptionalCSSProperties,
    Labels,
    RowBorderPosition,
    ColumnBorderPosition
)



# ---------------------------------------------------------------------
# Cell styling
# ---------------------------------------------------------------------

def style_cell(
    obj: StylerLike,
    row: Label,
    column: Label,
    styles: CSSProperties,
) -> Styler:
    """
    Apply CSS properties to a single DataFrame cell.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object to modify.

    row : collections.abc.Hashable
        Label identifying the target row. For a MultiIndex row,
        provide the complete tuple label.

    column : collections.abc.Hashable
        Label identifying the target column. For a MultiIndex column,
        provide the complete tuple label.

    styles : Mapping[str, str]
        Mapping of CSS property names to CSS values.

    Returns
    -------
    pandas.io.formats.style.Styler
        Styler containing the applied cell styles.

    Examples
    --------
    Apply bold text to a cell.

    >>> styled = style_cell(
    ...     df,
    ...     row="Total",
    ...     column="YTD",
    ...     styles={"font-weight": "bold"},
    ... )

    Style a cell identified by MultiIndex labels.

    >>> styled = style_cell(
    ...     df,
    ...     row=("Fixed Income", "Government"),
    ...     column=("Performance", "YTD"),
    ...     styles={"background-color": "yellow"},
    ... )
    """
    styler = ensure_styler(obj)

    selector = get_cell_selector(
        styler.data,
        row,
        column,
    )

    css = style_dict_to_css(styles)

    return apply_table_styles(
        styler,
        [selector],
        css,
    )


def style_cells(
    obj: StylerLike,
    rows: LabelCollection,
    columns: LabelCollection,
    styles: CSSProperties,
) -> Styler:
    """
    Apply CSS properties to the intersection of multiple rows and columns.

    Every combination of the supplied row and column labels is styled.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object to modify.

    rows : Iterable[collections.abc.Hashable]
        Row labels identifying the target cells. MultiIndex labels must
        be provided as complete tuples contained inside an iterable.

    columns : Iterable[collections.abc.Hashable]
        Column labels identifying the target cells. MultiIndex labels
        must be provided as complete tuples contained inside an iterable.

    styles : Mapping[str, str]
        Mapping of CSS property names to CSS values.

    Returns
    -------
    pandas.io.formats.style.Styler
        Styler containing the applied cell styles.

    Examples
    --------
    Highlight a rectangular group of cells.

    >>> styled = style_cells(
    ...     df,
    ...     rows=["Total", "Benchmark"],
    ...     columns=["YTD", "1Y"],
    ...     styles={"background-color": "#FFF2CC"},
    ... )

    Style multiple cells in a DataFrame with MultiIndex labels.

    >>> styled = style_cells(
    ...     df,
    ...     rows=[
    ...         ("Fixed Income", "Total"),
    ...         ("Equity", "Total"),
    ...     ],
    ...     columns=[
    ...         ("Performance", "YTD"),
    ...         ("Performance", "1Y"),
    ...     ],
    ...     styles={"font-weight": "bold"},
    ... )
    """
    styler = ensure_styler(obj)
    css = style_dict_to_css(styles)

    selectors = [
        get_cell_selector(
            styler.data,
            row,
            column,
        )
        for row in rows
        for column in columns
    ]

    return apply_table_styles(
        styler,
        selectors,
        css,
    )


# ---------------------------------------------------------------------
# Cell borders
# ---------------------------------------------------------------------

def border_cell(
    obj: StylerLike,
    row: Label,
    column: Label,
    position: BorderPosition = "top",
    width: str = "1px",
    color: str = "black",
    line_style: BorderLineStyle = "solid",
) -> Styler:
    """
    Add a border to one side of a single DataFrame cell.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object to modify.

    row : collections.abc.Hashable
        Label identifying the target row.

    column : collections.abc.Hashable
        Label identifying the target column.

    position : {"top", "bottom", "left", "right"}, default "top"
        Side of the cell on which the border is added.

    width : str, default "1px"
        CSS border width, such as ``"1px"``, ``"2px"``, or ``"0.1rem"``.

    color : str, default "black"
        Valid CSS color name, hexadecimal value, RGB value, or other
        supported CSS color expression.

    line_style : BorderLineStyle, default "solid"
        CSS border line style.

    Returns
    -------
    pandas.io.formats.style.Styler
        Styler containing the applied cell border.

    Examples
    --------
    Add a top border.

    >>> styled = border_cell(
    ...     df,
    ...     row="Total",
    ...     column="YTD",
    ...     position="top",
    ... )

    Add a thick red bottom border.

    >>> styled = border_cell(
    ...     df,
    ...     row="Total",
    ...     column="YTD",
    ...     position="bottom",
    ...     width="3px",
    ...     color="red",
    ... )
    """
    return style_cell(
        obj=obj,
        row=row,
        column=column,
        styles={
            f"border-{position}": f"{width} {line_style} {color}",
        },
    )


def border_cells(
    obj: StylerLike,
    rows: LabelCollection,
    columns: LabelCollection,
    position: BorderPosition = "top",
    width: str = "1px",
    color: str = "black",
    line_style: BorderLineStyle = "solid",
) -> Styler:
    """
    Add a border to one side of multiple DataFrame cells.

    A border is applied to every intersection of the supplied row and
    column labels.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object to modify.

    rows : Iterable[collections.abc.Hashable]
        Row labels identifying the target cells.

    columns : Iterable[collections.abc.Hashable]
        Column labels identifying the target cells.

    position : {"top", "bottom", "left", "right"}, default "top"
        Side of each cell on which the border is added.

    width : str, default "1px"
        CSS border width.

    color : str, default "black"
        CSS border color.

    line_style : BorderLineStyle, default "solid"
        CSS border line style.

    Returns
    -------
    pandas.io.formats.style.Styler
        Styler containing the applied cell borders.

    Examples
    --------
    Add a bottom border to summary cells.

    >>> styled = border_cells(
    ...     df,
    ...     rows=["Total"],
    ...     columns=["YTD", "1Y", "3Y"],
    ...     position="bottom",
    ... )

    Add borders to cells identified by MultiIndex labels.

    >>> styled = border_cells(
    ...     df,
    ...     rows=[("Fixed Income", "Total")],
    ...     columns=[
    ...         ("Performance", "YTD"),
    ...         ("Performance", "1Y"),
    ...     ],
    ...     position="bottom",
    ...     width="2px",
    ... )
    """
    return style_cells(
        obj=obj,
        rows=rows,
        columns=columns,
        styles={
            f"border-{position}": f"{width} {line_style} {color}",
        },
    )


# ---------------------------------------------------------------------
# Row and column highlighting
# ---------------------------------------------------------------------

def highlight_rows(
    obj: StylerLike,
    rows: Labels,
    styles: OptionalCSSProperties = None,
    include_index: bool = True,
    index_level: int | None = None,
) -> Styler:
    """
    Highlight one or more DataFrame rows.

    The supplied CSS properties are merged with
    ``DEFAULT_HIGHLIGHT_STYLE``. User-supplied properties override
    matching default properties.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object to modify.

    rows : Hashable | Iterable[Hashable]
        Single row label or iterable of row labels. For a MultiIndex row,
        a tuple is interpreted as one complete row label.

    styles : Mapping[str, str] | None, default None
        CSS properties that override or extend the default highlight
        style.

    include_index : bool, default True
        Whether the corresponding row index labels are also highlighted.

    index_level : int | None, default None
        Index level through which index styling is applied. The precise
        behavior depends on ``get_row_selectors``.

    Returns
    -------
    pandas.io.formats.style.Styler
        Styler containing the highlighted rows.

    Examples
    --------
    Highlight a total row using the default style.

    >>> styled = highlight_rows(
    ...     df,
    ...     rows="Total",
    ... )

    Highlight multiple rows with a custom background.

    >>> styled = highlight_rows(
    ...     df,
    ...     rows=["Benchmark", "Total"],
    ...     styles={"background-color": "#D9EAD3"},
    ... )

    Highlight one MultiIndex row.

    >>> styled = highlight_rows(
    ...     df,
    ...     rows=("Fixed Income", "Total"),
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
    obj: StylerLike,
    columns: Labels,
    styles: OptionalCSSProperties = None,
    include_header: bool = True,
    header_level: int | None = None,
) -> Styler:
    """
    Highlight one or more DataFrame columns.

    The supplied CSS properties are merged with
    ``DEFAULT_HIGHLIGHT_STYLE``. User-supplied properties override
    matching default properties.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object to modify.

    columns : Hashable | Iterable[Hashable]
        Single column label or iterable of column labels. For a
        MultiIndex column, a tuple is interpreted as one complete label.

    styles : Mapping[str, str] | None, default None
        CSS properties that override or extend the default highlight
        style.

    include_header : bool, default True
        Whether the corresponding column headers are also highlighted.

    header_level : int | None, default None
        Header level through which header styling is applied. The precise
        behavior depends on ``get_column_selectors``.

    Returns
    -------
    pandas.io.formats.style.Styler
        Styler containing the highlighted columns.

    Examples
    --------
    Highlight multiple columns.

    >>> styled = highlight_columns(
    ...     df,
    ...     columns=["YTD", "1Y"],
    ... )

    Highlight a MultiIndex column.

    >>> styled = highlight_columns(
    ...     df,
    ...     columns=("Performance", "YTD"),
    ...     styles={"background-color": "#FFF2CC"},
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


# ---------------------------------------------------------------------
# Row and column borders
# ---------------------------------------------------------------------

def border_rows(
    obj: StylerLike,
    rows: Labels,
    position: RowBorderPosition = "bottom",
    styles: OptionalCSSProperties = None,
) -> Styler:
    """
    Add a horizontal border across one or more DataFrame rows.

    The border is applied to the complete HTML table row. This allows
    the separator to extend across sparse MultiIndex labels rendered
    with ``rowspan``.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object to modify.

    rows : Hashable | Iterable[Hashable]
        Single row label or iterable of row labels.

        For a MultiIndex, a tuple is interpreted as one complete row
        label. To select multiple MultiIndex rows, provide an iterable
        of tuples.

    position : {"top", "bottom"}, default "bottom"
        Side of each selected row on which the horizontal border is
        added.

    styles : Mapping[str, str] | None, default None
        Optional border configuration passed to ``build_border_css``.

        Common properties include:

        - ``"width"``
        - ``"line_style"``
        - ``"color"``

    Returns
    -------
    pandas.io.formats.style.Styler
        Styler containing the horizontal row borders.

    Examples
    --------
    Add a separator below one standard row.

    >>> styled = border_rows(
    ...     obj=df,
    ...     rows="Total",
    ... )

    Add separators below multiple MultiIndex rows.

    >>> styled = border_rows(
    ...     obj=df,
    ...     rows=[
    ...         ("Delta Yield", "MTD", "A"),
    ...         ("Delta Yield", "YTD", "A"),
    ...     ],
    ...     styles={
    ...         "width": "1px",
    ...         "color": "red",
    ...     },
    ... )
    """
    styler = ensure_styler(obj)

    selectors = get_row_line_selectors(
        df=styler.data,
        rows=rows,
    )

    css = build_border_css(
        position=position,
        styles=styles,
    )

    return apply_table_styles(
        styler=styler,
        selectors=selectors,
        css=css,
    )


def border_columns(
    obj: StylerLike,
    columns: Labels,
    position: ColumnBorderPosition = "right",
    include_header: bool = True,
    header_level: int | None = None,
    styles: OptionalCSSProperties = None,
) -> Styler:
    """
    Add a vertical border to one or more DataFrame columns.

    Parameters
    ----------
    obj : pandas.DataFrame | pandas.io.formats.style.Styler
        DataFrame or existing Styler object to modify.

    columns : Hashable | Iterable[Hashable]
        Single column label or iterable of column labels.

    position : {"left", "right"}, default "right"
        Side of each selected column on which the border is added.

    include_header : bool, default True
        Whether the border is extended through the column headers.

    header_level : int | None, default None
        Header level through which border styling is applied. The precise
        behavior depends on ``get_column_selectors``.

    styles : Mapping[str, str] | None, default None
        Border configuration passed to ``build_border_css``.

    Returns
    -------
    pandas.io.formats.style.Styler
        Styler containing the column borders.

    Examples
    --------
    Add a separator after the YTD column.

    >>> styled = border_columns(
    ...     df,
    ...     columns="YTD",
    ...     position="right",
    ... )

    Add a left border to multiple columns.

    >>> styled = border_columns(
    ...     df,
    ...     columns=["YTD", "1Y"],
    ...     position="left",
    ...     styles={
    ...         "width": "2px",
    ...         "color": "#808080",
    ...     },
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


