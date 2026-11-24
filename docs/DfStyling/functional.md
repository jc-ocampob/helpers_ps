# Functional styling (without a sheet)

Every styling operation of `TableSheet` also exists as a **function that takes a DataFrame or a `Styler` and returns a `Styler`**. Use them when you want the styled table itself: to show it in a notebook, export it to Excel, or build your own `Styler` pipeline.

```python
import numpy as np
import pandas as pd
import helpers_ps as hp

simple = pd.DataFrame(
    {"YTD": [0.121, 0.084, 0.032, 0.067], "1Y": [0.156, 0.101, 0.041, 0.083], "3Y": [0.092, 0.075, 0.028, 0.061]},
    index=["Equity", "Bonds", "Cash", "Total"],
)
```

All functions are available as `hp.DfStyling.<name>`:

| Function | Description |
|---|---|
| `style_table(obj, font_family, font_size, text_color, background_color, text_align, header_styles, index_styles, data_styles, column_header_styles, row_index_styles, show_index_names, corner_styles)` | General look (same arguments as the method of `TableSheet`). |
| `style_cell(obj, row, column, styles)` | CSS on one cell. |
| `style_cells(obj, rows, columns, styles)` | CSS on rows x columns. |
| `border_cell(obj, row, column, position, width, color, line_style)` | Border on one side of a cell. |
| `border_cells(obj, rows, columns, position, width, color, line_style)` | Border on one side of many cells. |
| `highlight_rows(obj, rows, styles, include_index, index_level)` | Highlight rows (default: bold and boxed). |
| `highlight_columns(obj, columns, styles, include_header, header_level)` | Highlight columns. |
| `border_rows(obj, rows, position, styles)` | Horizontal line across complete rows. |
| `border_columns(obj, columns, position, include_header, header_level, styles)` | Vertical line next to columns. |
| `text_color_by_range(value, ranges)` / `background_color_by_range(value, ranges)` | Return the CSS (`"color: ..."`) for **one value**; use with `Styler.map`. |

`obj` is a `DataFrame` or an existing `Styler`; the result is always a `Styler`, so calls chain through the variable:

```python
styled = hp.DfStyling.style_table(
    simple,
    font_size=11,
    text_align="center",
    header_styles={"color": "white", "background-color": "#12275A"},
)
styled = hp.DfStyling.highlight_rows(styled, "Total", styles={"background-color": "#FFF2CC"})
styled = hp.DfStyling.border_rows(styled, "Cash", styles={"width": "2px", "color": "#12275A"})
styled = styled.format("{:.1%}")

type(styled).__name__
```
**Output**

```text
'Styler'
```

---

## Conditional color of a single value

`text_color_by_range(value, ranges)` and `background_color_by_range(value, ranges)` are the **per-value** helpers behind the sheet methods. They return a CSS declaration and are meant for `Styler.map`:

```python
import numpy as np

ranges = {(-np.inf, 0): "#B7331F", (0, 0.05): "#C9A227", (0.05, np.inf): "#1E8449"}

print(hp.DfStyling.text_color_by_range(0.08, ranges))
print(hp.DfStyling.background_color_by_range(0.08, {(0.05, np.inf): "#D9EAD3"}))

colored = simple.style.map(lambda v: hp.DfStyling.text_color_by_range(v, ranges))
```
**Output**

```text
color: #1E8449
background-color: #D9EAD3
```

Intervals are lower-inclusive and upper-exclusive; a missing value or a value outside every interval returns an empty string.

---

## Export a styled table to Excel

A `Styler` keeps fonts, colors and borders when written to Excel with [`to_excel_closed_styled`](../Excel/getting_started.md#to_excel_closed_styled):

```python
hp.Excel.to_excel_closed_styled(styled, "report.xlsx", sheet_name="Performance")
```

Only the styles that Excel understands are preserved (colors, bold / italic, borders, alignment, number formats set with `format`).

---

[API reference of DfStyling](../api/DfStyling/sheet.md)
