from __future__ import annotations

from collections.abc import Hashable, Iterable
from typing import TypeAlias

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------

Label: TypeAlias = Hashable
Targets: TypeAlias = Hashable | Iterable[Hashable]


# ---------------------------------------------------------------------
# Target normalization
# ---------------------------------------------------------------------

def normalize_targets(
    targets: Targets,
    axis_index: pd.Index,
) -> list:
    """
    Normalize one or more axis targets into a list of labels.

    The function distinguishes between a tuple representing one complete
    MultiIndex label and an iterable containing multiple labels.

    Parameters
    ----------
    targets : Hashable | Iterable[Hashable]
        Single axis label or iterable of axis labels.

        For a MultiIndex, a tuple is interpreted as one complete label.
        To provide multiple MultiIndex labels, use a list of tuples.

    axis_index : pandas.Index
        DataFrame index or columns against which the targets are
        interpreted.

    Returns
    -------
    list[Hashable]
        Normalized list of axis labels.

    Examples
    --------
    Normalize one standard index label.

    >>> normalize_targets(
    ...     targets="Total",
    ...     axis_index=df.index,
    ... )
    ['Total']

    Normalize multiple standard index labels.

    >>> normalize_targets(
    ...     targets=["Benchmark", "Total"],
    ...     axis_index=df.index,
    ... )
    ['Benchmark', 'Total']

    Normalize one MultiIndex label.

    >>> normalize_targets(
    ...     targets=("Fixed Income", "Total"),
    ...     axis_index=df.index,
    ... )
    [('Fixed Income', 'Total')]
    """
    if isinstance(axis_index, pd.MultiIndex):
        if isinstance(targets, tuple):
            return [targets]

        if isinstance(
            targets,
            (
                list,
                set,
                pd.Index,
                np.ndarray,
            ),
        ):
            return list(targets)

        return [targets]

    if isinstance(targets, (str, bytes)):
        return [targets]

    if isinstance(
        targets,
        (
            list,
            tuple,
            set,
            pd.Index,
            np.ndarray,
        ),
    ):
        return list(targets)

    return [targets]


# ---------------------------------------------------------------------
# Axis positions
# ---------------------------------------------------------------------

def get_axis_positions(
    axis_index: pd.Index,
    targets: Targets,
) -> list:
    """
    Return the integer positions of one or more axis labels.

    All occurrences of a label are returned. Therefore, duplicated index
    or column labels may produce more than one position.

    Parameters
    ----------
    axis_index : pandas.Index
        DataFrame index or columns containing the target labels.

    targets : Hashable | Iterable[Hashable]
        Single label or iterable of labels whose positions are required.

    Returns
    -------
    list[int]
        Integer positions of the matching labels. An empty list is
        returned when no labels match.

    Examples
    --------
    Find the position of one row.

    >>> get_axis_positions(
    ...     axis_index=df.index,
    ...     targets="Total",
    ... )
    [4]

    Find the positions of multiple columns.

    >>> get_axis_positions(
    ...     axis_index=df.columns,
    ...     targets=["YTD", "1Y"],
    ... )
    [1, 2]
    """
    normalized_targets = normalize_targets(
        targets=targets,
        axis_index=axis_index,
    )

    return [
        position
        for position, label in enumerate(axis_index)
        if label in normalized_targets
    ]


# ---------------------------------------------------------------------
# Level resolution
# ---------------------------------------------------------------------

def _resolve_max_level(
    number_of_levels: int,
    requested_level: int | None,
    parameter_name: str,
) -> int:
    """
    Resolve and validate the deepest axis level to include.

    Parameters
    ----------
    number_of_levels : int
        Total number of levels in the axis.

    requested_level : int | None
        Deepest requested level. If ``None``, the final available level
        is returned. Values above the available number of levels are
        clamped to the final level.

    parameter_name : str
        Parameter name included in validation error messages.

    Returns
    -------
    int
        Zero-based deepest level to include.

    Raises
    ------
    TypeError
        If ``requested_level`` is not an integer or ``None``.

    ValueError
        If ``requested_level`` is negative.
    """
    if requested_level is None:
        return number_of_levels - 1

    if not isinstance(requested_level, int):
        raise TypeError(
            f"{parameter_name} must be an integer or None."
        )

    if requested_level < 0:
        raise ValueError(
            f"{parameter_name} cannot be negative."
        )

    return min(
        requested_level,
        number_of_levels - 1,
    )


# ---------------------------------------------------------------------
# Sparse MultiIndex ownership
# ---------------------------------------------------------------------

