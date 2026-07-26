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

class Pie_tags():

    """
    Provide helper methods for pie-chart labels, values, and tags.

    Notes
    -----
    This docstring was added during the modular refactor to make the API easier
    to understand for new users and maintainers.
    """
    def _pie_format_template(
        self,
        template: str,
        ticker: str,
        value: float,
        pct: float,
        label: str | None = None,
    ) -> str:

        """
        Format pie chart labels using value, percentage, and custom formatting rules.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        return template.format(
            ticker=ticker,
            label=label if label is not None else ticker,
            value=value,
            pct=pct,
        )

    def _pie_get_anchor(
        self,
        ticker: str,
        radius: float = 0.7,
    ):

        """
        Compute the anchor coordinate for pie slice labels or callouts.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not hasattr(self, "_pie_data"):
            raise ValueError(
                "No existe self._pie_data. Ejecuta graph_pie antes de usar este helper."
            )

        if ticker not in self._pie_data:
            return None

        wedge = self._pie_data[ticker]["wedge"]

        theta = (wedge.theta1 + wedge.theta2) / 2.0
        theta_rad = np.deg2rad(theta)

        x = radius * np.cos(theta_rad)
        y = radius * np.sin(theta_rad)

        return x, y

    def _pie_value_label_generate_dict(
        self,
        label_dict: dict | None = None,
    ) -> None:

        """
        Generate numeric labels for pie slices from a configuration dictionary.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not label_dict:
            return

        if not hasattr(self, "_pie_data"):
            raise ValueError(
                "No existe self._pie_data. Ejecuta graph_pie antes de usar este helper."
            )

        ticker_to_label = {}

        if hasattr(self, "_ticker_label_color"):
            for t, lbl, _c in self._ticker_label_color:
                ticker_to_label[t] = lbl

        def _control(
            ticker: str | None = None,
            template: str = "{pct:.1f}%",
            radius: float = 0.65,
            font_color: str = "black",
            fontsize: int = 8,
            bg_color: str = "None",
            fontweight: str = "normal",
            label_h_align="center",
            label_v_align="center",
            ubic_etq=(0, 0),
            bg_alpha=1.0,
            edge_color="none",
            show_bbox=True,
            text_edge_color: str | None = None,
            text_edge_width: float = 0.0,
            zorder=6,
        ):

            """
            Execute `_control` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            if not ticker:
                return

            if ticker not in self._pie_data:
                return

            value = self._pie_data[ticker]["value"]
            pct = self._pie_data[ticker]["pct"]

            label = ticker_to_label.get(ticker, ticker)

            x, y = self._pie_get_anchor(
                ticker=ticker,
                radius=radius,
            )

            text = self._pie_format_template(
                template=template,
                ticker=ticker,
                value=value,
                pct=pct,
                label=label,
            )

            self.etiqueta_valor(
                x_value=x,
                y_value=y,
                label=text,
                ubic_etq=ubic_etq,
                bg_color=bg_color,
                font_color=font_color,
                fontsize=fontsize,
                fontweight=fontweight,
                bg_alpha=bg_alpha,
                edge_color=edge_color,
                show_bbox=show_bbox,
                text_edge_color=text_edge_color,
                text_edge_width=text_edge_width,
                zorder=zorder,
                label_h_align=label_h_align,
                label_v_align=label_v_align,
            )

        for _, cfg in label_dict.items():
            _control(**cfg)

    def _pie_tag_generate_dict(
        self,
        tag_dict: dict | None = None,
    ) -> None:

        """
        Generate custom pie chart callouts or tags from a configuration dictionary.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not tag_dict:
            return

        if not hasattr(self, "_pie_data"):
            raise ValueError(
                "No existe self._pie_data. Ejecuta graph_pie antes de usar este helper."
            )

        ticker_to_label = {}

        if hasattr(self, "_ticker_label_color"):
            for t, lbl, _c in self._ticker_label_color:
                ticker_to_label[t] = lbl

        def _control(
            ticker: str | None = None,
            template: str = "{label}\n{pct:.1f}%",
            radius: float = 1.15,
            font_color: str = "black",
            fontsize: int = 8,
            bg_color: str = "white",
            fontweight: str = "normal",
            label_h_align="center",
            label_v_align="center",
            ubic_etq=(0, 0),
            bg_alpha=1.0,
            edge_color="#BFBFBF",
            show_bbox=True,
            text_edge_color: str | None = None,
            text_edge_width: float = 0.0,
            zorder=7,
        ):

            """
            Execute `_control` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            if not ticker:
                return

            if ticker not in self._pie_data:
                return

            value = self._pie_data[ticker]["value"]
            pct = self._pie_data[ticker]["pct"]

            label = ticker_to_label.get(ticker, ticker)

            x, y = self._pie_get_anchor(
                ticker=ticker,
                radius=radius,
            )

            text = self._pie_format_template(
                template=template,
                ticker=ticker,
                value=value,
                pct=pct,
                label=label,
            )

            self.etiqueta_valor(
                x_value=x,
                y_value=y,
                label=text,
                ubic_etq=ubic_etq,
                bg_color=bg_color,
                font_color=font_color,
                fontsize=fontsize,
                fontweight=fontweight,
                bg_alpha=bg_alpha,
                edge_color=edge_color,
                show_bbox=show_bbox,
                text_edge_color=text_edge_color,
                text_edge_width=text_edge_width,
                zorder=zorder,
                label_h_align=label_h_align,
                label_v_align=label_v_align,
            )

        for _, cfg in tag_dict.items():
            _control(**cfg)

