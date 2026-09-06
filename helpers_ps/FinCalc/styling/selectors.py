from __future__ import annotations

from collections.abc import Hashable
from collections.abc import Sequence

import numpy as np
import pandas as pd


def normalize_targets(
    targets,
    axis_index,
):
    """
    Normalize targets.
    """

    if isinstance(
        axis_index,
        pd.MultiIndex,
    ):
        if isinstance(targets, tuple):
            return [targets]

        if isinstance(targets, list):
            return targets

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


def get_axis_positions(
    axis_index,
    targets,
):
    """
    Return positions.
    """

    normalized_targets = normalize_targets(
        targets,
        axis_index,
    )

    positions = []

    for position, label in enumerate(
        axis_index
    ):
        if label in normalized_targets:
            positions.append(position)

    return positions


def get_row_selectors(
    df: pd.DataFrame,
    rows,
    include_index: bool = True,
    index_level: int | None = None,
):
    """
    Return css selectors
    for rows.
    """

    row_positions = get_axis_positions(
        df.index,
        rows,
    )

    selectors = []

    for row_position in row_positions:

        selectors.append(
            f"td.row{row_position}"
        )

        if include_index:

            nlevels = (
                df.index.nlevels
            )

            if index_level is None:
                max_level = (
                    nlevels - 1
                )
            else:
                max_level = min(
                    index_level,
                    nlevels - 1,
                )

            for level in range(
                max_level + 1
            ):
                selectors.append(
                    f"th.row_heading.level{level}.row{row_position}"
                )

    return selectors


def get_column_selectors(
    df: pd.DataFrame,
    columns,
    include_header: bool = True,
    header_level: int | None = None,
):
    """
    Return css selectors
    for columns.
    """

    column_positions = (
        get_axis_positions(
            df.columns,
            columns,
        )
    )

    selectors = []

    for column_position in column_positions:

        selectors.append(
            f"td.col{column_position}"
        )

        if include_header:

            nlevels = (
                df.columns.nlevels
            )

            if header_level is None:
                max_level = (
                    nlevels - 1
                )
            else:
                max_level = min(
                    header_level,
                    nlevels - 1,
                )

            for level in range(
                max_level + 1
            ):
                selectors.append(
                    f"th.col_heading.level{level}.col{column_position}"
                )

    return selectors


def get_cell_selector(
    df: pd.DataFrame,
    row,
    column,
):
    """
    Get selector for a
    single cell.
    """

    row_positions = (
        get_axis_positions(
            df.index,
            row,
        )
    )

    column_positions = (
        get_axis_positions(
            df.columns,
            column,
        )
    )

    if len(
        row_positions
    ) != 1:
        raise ValueError(
            f"Row '{row}' "
            "not unique."
        )

    if len(
        column_positions
    ) != 1:
        raise ValueError(
            f"Column '{column}' "
            "not unique."
        )

    row_position = (
        row_positions[0]
    )

    column_position = (
        column_positions[0]
    )

    return (
        f"td.row{row_position}"
        f".col{column_position}"
    )