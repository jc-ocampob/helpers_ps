"""
Reference dictionaries for PowerPoint chart formatting.

This module centralizes mappings between user-friendly string keys and
python-pptx enum values used for legends, data labels and axis tick labels.
"""

from pptx.enum.chart import (
    XL_LABEL_POSITION,
    XL_LEGEND_POSITION,
    XL_TICK_LABEL_POSITION,
)


LEGEND_POSITION = {
    "bottom": XL_LEGEND_POSITION.BOTTOM,
    "top": XL_LEGEND_POSITION.TOP,
    "right": XL_LEGEND_POSITION.RIGHT,
    "left": XL_LEGEND_POSITION.LEFT,
    "corner": XL_LEGEND_POSITION.CORNER,
}


LABEL_POSITION = {
    "outside": XL_LABEL_POSITION.OUTSIDE_END,
    "outside_end": XL_LABEL_POSITION.OUTSIDE_END,
    "inside_base": XL_LABEL_POSITION.INSIDE_BASE,
    "inside_end": XL_LABEL_POSITION.INSIDE_END,
    "center": XL_LABEL_POSITION.CENTER,
    "best_fit": XL_LABEL_POSITION.BEST_FIT,
    "left": XL_LABEL_POSITION.LEFT,
    "right": XL_LABEL_POSITION.RIGHT,
    "top": XL_LABEL_POSITION.ABOVE,
    "bottom": XL_LABEL_POSITION.BELOW,
}


AXIS_POSITION = {
    "low": XL_TICK_LABEL_POSITION.LOW,
    "high": XL_TICK_LABEL_POSITION.HIGH,
    "center": XL_TICK_LABEL_POSITION.NEXT_TO_AXIS,
    "next_to_axis": XL_TICK_LABEL_POSITION.NEXT_TO_AXIS,
    "none": XL_TICK_LABEL_POSITION.NONE,
}