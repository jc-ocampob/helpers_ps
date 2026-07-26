from __future__ import annotations

import io
import locale
import warnings
from dataclasses import dataclass, field
from importlib.resources import files

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MultipleLocator

try:
    from helpers_ps.GlobVars.var_globs import PALETA_COLORES
except Exception:
    PALETA_COLORES = [
        "#2F71E5", "#00A6A6", "#F28E2B", "#E15759", "#76B7B2",
        "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F"
    ]

class Line_tags():
    # funcion para procesar diccionario de controles de annotaciones
    """
    Provide helper methods for line-chart annotations.

    Notes
    -----
    This docstring was added during the modular refactor to make the API easier
    to understand for new users and maintainers.
    """
    def _line_label_generate(
        self,
        control_dict: dict = None,
    ) -> None:
        """
        Generate line chart labels and markers based on a control dictionary.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if control_dict is None:
            return None
        df = self._df

        if not hasattr(self, "_custom_legend_handles"):
            self._custom_legend_handles = []

        existing_labels = {h.get_label() for h in self._custom_legend_handles}

        
        # una vez validado la información generar los puntos en base a las variables de control

        def _generate(
                ticker,
                x_values: list[str | float | int] | str = "last",
                show: str = "dot",
                template: str = "{ticker}\n{x_value:%B-%Y}: {y_value:,.2f}",
                tag: dict | None = None,
                dot: dict | None = None,
                legend_label: str | None = None,
        ):

            # Validar que es un ticker valido
            """
            Execute `_generate` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            if ticker not in df.columns:
                raise ValueError(f"El ticker {ticker} no es una columna disponible en el dataframe")
            
            tag = dict() if tag is None else tag.copy()
            dot = dict() if dot is None else dot.copy()
            
            # obtener los valores referenciales en formato de list of tuple
            xy_pairs = []
            if isinstance(x_values, str) and x_values == "last":
                last_x_value = df.tail(1)
                last_x_value = last_x_value.index.tolist()[0]
                last_value_y = df.loc[last_x_value, ticker].item()
                xy_pairs.append((last_x_value, last_value_y))
            elif isinstance(x_values, list):
                for i in x_values:
                    
                    if isinstance(i, str) and i == "last":
                        last_x_value = df.tail(1)
                        last_x_value = last_x_value.index.tolist()[0]
                        last_value_y = df.loc[last_x_value, ticker].item()
                        xy_pairs.append((last_x_value, last_value_y))
                        continue

                    _val_x = i
                    _val_y = df.loc[i, ticker].item()
                    xy_pairs.append((_val_x, _val_y))
            
            # con los pares xy generarlo en el grafico
            for pair in xy_pairs:
                x, y = pair
                _ticker_label_color = [dd for dd in self._ticker_label_color if dd[0] == ticker]

                dot_color = dot.get("color")

                if dot_color is None:
                    dot_color = _ticker_label_color[0][2]

                if legend_label is not None and legend_label not in existing_labels:
                    self._custom_legend_handles.append(
                        Line2D(
                            [0],
                            [0],
                            marker="o",
                            linestyle="None",
                            color="none",
                            markerfacecolor=dot_color,
                            markeredgecolor=dot_color,
                            markersize=np.sqrt(dot.get("size", 30)),
                            label=legend_label,
                        )
                    )
                    existing_labels.add(legend_label)

                if "tag" in show:
                    if tag.get("font_color") is None:
                        tag["font_color"] = _ticker_label_color[0][2]
                    self.etiqueta_valor(
                        label=template.format(x_value=x, y_value=y, ticker=ticker),
                        x_value=x,          # datetime real para texto "Mar 26: 4.3"
                        y_value=y,
                        **tag
                        )
                
                if "dot" in show:
                    if dot.get("color") is None:
                        dot["color"] = _ticker_label_color[0][2]
                    self.dot(
                        x_value=x,
                        y_value=y,
                        **dot
                    )

        for ti in control_dict.keys():
            _temp_controls = control_dict[ti]
            _generate(**_temp_controls)

