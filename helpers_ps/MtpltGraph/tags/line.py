from __future__ import annotations
import numpy as np
from matplotlib.lines import Line2D
from collections.abc import Mapping
from typing import Any

class LineTags():
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
        control_dict: Mapping[str, dict[str, Any]] | None = None,
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
                    self.tag(
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

        for control_name, controls in control_dict.items():
            _generate(**controls)

    def _split_tag_controls_by_axis(
        self,
        tag_dot: dict | None,
        axis_map: dict[str, str],
    ) -> tuple[dict, dict]:
        if not tag_dot:
            return {}, {}

        tag_dot_left = {}
        tag_dot_right = {}

        for control_name, control in tag_dot.items():
            ticker = control.get("ticker")

            if ticker is None:
                tag_dot_left[control_name] = control
                continue

            if axis_map.get(ticker, "left") == "right":
                tag_dot_right[control_name] = control
            else:
                tag_dot_left[control_name] = control

        return tag_dot_left, tag_dot_right

    def _apply_line_tags_by_axis(
        self,
        tag_dot: dict | None,
        axis_map: dict[str, str],
        left_ax,
        right_ax,
    ) -> None:
        tag_dot_left, tag_dot_right = self._split_tag_controls_by_axis(
            tag_dot=tag_dot,
            axis_map=axis_map,
        )

        if tag_dot_left:
            self._ax = left_ax
            self._line_label_generate(tag_dot_left)

        if tag_dot_right:
            if right_ax is None:
                raise RuntimeError(
                    "Right axis was not initialized for right-side tags."
                )

            self._ax = right_ax
            self._line_label_generate(tag_dot_right)

        self._ax = left_ax