# Excel

The `Excel` module writes DataFrames to Excel workbooks in three situations:

| Function | Workbook state | Engine | Best for |
|---|---|---|---|
| `to_excel_open` | **Open** in Excel (live) | `xlwings` | Update a workbook you are looking at; models with formulas, charts and links that read the data. |
| `to_excel_closed` | **Closed** (a file on disk) | `openpyxl` | Automated jobs, servers, no Excel installed. Creates or updates a sheet of the file. |
| `to_excel_closed_styled` | Closed, new file | `pandas` + `openpyxl` | Export a **styled** table (`Styler`, see [DfStyling](../DfStyling/getting_started.md)). |

```python
import helpers_ps as hp

hp.Excel.to_excel_closed(df, "report.xlsx", sheet="Data", cell="B2", to_table=True)
```

!!! info "Requirements"
    `to_excel_open` needs **Excel installed** (Windows or macOS) and the `xlwings` package. The other two functions only need `openpyxl`. Because the package imports `xlwings` when the `Excel` module loads, `xlwings` must be installed in every environment (it is part of the package dependencies).

```python
import numpy as np
import pandas as pd
import helpers_ps as hp

dates = pd.bdate_range("2024-01-02", periods=5)
df = pd.DataFrame(
    {"SPX": [4700.1, 4710.5, np.nan, 4725.0, 4731.2], "NDX": [16500.0, 16520.3, 16490.8, 16555.5, 16570.0]},
    index=pd.Index(dates, name="Date"),
)
```

---

## `to_excel_closed`

`to_excel_closed(df, path, sheet="Hoja1", cell="A1", include_index=True, index_label=None, table_name="Tabla1", to_table=False, autofit=True, overwrite=True, table_style="TableStyleMedium2")`

Writes the DataFrame into a workbook **file**. If the file does not exist it is created; if the sheet does not exist it is created; other sheets of an existing workbook are kept.

| Parameter | Default | Description |
|---|---|---|
| `df` | | DataFrame to write. |
| `path` | | Workbook path (`str` or `Path`). |
| `sheet` | `"Hoja1"` | Target sheet name. |
| `cell` | `"A1"` | Top-left cell of the output (header row). |
| `include_index` | `True` | Write the index as the first column(s). A **MultiIndex** becomes several columns. |
| `index_label` | `None` | Header(s) for the index column(s): a string, or a list / tuple with one label per level for a MultiIndex. |
| `table_name` | `"Tabla1"` | Name of the Excel table if `to_table=True`. |
| `to_table` | `False` | Convert the written range to a formatted **Excel table**. An existing table with the same name is replaced. |
| `table_style` | `"TableStyleMedium2"` | Style of the Excel table. |
| `autofit` | `True` | Adjust column widths to the content (capped at 40 characters). |
| `overwrite` | `True` | Clear the target range before writing. |

```python
hp.Excel.to_excel_closed(df, "prices.xlsx", sheet="Prices", cell="B2", to_table=True, table_name="tbl_prices")

from openpyxl import load_workbook

ws = load_workbook("prices.xlsx")["Prices"]
[[c.value for c in row] for row in ws["B2:D4"]]
```
**Output**

```text
[['Date', 'SPX', 'NDX'], [datetime.datetime(2024, 1, 2, 0, 0), 4700.1, 16500], [datetime.datetime(2024, 1, 3, 0, 0), 4710.5, 16520.3]]
```

Details to know:

- The **header row** is written as text and centered; **missing values** (`NaN`, `NaT`, `None`) are written as **empty cells**.
- Cells are written as **values** (no formulas). Dates are written as Excel dates.
- Calling it again with the same `sheet` and `cell` **refreshes** the data; with `overwrite=False` existing cell values outside the new data are not cleared.
- The workbook must **not be open** in Excel (Windows locks the file and `PermissionError` is raised).

### Several DataFrames in one workbook

Call it once per DataFrame, changing `sheet` and / or `cell`:

```python
returns = df.pct_change().dropna()

hp.Excel.to_excel_closed(df, "report.xlsx", sheet="Prices")
hp.Excel.to_excel_closed(returns, "report.xlsx", sheet="Returns", index_label="Date")
hp.Excel.to_excel_closed(df.describe(), "report.xlsx", sheet="Summary", cell="A1")

load_workbook("report.xlsx").sheetnames
```
**Output**

```text
['Sheet', 'Prices', 'Returns', 'Summary']
```

