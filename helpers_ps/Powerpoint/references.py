# Importar librerias necesarias
from pptx.enum.chart import XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_LABEL_POSITION

LEGEND_POSITION = {
    "bottom": XL_LEGEND_POSITION.BOTTOM,
    "top": XL_LEGEND_POSITION.TOP,
    "right": XL_LEGEND_POSITION.RIGHT,
    "left": XL_LEGEND_POSITION.LEFT
}

# Posición de label
LABEL_POSITION = {
    "outside": XL_LABEL_POSITION.OUTSIDE_END,
    "left": XL_LABEL_POSITION.LEFT,
    "top": XL_LABEL_POSITION.ABOVE,
    "bottom": XL_LABEL_POSITION.BELOW,
    "right": XL_LABEL_POSITION.RIGHT,
    "center": XL_LABEL_POSITION.CENTER,
    "best_fit": XL_LABEL_POSITION.BEST_FIT,
    "inside_base": XL_LABEL_POSITION.INSIDE_BASE,
    "outside_end": XL_LABEL_POSITION.OUTSIDE_END,
}

# Posición de x-axis ticks

AXIS_POSITION = {
    "low": XL_TICK_LABEL_POSITION.LOW,
    "high": XL_TICK_LABEL_POSITION.HIGH,
    "center": XL_TICK_LABEL_POSITION.NEXT_TO_AXIS
}