def _get_row_heading_owner(
    index: pd.Index,
    row_position: int,
    level: int,
) -> int:
    """
    Return the HTML owner row of a row-index cell.

    Pandas may sparsify repeated MultiIndex labels by rendering one
    ``th`` element with a ``rowspan`` value. In that case, the visible
    index cell beside a target row may belong to an earlier HTML row.

    This function finds the first row of the contiguous MultiIndex group
    containing the target row at the requested level.

    Parameters
    ----------
    index : pandas.Index
        DataFrame row index.

    row_position : int
        Integer position of the target row.

    level : int
        Zero-based index level.

    Returns
    -------
    int
        Row position containing the actual HTML ``th`` element for the
        requested index cell.
    """
    if not isinstance(index, pd.MultiIndex):
        return row_position

    owner_position = row_position

    current_prefix = tuple(
        index[row_position][: level + 1]
    )

    while owner_position > 0:
        previous_prefix = tuple(
            index[owner_position - 1][: level + 1]
        )

        if previous_prefix != current_prefix:
            break

        owner_position -= 1

    return owner_position


def _get_column_heading_owner(
    columns: pd.Index,
    column_position: int,
    level: int,
) -> int:
    """
    Return the HTML owner column of a column-header cell.

    Pandas may sparsify repeated MultiIndex column labels by rendering
    one ``th`` element with a ``colspan`` value. The visible header cell
    above a target column may therefore belong to an earlier physical
    column.

    This function finds the first column of the contiguous MultiIndex
    group containing the target column at the requested level.

    Parameters
    ----------
    columns : pandas.Index
        DataFrame columns.

    column_position : int
        Integer position of the target column.

    level : int
        Zero-based column-header level.

    Returns
    -------
    int
        Column position containing the actual HTML ``th`` element for
        the requested header cell.
    """
    if not isinstance(columns, pd.MultiIndex):
        return column_position

    owner_position = column_position

    current_prefix = tuple(
        columns[column_position][: level + 1]
    )

    while owner_position > 0:
        previous_prefix = tuple(
            columns[owner_position - 1][: level + 1]
        )

        if previous_prefix != current_prefix:
            break

        owner_position -= 1

    return owner_position


# ---------------------------------------------------------------------
# Row selectors
# ---------------------------------------------------------------------

def get_row_selectors(
    df: pd.DataFrame,
    rows: Targets,
    include_index: bool = True,
    index_level: int | None = None,
) -> list:
    """
    Build CSS selectors for one or more DataFrame rows.

    Data-cell selectors are generated for every selected row. When
    ``include_index`` is enabled, selectors for the corresponding
    row-index cells are also included.

    For sparse MultiIndex rendering, the function identifies the HTML
    row that owns each index cell. This allows styles such as horizontal
    borders to extend through merged outer index levels.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame whose rows are used to generate the selectors.

    rows : Hashable | Iterable[Hashable]
        Single row label or iterable of row labels.

        For a MultiIndex, a tuple is interpreted as one complete row
        label. To select multiple MultiIndex rows, use a list of tuples.

    include_index : bool, default True
        Whether row-index cells should be included.

    index_level : int | None, default None
        Deepest index level to include. The value is inclusive.

        If ``None``, every available index level is included. If the
        value exceeds the available levels, it is clamped to the final
        level.

    Returns
    -------
    list[str]
        CSS selectors for the selected rows and associated index cells.

    Raises
    ------
    TypeError
        If ``index_level`` is not an integer or ``None``.

    ValueError
        If ``index_level`` is negative.

    Examples
    --------
    Select a standard row and its index label.

    >>> selectors = get_row_selectors(
    ...     df=df,
    ...     rows="Total",
    ... )

    Select a three-level MultiIndex row and include every index level.

    >>> selectors = get_row_selectors(
    ...     df=df,
    ...     rows=("Asset Class", "Sector", "Total"),
    ...     include_index=True,
    ...     index_level=None,
    ... )

    Select multiple rows without including their index labels.

    >>> selectors = get_row_selectors(
    ...     df=df,
    ...     rows=["Benchmark", "Total"],
    ...     include_index=False,
    ... )
    """
    row_positions = get_axis_positions(
        axis_index=df.index,
        targets=rows,
    )

    selectors: list[str] = []

    max_level = _resolve_max_level(
        number_of_levels=df.index.nlevels,
        requested_level=index_level,
        parameter_name="index_level",
    )

    for row_position in row_positions:
        selectors.append(
            f"td.row{row_position}"
        )

        if not include_index:
            continue

        for level in range(max_level + 1):
            owner_position = _get_row_heading_owner(
                index=df.index,
                row_position=row_position,
                level=level,
            )

            selectors.append(
                f"th.row_heading.level{level}"
                f".row{owner_position}"
            )

    return list(dict.fromkeys(selectors))


