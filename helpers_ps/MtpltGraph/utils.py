from __future__ import annotations

import pandas as pd


def validate_dataframe(df: pd.DataFrame, allow_empty: bool = False) -> None:
    """
    Validate that an object is a pandas DataFrame and optionally validate that it is not empty.

    Parameters
    ----------
    df:
        Object expected to be a pandas DataFrame.
    allow_empty:
        If False, an empty DataFrame raises a ValueError.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")
    if not allow_empty and df.empty:
        raise ValueError("The dataframe is empty.")


def as_list(value):
    """
    Convert a scalar value into a list while preserving existing lists.

    Parameters
    ----------
    value:
        Scalar, list, tuple, set, or None value to normalize.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]
