from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd


class BoxWTags:
    """
    Provides reference-resolution and annotation logic for box charts.

    Each reference is declared inside ``BoxSeriesConfig.tag`` and can
    independently use the shared ``self.tag()`` and ``self.dot()``
    methods through nested ``tag`` and ``dot`` dictionaries.
    """

    def _normalize_box_reference_key(
        self,
        value,
        index: pd.Index,
    ):
        """Normalize a requested reference against the series index."""
        if pd.api.types.is_datetime64_any_dtype(index):
            try:
                return pd.Timestamp(value)
            except (TypeError, ValueError):
                return value

        if pd.api.types.is_numeric_dtype(index):
            try:
                return float(value)
            except (TypeError, ValueError):
                return value

        return str(value)

    def _resolve_box_reference_indices(
        self,
        *,
        values: pd.Series,
        x_values,
    ) -> list[int]:
        """
        Resolve requested X-values into positional series indices.

        Supported values are ``"last"``, ``"all"``, one index value,
        or a sequence of index values.
        """
        if values.empty:
            return []

        numeric_values = pd.to_numeric(
            values,
            errors="coerce",
        )

        finite_mask = pd.Series(
            np.isfinite(
                numeric_values.to_numpy(dtype=float)
            ),
            index=numeric_values.index,
        )

        valid_mask = (
            numeric_values.notna()
            & finite_mask
        )

        valid_positions = np.flatnonzero(
            valid_mask.to_numpy()
        )

        if len(valid_positions) == 0:
            return []

        if x_values is None:
            x_values = "last"

        if isinstance(x_values, str):
            if x_values == "all":
                return valid_positions.tolist()

            if x_values == "last":
                return [int(valid_positions[-1])]

            requested_values = [x_values]

        elif isinstance(
            x_values,
            (list, tuple, set, pd.Index, np.ndarray),
        ):
            requested_values = list(x_values)

        else:
            requested_values = [x_values]

        index = values.index

        normalized_index = [
            self._normalize_box_reference_key(
                value,
                index,
            )
            for value in index
        ]

        normalized_requested = {
            self._normalize_box_reference_key(
                value,
                index,
            )
            for value in requested_values
        }

        return [
            position
            for position, value in enumerate(normalized_index)
            if (
                value in normalized_requested
                and bool(valid_mask.iloc[position])
            )
        ]

    def _calculate_box_statistics(
        self,
        *,
        values: pd.Series,
        whis,
    ) -> dict[str, float]:
        """Calculate supported statistics for one box series."""
        numeric_values = pd.to_numeric(
            values,
            errors="coerce",
        )

        numeric_values = (
            numeric_values
            .replace([np.inf, -np.inf], np.nan)
            .dropna()
        )

        if numeric_values.empty:
            raise ValueError(
                "Cannot calculate box statistics from "
                "an empty numeric series."
            )

        array = numeric_values.to_numpy(dtype=float)

        q1 = float(np.percentile(array, 25))
        median = float(np.percentile(array, 50))
        q3 = float(np.percentile(array, 75))
        mean = float(np.mean(array))

        if (
            isinstance(whis, (tuple, list))
            and len(whis) == 2
        ):
            low = float(
                np.percentile(array, whis[0])
            )
            high = float(
                np.percentile(array, whis[1])
            )

        else:
            iqr = q3 - q1
            whis_factor = float(whis)

            lower_limit = q1 - whis_factor * iqr
            upper_limit = q3 + whis_factor * iqr

            lower_values = array[
                array >= lower_limit
            ]
            upper_values = array[
                array <= upper_limit
            ]

            low = float(
                np.min(lower_values)
                if len(lower_values)
                else np.min(array)
            )
            high = float(
                np.max(upper_values)
                if len(upper_values)
                else np.max(array)
            )

        return {
            "low": low,
            "high": high,
            "mean": mean,
            "median": median,
            "q1": q1,
            "q3": q3,
        }

    def _format_box_reference_label(
        self,
        *,
        template: str,
        ticker: str,
        series_label: str,
        x_value,
        y_value: float,
        statistic: str | None,
    ) -> str:
        """
        Format a label using the resolved reference metadata.

        Available fields are ``ticker``, ``label``, ``x_value``,
        ``y_value``, ``value``, and ``statistic``.
        """
        try:
            return template.format(
                ticker=ticker,
                label=series_label,
                x_value=x_value,
                y_value=y_value,
                value=y_value,
                statistic=statistic,
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid box-tag label for ticker "
                f"'{ticker}': {template!r}."
            ) from exc

    def _resolve_box_reference_coordinates(
        self,
        *,
        values: pd.Series,
        box_position: int,
        vertical: bool,
        reference_position: int | None = None,
        statistic: str | None = None,
        whis=1.5,
    ) -> tuple[float, float, Any, float]:
        """
        Resolve chart coordinates and source metadata for a reference.
        """
        if statistic is not None:
            statistics = self._calculate_box_statistics(
                values=values,
                whis=whis,
            )

            if statistic not in statistics:
                raise ValueError(
                    "'statistic' must be one of: "
                    "'low', 'high', 'mean', 'median', "
                    "'q1', or 'q3'."
                )

            source_x_value = None
            source_y_value = float(
                statistics[statistic]
            )

        else:
            if reference_position is None:
                raise ValueError(
                    "'reference_position' is required "
                    "for observation references."
                )

            source_x_value = values.index[
                reference_position
            ]

            source_y_value = float(
                pd.to_numeric(
                    values.iloc[reference_position],
                    errors="raise",
                )
            )

        if vertical:
            chart_x = float(box_position)
            chart_y = source_y_value
        else:
            chart_x = source_y_value
            chart_y = float(box_position)

        return (
            chart_x,
            chart_y,
            source_x_value,
            source_y_value,
        )

    def _apply_box_tag_control(
        self,
        *,
        chart_x: float,
        chart_y: float,
        ticker: str,
        series_label: str,
        source_x_value,
        source_y_value: float,
        statistic: str | None,
        tag_config: dict[str, Any] | None,
    ) -> None:
        """Format and pass nested tag controls to ``self.tag()``."""
        if tag_config is None:
            return

        if not isinstance(tag_config, dict):
            raise TypeError(
                "The nested 'tag' configuration must be "
                "a dictionary or None."
            )

        options = tag_config.copy()

        template = options.pop(
            "label",
            "{y_value:,.2f}",
        )

        formatted_label = self._format_box_reference_label(
            template=template,
            ticker=ticker,
            series_label=series_label,
            x_value=source_x_value,
            y_value=source_y_value,
            statistic=statistic,
        )

        self.tag(
            x_value=chart_x,
            y_value=chart_y,
            label=formatted_label,
            **options,
        )

    def _apply_box_dot_control(
        self,
        *,
        chart_x: float,
        chart_y: float,
        dot_config: dict[str, Any] | None,
    ) -> None:
        """Pass nested dot controls to ``self.dot()``."""
        if dot_config is None:
            return

        if not isinstance(dot_config, dict):
            raise TypeError(
                "The nested 'dot' configuration must be "
                "a dictionary or None."
            )

        options = dot_config.copy()

        self.dot(
            x_value=chart_x,
            y_value=chart_y,
            **options,
        )

    def _apply_resolved_box_reference(
        self,
        *,
        ticker: str,
        series_label: str,
        values: pd.Series,
        box_position: int,
        vertical: bool,
        whis,
        reference_config: dict[str, Any],
        reference_position: int | None = None,
        statistic: str | None = None,
    ) -> None:
        """Apply separate dot and tag controls to one reference."""
        (
            chart_x,
            chart_y,
            source_x_value,
            source_y_value,
        ) = self._resolve_box_reference_coordinates(
            values=values,
            box_position=box_position,
            vertical=vertical,
            reference_position=reference_position,
            statistic=statistic,
            whis=whis,
        )

        self._apply_box_dot_control(
            chart_x=chart_x,
            chart_y=chart_y,
            dot_config=reference_config.get("dot"),
        )

        self._apply_box_tag_control(
            chart_x=chart_x,
            chart_y=chart_y,
            ticker=ticker,
            series_label=series_label,
            source_x_value=source_x_value,
            source_y_value=source_y_value,
            statistic=statistic,
            tag_config=reference_config.get("tag"),
        )

    def _apply_single_box_reference(
        self,
        *,
        ticker: str,
        series_label: str,
        values: pd.Series,
        box_position: int,
        vertical: bool,
        whis,
        reference_config: dict[str, Any],
    ) -> None:
        """Resolve and apply one box-series reference."""
        mode = reference_config.get(
            "mode",
            (
                "statistic"
                if "statistic" in reference_config
                else "observation"
            ),
        )

        if mode == "statistic":
            statistic = reference_config.get(
                "statistic"
            )

            if statistic is None:
                raise ValueError(
                    "A reference with mode='statistic' "
                    "must define 'statistic'."
                )

            self._apply_resolved_box_reference(
                ticker=ticker,
                series_label=series_label,
                values=values,
                box_position=box_position,
                vertical=vertical,
                whis=whis,
                reference_config=reference_config,
                statistic=statistic,
            )
            return

        if mode != "observation":
            raise ValueError(
                "'mode' must be 'observation' or "
                "'statistic'."
            )

        reference_positions = (
            self._resolve_box_reference_indices(
                values=values,
                x_values=reference_config.get(
                    "x_values",
                    "last",
                ),
            )
        )

        for reference_position in reference_positions:
            self._apply_resolved_box_reference(
                ticker=ticker,
                series_label=series_label,
                values=values,
                box_position=box_position,
                vertical=vertical,
                whis=whis,
                reference_config=reference_config,
                reference_position=reference_position,
            )

    def _apply_box_tags(
        self,
        *,
        dataframe: pd.DataFrame,
        series_config: list[dict[str, Any]],
        vertical: bool,
        whis,
        ax,
    ) -> None:
        """
        Apply references declared inside each box-series configuration.

        The outer reference resolves the observation or statistic.
        The nested ``dot`` dictionary is passed to ``self.dot()`` and
        the nested ``tag`` dictionary is passed to ``self.tag()``.
        """
        self._ax = ax

        for box_position, item in enumerate(
            series_config,
            start=1,
        ):
            ticker = item["ticker"]
            series_label = str(item["label"])

            references = item.get("tag")

            if not references:
                continue

            if isinstance(references, dict):
                references = [references]

            if not isinstance(references, (list, tuple)):
                raise TypeError(
                    f"'tag' for ticker '{ticker}' must "
                    "be a dictionary, list of dictionaries, "
                    "or None."
                )

            for position, reference in enumerate(references):
                if not isinstance(reference, dict):
                    raise TypeError(
                        "Each item inside 'tag' must be "
                        "a dictionary. Invalid item at "
                        f"position {position} for ticker "
                        f"'{ticker}'."
                    )

                if (
                    reference.get("tag") is None
                    and reference.get("dot") is None
                ):
                    continue

                self._apply_single_box_reference(
                    ticker=ticker,
                    series_label=series_label,
                    values=dataframe[ticker],
                    box_position=box_position,
                    vertical=vertical,
                    whis=whis,
                    reference_config=reference,
                )
