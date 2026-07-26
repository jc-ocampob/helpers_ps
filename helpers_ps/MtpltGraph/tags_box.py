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

class BoxW_tags():
    """
    Provide helper methods for box-and-whisker chart annotations.

    Notes
    -----
    This docstring was added during the modular refactor to make the API easier
    to understand for new users and maintainers.
    """
    def _box_whiskers_label_generate(
        self,
        control_dict: dict = None,
    ) -> None:
        
        """
        Generate labels and annotations for box-and-whisker chart statistics.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if control_dict is None:
            return None

        df = self._df
        columns = df.columns.tolist()

        # ---------------------------------------------------------
        # Custom legend handles para puntos de box & whiskers
        # ---------------------------------------------------------
        if not hasattr(self, "_custom_legend_handles"):
            self._custom_legend_handles = []

        existing_labels = {h.get_label() for h in self._custom_legend_handles}

        def _generate(
                ticker,
                x_values: list[str | float | int] | str = "last",
                show: str = "dot",       # dot | tag | dot_tag
                template: str = "{y_value:,.2f}",
                tag: dict | None = None,
                dot: dict | None = None,
                legend_label: str | None = None,
                legend_marker: str = "o",
        ):
            """
            Execute `_generate` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """

            # -----------------------------------------------------
            # Validaciones
            # -----------------------------------------------------
            if ticker not in columns:
                raise ValueError(f"El ticker {ticker} no es una columna disponible en el dataframe")
            
            tag = dict() if tag is None else tag.copy()
            dot = dict() if dot is None else dot.copy()

            # Posición categórica del boxplot
            z_value = columns.index(ticker) + 1

            # Color base del ticker
            _ticker_label_color = [dd for dd in self._ticker_label_color if dd[0] == ticker]

            if len(_ticker_label_color) == 0:
                raise ValueError(f"No se encontró metadata de color para el ticker {ticker}")

            ticker_color = _ticker_label_color[0][2]

            # -----------------------------------------------------
            # Defaults heredados para tag y dot
            # -----------------------------------------------------
            if tag.get("font_color") is None:
                tag["font_color"] = ticker_color

            if dot.get("color") is None:
                dot["color"] = ticker_color

            if dot.get("size") is None:
                dot["size"] = 30

            if dot.get("zorder") is None:
                dot["zorder"] = 5

            # -----------------------------------------------------
            # Handle artificial para leyenda, sin tocar dot
            # -----------------------------------------------------
            if legend_label is not None and legend_label not in existing_labels:

                self._custom_legend_handles.append(
                    Line2D(
                        [0],
                        [0],
                        marker=legend_marker,
                        linestyle="None",
                        color="none",
                        markerfacecolor=dot.get("color"),
                        markeredgecolor=dot.get("color"),
                        markersize=np.sqrt(dot.get("size", 30)),
                        label=legend_label,
                    )
                )

                existing_labels.add(legend_label)

            # -----------------------------------------------------
            # Resolver pares x/y/z
            # -----------------------------------------------------
            xyz_pairs = []

            if isinstance(x_values, str) and x_values == "last":
                last_x_value = df.tail(1)
                last_x_value = last_x_value.index.tolist()[0]
                last_value_y = df.loc[last_x_value, ticker].item()
                xyz_pairs.append((last_x_value, last_value_y, z_value))

            elif isinstance(x_values, list):
                for i in x_values:

                    if isinstance(i, str) and i == "last":
                        last_x_value = df.tail(1)
                        last_x_value = last_x_value.index.tolist()[0]
                        last_value_y = df.loc[last_x_value, ticker].item()
                        xyz_pairs.append((last_x_value, last_value_y, z_value))
                        continue

                    _val_x = i
                    _val_y = df.loc[i, ticker].item()
                    xyz_pairs.append((_val_x, _val_y, z_value))

            else:
                raise ValueError("x_values debe ser 'last' o una lista de valores del índice.")

            # -----------------------------------------------------
            # Graficar puntos y/o etiquetas
            # -----------------------------------------------------
            for pair in xyz_pairs:
                x, y, z = pair

                if "tag" in show:
                    self.etiqueta_valor(
                        label=template.format(
                            x_value=x,
                            y_value=y,
                            ticker=ticker
                        ),
                        x_value=z,
                        y_value=y,
                        **tag
                    )

                if "dot" in show:
                    self.dot(
                        x_value=z,
                        y_value=y,
                        **dot
                    )

        for ti in control_dict.keys():
            _temp_controls = control_dict[ti]
            _generate(**_temp_controls)

