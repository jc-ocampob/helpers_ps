from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, Any

import xlwings as xw
import pandas as pd

from openpyxl import load_workbook, Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils.cell import coordinate_to_tuple
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment


def _clean_excel_value(value: Any) -> Any:
    """
    Convert pandas missing values into Excel-compatible empty values.

    Parameters
    ----------
    value : Any
        Value to be written into Excel.

    Returns
    -------
    Any
        Cleaned value compatible with Excel.
    """
    if pd.isna(value):
        return None
    return value


def _prepare_dataframe_for_excel(
    df: pd.DataFrame,
    include_index: bool = True,
    index_label: Optional[Union[str, list[str], tuple[str, ...]]] = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Prepare a dataframe before writing it to Excel.

    If include_index is True, the index is converted into one or multiple columns.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to prepare.
    include_index : bool, default True
        Whether to include the dataframe index as Excel columns.
    index_label : str, list[str], tuple[str, ...], optional
        Label or labels to use for the index columns.

    Returns
    -------
    tuple[pd.DataFrame, list[str]]
        Prepared dataframe and list of header labels.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    if include_index:
        if isinstance(df.index, pd.MultiIndex):
            n_levels = df.index.nlevels

            if index_label is None:
                index_labels = [
                    name if name is not None else ""
                    for name in df.index.names
                ]
            else:
                if not isinstance(index_label, (list, tuple)) or len(index_label) != n_levels:
                    raise ValueError(
                        f"For a MultiIndex, index_label must be a list or tuple "
                        f"with length {n_levels}."
                    )
                index_labels = list(index_label)

            idx_df = df.index.to_frame(index=False)
            data_to_write = pd.concat(
                [idx_df.reset_index(drop=True), df.reset_index(drop=True)],
                axis=1,
            )
            header_labels = index_labels + list(df.columns)

        else:
            idx_name = df.index.name if df.index.name is not None else ""

            if index_label is not None:
                if not isinstance(index_label, str):
                    raise ValueError("For a simple index, index_label must be a string.")
                idx_name = index_label

            idx_series = df.index.to_series().reset_index(drop=True).to_frame(name=idx_name)
            data_to_write = pd.concat(
                [idx_series, df.reset_index(drop=True)],
                axis=1,
            )
            header_labels = [idx_name] + list(df.columns)

    else:
        data_to_write = df.reset_index(drop=True)
        header_labels = list(df.columns)

    header_labels = [str(col) for col in header_labels]

    return data_to_write, header_labels

