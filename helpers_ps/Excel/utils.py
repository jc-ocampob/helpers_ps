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


def to_excel_open(
    df: pd.DataFrame,
    book: Union[str, xw.Book],
    sheet: str = "Hoja1",
    cell: str = "A1",
    include_index: bool = True,
    include_header: bool = True,
    table_name: str = "Tabla1",
    to_table: bool = False,
    clear_range: bool = False,
    **kwargs,
) -> None:
    """
    Write a DataFrame to an open Excel workbook using xlwings.

    This function is useful when Excel is already open and the workbook is active
    or accessible through xlwings. Optionally, the written range can be converted
    into an Excel table.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to write into Excel.
    book : str or xlwings.Book
        Open workbook object or workbook name/path.
    sheet : str, default "Hoja1"
        Target sheet name.
    cell : str, default "A1"
        Top-left cell where the dataframe will be written.
    include_index : bool, default True
        Whether to include the dataframe index.
    include_header : bool, default True
        Whether to include column headers.
    table_name : str, default "Tabla1"
        Name of the Excel table to create or update.
    to_table : bool, default False
        Whether to create an Excel table from the written range.
    clear_range : bool, default False
        Whether to clear the current region starting from the target cell
        before writing the dataframe.
    **kwargs
        Additional keyword arguments passed to the xlwings table creation method.

    Returns
    -------
    None
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    if isinstance(book, xw.Book):
        wb = book
    elif isinstance(book, str):
        wb = xw.Book(book)
    else:
        raise TypeError("book must be an xlwings.Book object or a workbook name/path.")

    if sheet not in [s.name for s in wb.sheets]:
        ws = wb.sheets.add(sheet)
    else:
        ws = wb.sheets[sheet]

    start_range = ws.range(cell)

    if clear_range:
        start_range.current_region.clear_contents()

    start_range.options(
        index=include_index,
        header=include_header,
    ).value = df

    if to_table:
        n_rows = len(df) + (1 if include_header else 0)
        n_cols = len(df.columns) + (1 if include_index else 0)

        end_row = start_range.row + n_rows - 1
        end_col = start_range.column + n_cols - 1

        table_range = ws.range(
            (start_range.row, start_range.column),
            (end_row, end_col),
        )

        existing_tables = [tbl.name for tbl in ws.tables]

        if table_name in existing_tables:
            ws.tables[table_name].resize(table_range)
        else:
            ws.tables.add(
                source=table_range,
                name=table_name,
                **kwargs,
            )


def to_excel_closed(
    df: pd.DataFrame,
    path: Union[str, Path],
    sheet: str = "Hoja1",
    cell: str = "A1",
    include_index: bool = True,
    index_label: Optional[Union[str, list[str], tuple[str, ...]]] = None,
    table_name: str = "Tabla1",
    to_table: bool = False,
    autofit: bool = True,
    overwrite: bool = True,
    table_style: str = "TableStyleMedium2",
) -> None:
    """
    Write a DataFrame to a closed Excel workbook using openpyxl.

    If the workbook does not exist, it is created. If the target sheet does not
    exist, it is created. Optionally, the written range can be converted into
    an Excel table.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to write into Excel.
    path : str or pathlib.Path
        Path to the Excel workbook.
    sheet : str, default "Hoja1"
        Target sheet name.
    cell : str, default "A1"
        Top-left cell where the dataframe will be written.
    include_index : bool, default True
        Whether to include the dataframe index.
    index_label : str, list[str], tuple[str, ...], optional
        Label or labels for the index columns.
    table_name : str, default "Tabla1"
        Name of the Excel table to create.
    to_table : bool, default False
        Whether to create an Excel table from the written range.
    autofit : bool, default True
        Whether to adjust column widths based on cell contents.
    overwrite : bool, default True
        Whether to overwrite the target output range.
    table_style : str, default "TableStyleMedium2"
        Excel table style name.

    Returns
    -------
    None
    """
    path = Path(path)

    if path.exists():
        wb = load_workbook(path)
    else:
        wb = Workbook()

    if sheet in wb.sheetnames:
        ws = wb[sheet]
    else:
        ws = wb.create_sheet(sheet)

    data_to_write, header_labels = _prepare_dataframe_for_excel(
        df=df,
        include_index=include_index,
        index_label=index_label,
    )

    start_row, start_col = coordinate_to_tuple(cell)

    n_rows = len(data_to_write) + 1
    n_cols = len(header_labels)

    if overwrite:
        for row in ws.iter_rows(
            min_row=start_row,
            max_row=start_row + n_rows - 1,
            min_col=start_col,
            max_col=start_col + n_cols - 1,
        ):
            for excel_cell in row:
                excel_cell.value = None

    # Write headers
    for j, col_name in enumerate(header_labels):
        excel_cell = ws.cell(
            row=start_row,
            column=start_col + j,
            value=str(col_name),
        )
        excel_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Write data
    for i, row_vals in enumerate(data_to_write.itertuples(index=False, name=None), start=1):
        for j, value in enumerate(row_vals):
            ws.cell(
                row=start_row + i,
                column=start_col + j,
                value=_clean_excel_value(value),
            )

    # Create Excel table
    if to_table:
        end_row = start_row + n_rows - 1
        end_col = start_col + n_cols - 1

        start_ref = f"{get_column_letter(start_col)}{start_row}"
        end_ref = f"{get_column_letter(end_col)}{end_row}"
        table_ref = f"{start_ref}:{end_ref}"

        # Remove existing table with same name if needed
        if table_name in ws.tables:
            del ws.tables[table_name]

        table = Table(displayName=table_name, ref=table_ref)

        style = TableStyleInfo(
            name=table_style,
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )

        table.tableStyleInfo = style
        ws.add_table(table)

    # Autofit columns
    if autofit:
        for col_idx in range(start_col, start_col + n_cols):
            col_letter = get_column_letter(col_idx)
            max_length = 0

            for row_idx in range(start_row, start_row + n_rows):
                value = ws.cell(row=row_idx, column=col_idx).value
                if value is not None:
                    max_length = max(max_length, len(str(value)))

            ws.column_dimensions[col_letter].width = min(max_length + 2, 40)

    wb.save(path)


def to_excel_closed_styled(
    styled_df,
    output_path: Union[str, Path],
    sheet_name: str = "Sheet1",
    freeze_panes: Optional[str] = "B2",
    autofit: bool = True,
    index: bool = True,
) -> None:
    """
    Export a pandas Styler or DataFrame object to Excel preserving styles where possible.

    Parameters
    ----------
    styled_df : pandas.io.formats.style.Styler or pd.DataFrame
        Styled dataframe created with df.style, or a normal pandas DataFrame.
    output_path : str or pathlib.Path
        Output Excel file path.
    sheet_name : str, default "Sheet1"
        Name of the Excel sheet.
    freeze_panes : str, optional, default "B2"
        Cell reference used to freeze panes.
    autofit : bool, default True
        Whether to adjust column widths based on content.
    index : bool, default True
        Whether to export the dataframe index.

    Returns
    -------
    None
    """
    output_path = Path(output_path)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        styled_df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=index,
        )

        ws = writer.sheets[sheet_name]

        if freeze_panes:
            ws.freeze_panes = freeze_panes

        if autofit:
            for col in ws.columns:
                max_length = 0
                col_letter = col[0].column_letter

                for excel_cell in col:
                    if excel_cell.value is not None:
                        max_length = max(max_length, len(str(excel_cell.value)))

                ws.column_dimensions[col_letter].width = min(max_length + 2, 40)