# ---------------------------------------------------------------------
# Column selectors
# ---------------------------------------------------------------------

def get_column_selectors(
    df: pd.DataFrame,
    columns: Targets,
    include_header: bool = True,
    header_level: int | None = None,
) -> list:
    """
    Build CSS selectors for one or more DataFrame columns.

    Data-cell selectors are generated for every selected column. When
    ``include_header`` is enabled, selectors for the corresponding
    column-header cells are also included.

    For sparse MultiIndex rendering, the function identifies the HTML
    column that owns each header cell.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame whose columns are used to generate the selectors.

    columns : Hashable | Iterable[Hashable]
        Single column label or iterable of column labels.

        For MultiIndex columns, a tuple is interpreted as one complete
        column label. To select multiple MultiIndex columns, use a list
        of tuples.

    include_header : bool, default True
        Whether column-header cells should be included.

    header_level : int | None, default None
        Deepest column-header level to include. The value is inclusive.

        If ``None``, every available header level is included. If the
        value exceeds the available levels, it is clamped to the final
        level.

    Returns
    -------
    list[str]
        CSS selectors for the selected columns and associated headers.

    Raises
    ------
    TypeError
        If ``header_level`` is not an integer or ``None``.

    ValueError
        If ``header_level`` is negative.

    Examples
    --------
    Select one standard column and its header.

    >>> selectors = get_column_selectors(
    ...     df=df,
    ...     columns="YTD",
    ... )

    Select one MultiIndex column and all its header levels.

    >>> selectors = get_column_selectors(
    ...     df=df,
    ...     columns=("Performance", "YTD"),
    ...     include_header=True,
    ...     header_level=None,
    ... )
    """
    column_positions = get_axis_positions(
        axis_index=df.columns,
        targets=columns,
    )

    selectors: list[str] = []

    max_level = _resolve_max_level(
        number_of_levels=df.columns.nlevels,
        requested_level=header_level,
        parameter_name="header_level",
    )

    for column_position in column_positions:
        selectors.append(
            f"td.col{column_position}"
        )

        if not include_header:
            continue

        for level in range(max_level + 1):
            owner_position = _get_column_heading_owner(
                columns=df.columns,
                column_position=column_position,
                level=level,
            )

            selectors.append(
                f"th.col_heading.level{level}"
                f".col{owner_position}"
            )

    return list(dict.fromkeys(selectors))


# ---------------------------------------------------------------------
# Cell selector
# ---------------------------------------------------------------------

def get_cell_selector(
    df: pd.DataFrame,
    row: Label,
    column: Label,
) -> str:
    """
    Build the CSS selector for one uniquely identified DataFrame cell.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing the target cell.

    row : Hashable
        Target row label. For a MultiIndex row, provide the complete
        tuple label.

    column : Hashable
        Target column label. For a MultiIndex column, provide the
        complete tuple label.

    Returns
    -------
    str
        CSS selector targeting the identified data cell.

    Raises
    ------
    ValueError
        If the row or column label does not resolve to exactly one
        position.

    Examples
    --------
    Select one standard DataFrame cell.

    >>> selector = get_cell_selector(
    ...     df=df,
    ...     row="Total",
    ...     column="YTD",
    ... )
    >>> selector
    'td.row4.col2'

    Select one cell with MultiIndex labels.

    >>> selector = get_cell_selector(
    ...     df=df,
    ...     row=("Fixed Income", "Total"),
    ...     column=("Performance", "YTD"),
    ... )
    """
    row_positions = get_axis_positions(
        axis_index=df.index,
        targets=row,
    )

    column_positions = get_axis_positions(
        axis_index=df.columns,
        targets=column,
    )

    if len(row_positions) != 1:
        raise ValueError(
            f"Row {row!r} must identify exactly one row. "
            f"Found {len(row_positions)} matches."
        )

    if len(column_positions) != 1:
        raise ValueError(
            f"Column {column!r} must identify exactly one column. "
            f"Found {len(column_positions)} matches."
        )

    row_position = row_positions[0]
    column_position = column_positions[0]

    return (
        f"td.row{row_position}"
        f".col{column_position}"
    )