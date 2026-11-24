# Template helpers

When you build decks from a **corporate template** (`.pptx`) you rarely draw from scratch: you pick a layout, find the placeholder or text box called *"Title"*, *"Date"* or *"Note"*, replace its text **without losing the template's font and color**, fill table cells and delete the slides you do not need. These helpers cover that workflow.

```python
import helpers_ps as hp
from pptx import Presentation
from pptx.util import Cm

prs = Presentation()                                   # in practice: Presentation("template.pptx")
layout = prs.slide_layouts[1]                          # "Title and Content"
slide = prs.slides.add_slide(layout)
```

| Function | Description |
|---|---|
| `get_layout_by_name(prs, layout_name)` | Slide layout of the presentation by **name**. `ValueError` if it does not exist. |
| `get_shape_by_name(slide, target_name)` | Shape of a slide by **name**, searching inside groups too. `None` if not found. |
| `replace_text_preserve_style(target, new_text, ...)` | Replace the text of a shape or table cell **keeping the formatting** of its first paragraph and run. |
| `delete_slide(prs, slide_index)` | Delete a slide by position. |
| `hex_to_rgb(hex_color)` | `"#122B5F"` or `"122B5F"` to a python-pptx `RGBColor`. |

`get_shape_by_name`, `get_layout_by_name` and `replace_text_preserve_style` are available as `hp.Ppt.<name>`; `delete_slide` and `hex_to_rgb` live in `helpers_ps.Ppt.utils`.

---

## Naming shapes in your template

Shapes are found by the name shown in PowerPoint's **Selection Pane** (Home > Arrange > Selection Pane, `Alt+F10`). Give meaningful names to the boxes you will fill (`txt_title`, `txt_date`, `tbl_summary`, `note`) and the code becomes independent of their position.

To list what a slide contains:

```python
for shape in slide.shapes:
    print(shape.shape_id, repr(shape.name), shape.shape_type, shape.has_text_frame)
```
**Output**

```text
2 'Title 1' PLACEHOLDER (14) True
3 'Content Placeholder 2' PLACEHOLDER (14) True
```

And the layouts available in a template:

```python
[layout.name for layout in prs.slide_layouts]
```
**Output**

```text
['Title Slide', 'Title and Content', 'Section Header', 'Two Content', 'Comparison', 'Title Only', 'Blank', 'Content with Caption', 'Picture with Caption', 'Title and Vertical Text', 'Vertical Title and Text']
```

---

## `get_layout_by_name` and `get_shape_by_name`

```python
layout = hp.Ppt.get_layout_by_name(prs, "Title Only")
slide = prs.slides.add_slide(layout)

title = hp.Ppt.get_shape_by_name(slide, "Title 1")
print(title.name if title else None)
print(hp.Ppt.get_shape_by_name(slide, "does not exist"))
```
**Output**

```text
Title 1
None
```

!!! tip "Names must be exact"
    The comparison is exact (case and spaces). Python-pptx names placeholders like `"Title 1"`; in a corporate template they are whatever you set in the Selection Pane.

---

## `replace_text_preserve_style`

`replace_text_preserve_style(target, new_text, *, preserve_linebreaks=True, linebreak_replacement=" ", clear_extra_runs=True, clear_extra_paragraphs=True, none_as_empty=True)`

`target` is **any object with a `text_frame`**: a shape, a placeholder or a **table cell**. The new text takes the formatting of the **first run of the first paragraph** (font, size, color, bold...), so the template look survives.

| Argument | Default | Description |
|---|---|---|
| `new_text` | | The text. Non-strings are converted with `str()`. |
| `preserve_linebreaks` | `True` | Each `\n` becomes a new paragraph copying the first paragraph's format. If `False`, line breaks are replaced by `linebreak_replacement`. |
| `clear_extra_runs` | `True` | Remove the other runs of the first paragraph (otherwise old fragments with different formatting remain). |
| `clear_extra_paragraphs` | `True` | Remove paragraphs after the first one before writing multiline text. |
| `none_as_empty` | `True` | `None` becomes `""`. With `False` it becomes the text `"None"`. |

```python
title = hp.Ppt.get_shape_by_name(slide, "Title 1")

hp.Ppt.replace_text_preserve_style(title, "Monthly report\nPortfolio Solutions")
[p.text for p in title.text_frame.paragraphs]
```
**Output**

```text
['Monthly report', 'Portfolio Solutions']
```

A target without a text frame raises `ValueError`.

### Filling a table

Tables in a slide are shapes whose `.table` has `.cell(row, col)`; each cell works as a target:

```python
import pandas as pd

summary = pd.DataFrame(
    {"YTD": [0.121, 0.084], "1Y": [0.156, 0.101]},
    index=["Portfolio", "Benchmark"],
)

shape = slide.shapes.add_table(3, 3, Cm(2), Cm(6), Cm(12), Cm(3))
table = shape.table

headers = ["", *summary.columns]
for j, header in enumerate(headers):
    hp.Ppt.replace_text_preserve_style(table.cell(0, j), header)

for i, (name, row) in enumerate(summary.iterrows(), start=1):
    hp.Ppt.replace_text_preserve_style(table.cell(i, 0), name)
    for j, value in enumerate(row, start=1):
        hp.Ppt.replace_text_preserve_style(table.cell(i, j), f"{value:.1%}")

table.cell(1, 1).text
```
**Output**

```text
'12.1%'
```

When your template already contains a formatted table, **do not add a new one**: find it by name (`get_shape_by_name(slide, "tbl_summary").table`) and fill its cells; the formatting comes along.

---

## Deleting slides

Use it to remove the example slides of a template once the real ones are built:

```python
from helpers_ps.Ppt.utils import delete_slide

delete_slide(prs, 0)            # delete the first slide
```

Delete from the **last** slide to the first when removing several, because positions shift after every deletion:

```python
for index in sorted([0, 2, 3], reverse=True):
    delete_slide(prs, index)
```

!!! warning "Only the slide reference is removed"
    `delete_slide` removes the slide from the presentation order. The slide part may remain in the file package until PowerPoint re-saves it; this is harmless for normal use.

---

## A complete mini workflow

```python
import numpy as np
from pptx import Presentation
from pptx.util import Cm

prs = Presentation()
prs.slide_width, prs.slide_height = Cm(33.867), Cm(19.05)

slide = prs.slides.add_slide(hp.Ppt.get_layout_by_name(prs, "Title Only"))
hp.Ppt.replace_text_preserve_style(hp.Ppt.get_shape_by_name(slide, "Title 1"), "Performance review")

months = ["Jan", "Feb", "Mar", "Apr"]
returns = [1.2, 0.8, -0.4, 1.6]

hp.Ppt.BarChart(
    presentation=prs, slide=0,
    position_x=2, position_y=4, width=18, height=10,
    series_names=["Portfolio"], x_values=[months], y_values=[returns],
    colors=["#12275A"], data_labels_show=True, data_labels_position="outside_end",
    x_axis_position="low",
).chart()

prs.save("review.pptx")
[shape.name for shape in prs.slides[0].shapes]
```
**Output**

```text
['Title 1', 'Chart 2']
```

---

[API reference of Ppt](../api/Ppt/ppt.md)
