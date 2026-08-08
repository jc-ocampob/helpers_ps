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

from ._colors import PALETA_COLORES

class BarTags:
    """
    Provide helper methods for bar-chart labels, values, and tags.

    Notes
    -----
    This docstring was added during the modular refactor to make the API easier
    to understand for new users and maintainers.
    """

    def _bar_x_key_normalize(self, value):
        """
        Normalize bar-chart x-axis keys to make lookup matching consistent.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        try:
            if isinstance(value, (pd.Timestamp, np.datetime64)):
                return pd.Timestamp(value)
            return pd.Timestamp(value)
        except Exception:
            return str(value)

    def _bar_resolve_x_indices(self, ticker: str, x_values) -> list:
        """
        Resolve one or more bar positions from a ticker or x-axis value.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not self._bars_x_reference:
            raise ValueError(
                "No existe self._bars_x_reference. Guarda la referencia del eje x dentro de graph_bar."
            )

        x_ref = list(self._bars_x_reference)
        x_ref_norm = [self._bar_x_key_normalize(v) for v in x_ref]

        if x_values is None:
            x_values = "last"

        if x_values == "all":
            return list(range(len(x_ref)))

        if x_values == "last":
            bars_entry = self._bars_data.get(ticker)

            if bars_entry is None:
                return []

            for idx in range(len(x_ref) - 1, -1, -1):
                rect, _mode = self._bar_get_rect_for_index(
                    bars_entry=bars_entry,
                    idx=idx
                )

                if rect is None:
                    continue

                h = rect.get_height()

                if h is not None and not np.isnan(h) and abs(h) > 0:
                    return [idx]

            return [len(x_ref) - 1] if len(x_ref) > 0 else []

        if not isinstance(x_values, (list, tuple, set)):
            raise ValueError(
                "x_values debe ser 'all', 'last' o una lista/tupla/set de fechas/categorías."
            )

        requested = {self._bar_x_key_normalize(v) for v in x_values}

        return [
            i for i, v in enumerate(x_ref_norm)
            if v in requested
        ]

    def _bar_get_rect_for_index(self, bars_entry: dict, idx: int):
        """
        Return the Matplotlib bar rectangle associated with a resolved x-index.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        bars_obj = bars_entry["bars"]

        # --- stacked
        if isinstance(bars_obj, dict):
            bars_pos = bars_obj.get("pos")
            bars_neg = bars_obj.get("neg")

            rect_pos = None
            rect_neg = None

            if bars_pos is not None and idx < len(bars_pos):
                rect_pos = bars_pos[idx]

            if bars_neg is not None and idx < len(bars_neg):
                rect_neg = bars_neg[idx]

            h_pos = rect_pos.get_height() if rect_pos is not None else 0.0
            h_neg = rect_neg.get_height() if rect_neg is not None else 0.0

            if (
                rect_pos is not None
                and h_pos is not None
                and not np.isnan(h_pos)
                and abs(h_pos) > 0
            ):
                return rect_pos, "stacked"

            if (
                rect_neg is not None
                and h_neg is not None
                and not np.isnan(h_neg)
                and abs(h_neg) > 0
            ):
                return rect_neg, "stacked"

            return None, "stacked"

        # --- grouped / single
        if idx < len(bars_obj):
            return bars_obj[idx], "grouped"

        return None, "grouped"

    def _bar_get_stack_total_anchor(self, idx: int, ref_ticker: str):
        """
        Find the anchor point for labels over stacked bar totals.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if ref_ticker not in self._bars_data:
            return None, None, None, None

        total_value = 0.0
        top_positive = 0.0
        bottom_negative = 0.0

        ref_rect, ref_mode = self._bar_get_rect_for_index(
            self._bars_data[ref_ticker],
            idx
        )

        if ref_rect is None:
            return None, None, None, None

        if ref_mode != "stacked":
            raise ValueError(
                "El total del stack solo aplica cuando el gráfico es stacked."
            )

        x = ref_rect.get_x() + ref_rect.get_width() / 2.0

        for _ticker, entry in self._bars_data.items():
            bars_obj = entry["bars"]

            if not isinstance(bars_obj, dict):
                continue

            rect_pos = None
            rect_neg = None

            if bars_obj.get("pos") is not None and idx < len(bars_obj["pos"]):
                rect_pos = bars_obj["pos"][idx]

            if bars_obj.get("neg") is not None and idx < len(bars_obj["neg"]):
                rect_neg = bars_obj["neg"][idx]

            if rect_pos is not None:
                h = rect_pos.get_height()

                if h is not None and not np.isnan(h):
                    total_value += h
                    top_positive = max(
                        top_positive,
                        rect_pos.get_y() + rect_pos.get_height()
                    )

            if rect_neg is not None:
                h = rect_neg.get_height()

                if h is not None and not np.isnan(h):
                    total_value += h
                    bottom_negative = min(
                        bottom_negative,
                        rect_neg.get_y() + rect_neg.get_height()
                    )

        if total_value >= 0:
            return x, top_positive, total_value, "positive"

        return x, bottom_negative, total_value, "negative"

    def _bar_format_template(
        self,
        template: str,
        ticker: str,
        x_value,
        y_value: float | None = None,
        total_value: float | None = None,
        label: str | None = None
    ) -> str:
        """
        Format bar labels using value, percentage, and custom formatting rules.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        return template.format(
            ticker=ticker,
            label=label if label is not None else ticker,
            x_value=x_value,
            y_value=y_value,
            total_value=total_value
        )

    def _bar_label_generate_dict(self, label_dict: dict | None = None) -> None:
        """
        Generate category labels for bar charts from a configuration dictionary.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not label_dict:
            return None

        if not hasattr(self, "_bars_data") or not self._bars_data:
            raise ValueError(
                "No existe self._bars_data. Ejecuta graph_bar antes de usar este helper."
            )

        ticker_to_label = {}

        if hasattr(self, "_ticker_label_color") and self._ticker_label_color is not None:
            for t, lbl, _c in self._ticker_label_color:
                ticker_to_label[t] = lbl

        x_ref = list(self._bars_x_reference)

        def _safe_offset(tag: dict, default: tuple[float, float]) -> tuple[float, float]:
            """
            Execute `_safe_offset` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            ubic = tag.get("ubic_etq", default)

            if ubic is None:
                return default

            return ubic

        def _control(
            ticker: str | None = None,
            show: str = "value_label",
            x_values: list[str | int | float] | str | None = "last",
            template: str = "{y_value:,.2f}",
            tag: dict | None = None,
        ):
            """
            Execute `_control` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            if not ticker:
                return None

            if ticker not in self._bars_data:
                return None

            tag = dict() if tag is None else tag.copy()

            idxs = self._bar_resolve_x_indices(
                ticker=ticker,
                x_values=x_values
            )

            for idx in idxs:
                x_value = x_ref[idx]
                label = ticker_to_label.get(ticker, ticker)

                # ======================================================
                # 1. TAG SOBRE TOTAL DEL STACK
                # ======================================================
                if show == "stack_total":
                    x, y_anchor, total_value, sign = self._bar_get_stack_total_anchor(
                        idx=idx,
                        ref_ticker=ticker
                    )

                    if x is None:
                        continue

                    text = self._bar_format_template(
                        template=template,
                        ticker=ticker,
                        x_value=x_value,
                        y_value=None,
                        total_value=total_value,
                        label=label
                    )

                    if sign == "positive":
                        tag["label_v_align"] = tag.get("label_v_align", "bottom")
                        ox, oy = _safe_offset(tag, (0, 5))
                        tag["ubic_etq"] = (ox, abs(oy))
                    else:
                        tag["label_v_align"] = tag.get("label_v_align", "top")
                        ox, oy = _safe_offset(tag, (0, -5))
                        tag["ubic_etq"] = (ox, -abs(oy))

                    self.tag(
                        x_value=x,
                        y_value=y_anchor,
                        label=text,
                        **tag
                    )

                    continue

                # ======================================================
                # 2. VALUE LABEL O BAR TAG SOBRE BARRA / SEGMENTO
                # ======================================================
                rect, mode = self._bar_get_rect_for_index(
                    bars_entry=self._bars_data[ticker],
                    idx=idx
                )

                if rect is None:
                    continue

                h = rect.get_height()

                if h is None or np.isnan(h) or abs(h) == 0:
                    continue

                x = rect.get_x() + rect.get_width() / 2.0
                y_segment_center = rect.get_y() + rect.get_height() / 2.0
                y_end = rect.get_y() + rect.get_height()

                text = self._bar_format_template(
                    template=template,
                    ticker=ticker,
                    x_value=x_value,
                    y_value=h,
                    total_value=None,
                    label=label
                )

                # ------------------------------------------------------
                # 2A. Etiqueta numérica estándar
                # ------------------------------------------------------
                if show == "value_label":
                    # stacked: centro del segmento
                    if mode == "stacked":
                        ox, oy = _safe_offset(tag, (0, 0))
                        tag["ubic_etq"] = (ox, oy)

                        self.tag(
                            x_value=x,
                            y_value=y_segment_center,
                            label=text,
                            **tag
                        )

                    # grouped/single: final de la barra
                    else:
                        if h >= 0:
                            tag["label_v_align"] = tag.get("label_v_align", "bottom")
                            ox, oy = _safe_offset(tag, (0, 3))
                            tag["ubic_etq"] = (ox, abs(oy))
                        else:
                            tag["label_v_align"] = tag.get("label_v_align", "top")
                            ox, oy = _safe_offset(tag, (0, -3))
                            tag["ubic_etq"] = (ox, -abs(oy))

                        self.tag(
                            x_value=x,
                            y_value=y_end,
                            label=text,
                            **tag
                        )

                    continue

                # ------------------------------------------------------
                # 2B. Tag libre al centro de barra / segmento
                # ------------------------------------------------------
                if show == "bar_tag":
                    ox, oy = _safe_offset(tag, (0, 0))
                    tag["ubic_etq"] = (ox, oy)

                    self.tag(
                        x_value=x,
                        y_value=y_segment_center,
                        label=text,
                        **tag
                    )

                    continue

                raise ValueError(
                    "show debe ser uno de: 'value_label', 'bar_tag', 'stack_total'."
                )

        for _key, cfg in label_dict.items():
            _control(**cfg)

    # ---------------------------------------------------------------------
    # Backward compatibility wrappers
    # ---------------------------------------------------------------------
    def _bar_value_label_generate_dict(self, label_dict: dict | None = None) -> None:
        """
        Generate numeric value labels for bar charts from a configuration dictionary.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not label_dict:
            return None

        new_dict = {}

        for k, cfg in label_dict.items():
            cfg_new = cfg.copy()
            cfg_new.setdefault("show", "value_label")
            new_dict[k] = cfg_new

        return self._bar_label_generate_dict(new_dict)

    def _bar_tag_generate_dict(self, tag_dict: dict | None = None) -> None:
        """
        Generate custom bar tags or callouts from a configuration dictionary.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not tag_dict:
            return None

        new_dict = {}

        for k, cfg in tag_dict.items():
            cfg_new = cfg.copy()
            cfg_new.setdefault("show", "bar_tag")
            new_dict[k] = cfg_new

        return self._bar_label_generate_dict(new_dict)