!!! note "The default sheet name"
    The default `sheet="Hoja1"` (Spanish for *Sheet1*) and `table_name="Tabla1"` are only defaults: pass your own names. A freshly created workbook also contains its initial empty sheet (`Sheet`).

---

## `to_excel_closed_styled`

`to_excel_closed_styled(styled_df, output_path, sheet_name="Sheet1", freeze_panes="B2", autofit=True, index=True)`

Exports a **`Styler`** (or a plain DataFrame) to a **new** workbook, keeping the styles pandas can translate to Excel (colors, bold / italic, borders, alignment). Unlike `to_excel_closed` it **always creates a new file** (an existing file with the same name is overwritten).

| Parameter | Default | Description |
|---|---|---|
| `styled_df` | | `Styler` (from `df.style` or [`hp.DfStyling`](../DfStyling/functional.md)) or DataFrame. |
| `output_path` | | Output `.xlsx` path. |
| `sheet_name` | `"Sheet1"` | Sheet name. |
| `freeze_panes` | `"B2"` | Cell where panes are frozen (header row and index column stay visible). `None` disables it. |
| `autofit` | `True` | Adjust column widths (capped at 40). |
| `index` | `True` | Export the index. |

```python
import os

styled = hp.DfStyling.style_table(
    df.round(1),
    header_styles={"color": "white", "background-color": "#12275A", "font-weight": "bold"},
)
styled = hp.DfStyling.highlight_rows(styled, df.index[-1], include_index=False)

hp.Excel.to_excel_closed_styled(styled, "styled.xlsx", sheet_name="Prices", freeze_panes="B2")
os.path.exists("styled.xlsx")
```
**Output**

```text
True
```

!!! warning "What survives the export"
    Excel understands a **subset of CSS**: background and text colors, font weight and style, borders and alignment are translated; layout properties (padding, `font-family` lists, etc.) are not. Check the result in Excel and keep the sheet-based image output ([`TableSheet`](../DfStyling/getting_started.md)) for pixel-exact looks.

---

## `to_excel_open`

`to_excel_open(df, book, sheet="Hoja1", cell="A1", include_index=True, include_header=True, table_name="Tabla1", to_table=False, clear_range=False, **kwargs)`

Writes the DataFrame into a workbook that is **open in Excel**, through `xlwings`. Nothing is saved to disk; the user (or your code) saves the workbook.

| Parameter | Default | Description |
|---|---|---|
| `df` | | DataFrame to write. |
| `book` | | An `xlwings.Book` object, **or** a workbook name / path (`str`) that `xlwings` can find. Any other type raises `TypeError`. |
| `sheet` | `"Hoja1"` | Sheet to write to. It is **created** if it does not exist. |
| `cell` | `"A1"` | Top-left cell. |
| `include_index`, `include_header` | `True`, `True` | Write the index / the column names. |
| `to_table` | `False` | Convert the range to an Excel table (`table_name`). If the table already exists, it is **resized** to the new range. |
| `table_name` | `"Tabla1"` | Name of the table. |
| `clear_range` | `False` | Clear the **current region** around `cell` before writing (use it when the new data may be smaller than the previous one). |
| `**kwargs` | | Extra arguments for `ws.tables.add(...)` of xlwings (for example `table_style_name="TableStyleMedium2"`). |

```python
import xlwings as xw

wb = xw.Book("model.xlsx")                       # or xw.books.active

hp.Excel.to_excel_open(
    df,
    book=wb,
    sheet="Data",
    cell="A1",
    clear_range=True,
    to_table=True,
    table_name="tbl_prices",
)
```

Using the workbook name is equivalent when it is already open:

```python
hp.Excel.to_excel_open(df, "model.xlsx", sheet="Data")
```

!!! tip "Typical pattern"
    Keep the formulas and charts of a model in an Excel template that reads from tables (`tbl_prices`). Refresh the data from Python with `to_excel_open(..., to_table=True, clear_range=True)`; the tables resize and the formulas update.

---

## Choosing the right function

| I want to... | Use |
|---|---|
| Refresh data inside an Excel model that is open | `to_excel_open` |
| Produce or update a data file in a job / server | `to_excel_closed` |
| Deliver a formatted table to a colleague | `to_excel_closed_styled` |
| Deliver a table as an **image** or put it in a slide | [`TableSheet`](../DfStyling/getting_started.md) |

---

[API reference of Excel](../api/Excel/excel.md)
