# Importar librerias necesarias
from pptx.enum.chart import XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_LABEL_POSITION

# Multigraph layout on presentations
LAYOUT2_2 = {
    "height": 6,
    "width": 12,
    "position_x": [1.5, 1.5, 14, 14],
    "position_y": [1.5, 8, 1.5, 8],
}

LAYOUT3_2 = {
    "height": 5.5,
    "width": 9,
    "position_x": [0.5, 9.5, 18.5, 
              0.5, 9.5, 18.5],
    "position_y": [1.5, 1.5, 1.5,
              7.5, 7.5, 7.5],
}

LAYOUT3_3 = {
    "height": 4,
    "width": 9,
    "position_x": [1, 10, 19, 
              1, 10, 19,
              1, 10, 19],
    "position_y": [1.5, 1.5, 1.5,
              5.5, 5.5, 5.5,
              9.5, 9.5, 9.5],
}

LAYOUT4_3 = {
    "height": 4,
    "width": 6.5,
    "position_x": [0.5, 7, 13.5, 20, 
              0.5, 7, 13.5, 20,
              0.5, 7, 13.5, 20],
    "position_y": [1.5, 1.5, 1.5, 1.5,
              5.5, 5.5, 5.5, 5.5,
              9.5, 9.5, 9.5, 9.5],
}


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

