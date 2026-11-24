# Ppt: Getting Started

The `Ppt` module creates **native, editable PowerPoint charts** (not pictures) on slides of a presentation, using [`python-pptx`](https://python-pptx.readthedocs.io/). It also includes helpers to **replace text while keeping the template formatting**, to find shapes and layouts by name and to delete slides.

| Need | Use | Page |
|---|---|---|
| Line, bar / column, pie, bubble and waterfall charts | `LineChart`, `BarChart`, `PieChart`, `BubbleChart`, `WaterfallChart` | [Charts](charts.md) |
| Fill a template: texts, tables, layouts, shapes | `replace_text_preserve_style`, `get_shape_by_name`, `get_layout_by_name`, `delete_slide` | [Template helpers](utilities.md) |
| Place several charts on a grid | `hp.Ppt.layouts` (`LAYOUT2_2`, `LAYOUT3_2`, `LAYOUT3_3`, `LAYOUT4_3`) | [Charts](charts.md#placing-several-charts-on-a-slide) |
| A static **picture** of a `GraphMtplt` chart or a table | `GraphMtplt.save()` / `TableSheet.to_bytes()` + `slide.shapes.add_picture` | [Pictures vs native charts](#native-charts-vs-pictures) |

```python
import helpers_ps as hp
from pptx import Presentation

prs = Presentation("template.pptx")          # or Presentation() for a blank deck

chart = hp.Ppt.LineChart(
    presentation=prs,
    slide=0,                                  # position of the slide (0 = first)
    position_x=2, position_y=3, width=15, height=8,      # centimeters
    series_names=["SPX", "NDX"],
    x_values=[dates, dates],
    y_values=[spx, ndx],
    legend_show=True,
).chart()                                     # inserts the chart and returns it

prs.save("output.pptx")
```

---

## Key ideas

1. **Each chart is a dataclass.** You fill its fields (data, position, formatting) and call `.chart()`; it validates the inputs, inserts the chart in the slide and returns the `pptx.chart.chart.Chart`, which you can keep modifying with `python-pptx`.
2. **Positions and sizes are in centimeters** (`position_x`, `position_y`, `width`, `height`), measured from the top-left corner of the slide.
3. **Data is passed as lists**, not as a DataFrame: `series_names`, `x_values`, `y_values` (one list per series). Build them from a DataFrame with `.index.tolist()` and `df[col].tolist()`.
4. **Defaults follow the house style**: font `Inter`, palette `hp.PALETA_COLORES`, small font sizes (5-6 pt) suited for dense slides.
5. The **slide must already exist** in the presentation (`slide` is its position). With a template, add the slide first with `prs.slides.add_slide(layout)`.

---

## Native charts vs pictures

| | Native (`Ppt` chart classes) | Picture (`GraphMtplt`, `TableSheet`) |
|---|---|---|
| Editable in PowerPoint | Yes: the data is embedded, colors and labels can be edited | No (image) |
| Visual flexibility | Limited to the options of the class | Very high (tags, dots, shaded regions, Bloomberg-style axis...) |
| File size | Small | Larger |
| Best for | Charts the audience may need to edit; simple standardized charts | Analytical charts with annotations; tables |

To insert a picture on a slide:

```python
import io
from pptx.util import Cm

buffer = graph.save()                      # GraphMtplt -> BytesIO (PNG)
slide = prs.slides[0]
slide.shapes.add_picture(buffer, Cm(2), Cm(3), width=Cm(15))

slide.shapes.add_picture(io.BytesIO(sheet.to_bytes()), Cm(2), Cm(3), width=Cm(20))   # TableSheet
```

---

## The `GraphPpt` class

`hp.Ppt.GraphPpt(data, presentation, slide=0, font_name="Inter")` is a **DataFrame-centered holder** with the same chaining style as `GraphMtplt`. It stores the DataFrame, the presentation, the active slide and the active chart, and offers:

| Member | Description |
|---|---|
| `df` | The DataFrame (`TypeError` if `data` is not a DataFrame). |
| `slide` | The active `pptx` slide object. |
| `chart` | The active native chart, or `None`. |
| `use_slide(i)` | Change the active slide (validates the range) and clears the active chart. |
| `copy_data(deep=True)` | Replace the data with a copy. |
| `pipe(func, ...)`, `tap(func, ...)` | Chaining helpers, as in `GraphMtplt`. |

!!! note "Current scope"
    In the current version `GraphPpt` provides the state management and validation shown above; the charts themselves are created with the chart classes of the next page. Its error messages mention `graph_line()`, `graph_bar()`, `graph_pie()`, `graph_bubble()` and `graph_waterfall()`, which are the planned DataFrame-based entry points and are **not available yet**.

---

## Next step

[Charts ->](charts.md)
