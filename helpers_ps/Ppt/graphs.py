"""
PowerPoint chart classes.

This module provides reusable dataclass-based wrappers around python-pptx chart
objects. The classes are designed to standardize chart creation across reports
and presentations while keeping formatting parameters easy to customize.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pptx.chart.data import BubbleChartData, CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Cm, Pt

from helpers_ps.GlobVars.var_globs import PALETA_COLORES

from .base import BasePowerPointChart
from .references import LABEL_POSITION
from .utils import (
    calculate_axis_bounds,
    flatten_nested_values,
    hex_to_rgb,
    validate_option,
)


BAR_CHART_TYPES = {
    "COLUMN_CLUSTERED": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "COLUMN_STACKED": XL_CHART_TYPE.COLUMN_STACKED,
    "COLUMN_STACKED_100": XL_CHART_TYPE.COLUMN_STACKED_100,
    "BAR_CLUSTERED": XL_CHART_TYPE.BAR_CLUSTERED,
    "BAR_STACKED": XL_CHART_TYPE.BAR_STACKED,
    "BAR_STACKED_100": XL_CHART_TYPE.BAR_STACKED_100,
}


WATERFALL_SERIES_ORDER = [
    "BasePositive",
    "BaseNegative",
    "IncreasePositive",
    "IncreaseNegative",
    "DecreasePositive",
    "DecreaseNegative",
    "TotalPositive",
    "TotalNegative",
    "LabelCarrier",
]


@dataclass
class LineChart(BasePowerPointChart):
    """
    Create a line chart in a PowerPoint slide.

    This class supports multiple line series. Since python-pptx line charts are
    category charts, all series must share the same x-axis categories.

    Parameters
    ----------
    series_names : list[str]
        Names of the chart series.
    x_values : list[list]
        Category labels for each series. All series must share the same
        categories.
    y_values : list[list[float]]
        Numeric values for each series.
    colors : list[str]
        Hexadecimal colors applied to each line series.

    Methods
    -------
    chart()
        Insert the line chart into the selected PowerPoint slide.

    Returns
    -------
    pptx.chart.chart.Chart
        The created chart object when calling chart().
    """

    series_names: list[str] = field(default_factory=list)
    x_values: list[list] = field(default_factory=list)
    y_values: list[list[float]] = field(default_factory=list)
    colors: list[str] = field(default_factory=lambda: PALETA_COLORES)

    x_axis_title_show: bool = False
    x_axis_title: str = ""
    x_axis_font_size: float = 6
    x_axis_number_format: str = "0.00"

    y_axis_title_show: bool = False
    y_axis_title: str = ""
    y_axis_font_size: float = 6
    y_axis_gridlines_show: bool = False
    y_axis_number_format: str = "0.00"
    y_axis_minimum_adjustment: float = 5.0
    y_axis_maximum_adjustment: float = 5.0

    def validate_inputs(self) -> None:
        """
        Validate line chart input data.

        Raises
        ------
        ValueError
            If the presentation is missing, series are empty, lengths are
            inconsistent or x-axis categories differ across series.
        """
        self.validate_base_inputs()

        if not self.series_names:
            raise ValueError("series_names cannot be empty.")

        if not self.x_values:
            raise ValueError("x_values cannot be empty.")

        if not self.y_values:
            raise ValueError("y_values cannot be empty.")

        if not (
            len(self.series_names)
            == len(self.x_values)
            == len(self.y_values)
        ):
            raise ValueError(
                "series_names, x_values and y_values must have the same "
                "number of series."
            )

        reference_categories = self.x_values[0]

        for index, series_name in enumerate(self.series_names):
            if len(self.x_values[index]) != len(self.y_values[index]):
                raise ValueError(
                    f"Series '{series_name}' has inconsistent lengths: "
                    f"len(x_values)={len(self.x_values[index])}, "
                    f"len(y_values)={len(self.y_values[index])}."
                )

            if self.x_values[index] != reference_categories:
                raise ValueError(
                    "All line chart series must share the same x-axis "
                    "categories."
                )

    def build_chart_data(self) -> CategoryChartData:
        """
        Build the chart data object used by python-pptx.

        Returns
        -------
        CategoryChartData
            Chart data object ready to be inserted into PowerPoint.
        """
        chart_data = CategoryChartData()
        chart_data.categories = self.x_values[0]

        for series_name, values in zip(self.series_names, self.y_values):
            chart_data.add_series(series_name, values)

        return chart_data

    def apply_series_format(self, chart) -> None:
        """
        Apply line color formatting to each chart series.

        Parameters
        ----------
        chart : pptx.chart.chart.Chart
            Chart object to format.
        """
        for index, series in enumerate(chart.series):
            color = self.colors[index % len(self.colors)]
            series.format.line.color.rgb = hex_to_rgb(color)

    def chart(self):
        """
        Insert the line chart into the selected PowerPoint slide.

        Returns
        -------
        pptx.chart.chart.Chart
            Created PowerPoint chart object.
        """
        self.validate_inputs()

        chart_data = self.build_chart_data()
        slide = self.get_slide()
        x, y, width, height = self.get_chart_position()

        chart = slide.shapes.add_chart(
            XL_CHART_TYPE.LINE,
            x,
            y,
            width,
            height,
            chart_data,
        ).chart

        y_minimum, y_maximum = calculate_axis_bounds(
            values=flatten_nested_values(self.y_values),
            minimum_adjustment_factor=self.y_axis_minimum_adjustment,
            maximum_adjustment_factor=self.y_axis_maximum_adjustment,
        )

        self.apply_title(chart)
        self.apply_value_axis(
            chart=chart,
            title_show=self.y_axis_title_show,
            title=self.y_axis_title,
            font_size=self.y_axis_font_size,
            number_format=self.y_axis_number_format,
            show_gridlines=self.y_axis_gridlines_show,
            minimum_scale=y_minimum,
            maximum_scale=y_maximum,
        )
        self.apply_category_axis(
            chart=chart,
            title_show=self.x_axis_title_show,
            title=self.x_axis_title,
            font_size=self.x_axis_font_size,
            number_format=self.x_axis_number_format,
        )
        self.apply_legend(chart)
        self.apply_series_format(chart)

        return chart


@dataclass
class PieChart(BasePowerPointChart):
    """
    Create a pie chart in a PowerPoint slide.

    Parameters
    ----------
    series_name : str
        Name of the data series.
    categories : list[str]
        Category labels for each slice.
    values : list[float]
        Numeric values for each slice.
    colors : list[str]
        Hexadecimal colors applied to each slice.

    Methods
    -------
    chart()
        Insert the pie chart into the selected PowerPoint slide.

    Returns
    -------
    pptx.chart.chart.Chart
        The created chart object when calling chart().
    """

    series_name: str = ""
    categories: list[str] = field(default_factory=list)
    values: list[float] = field(default_factory=list)
    colors: list[str] = field(default_factory=lambda: PALETA_COLORES)

    title_show: bool = True

    data_labels_show: bool = False
    data_labels_position: str = "center"
    data_labels_number_format: str = "0.0"
    data_labels_font_size: float = 5

    def validate_inputs(self) -> None:
        """
        Validate pie chart input data.

        Raises
        ------
        ValueError
            If categories or values are empty, or category/value lengths are
            inconsistent.
        """
        self.validate_base_inputs()

        if not self.categories:
            raise ValueError("categories cannot be empty.")

        if not self.values:
            raise ValueError("values cannot be empty.")

        if len(self.categories) != len(self.values):
            raise ValueError(
                f"categories and values must have the same length. "
                f"Got len(categories)={len(self.categories)} and "
                f"len(values)={len(self.values)}."
            )

    def build_chart_data(self) -> CategoryChartData:
        """
        Build the chart data object used by python-pptx.

        Returns
        -------
        CategoryChartData
            Chart data object ready to be inserted into PowerPoint.
        """
        chart_data = CategoryChartData()
        chart_data.categories = self.categories
        chart_data.add_series(self.series_name, self.values)

        return chart_data

    def apply_slice_colors(self, chart) -> None:
        """
        Apply fill colors to each pie slice.

        Parameters
        ----------
        chart : pptx.chart.chart.Chart
            Chart object to format.
        """
        series = chart.series[0]

        for index, point in enumerate(series.points):
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = hex_to_rgb(
                self.colors[index % len(self.colors)]
            )

    def chart(self):
        """
        Insert the pie chart into the selected PowerPoint slide.

        Returns
        -------
        pptx.chart.chart.Chart
            Created PowerPoint chart object.
        """
        self.validate_inputs()

        chart_data = self.build_chart_data()
        slide = self.get_slide()
        x, y, width, height = self.get_chart_position()

        chart = slide.shapes.add_chart(
            XL_CHART_TYPE.PIE,
            x,
            y,
            width,
            height,
            chart_data,
        ).chart

        self.apply_title(chart)
        self.apply_legend(chart)
        self.apply_plot_data_labels(
            chart=chart,
            show_labels=self.data_labels_show,
            label_position=self.data_labels_position,
            number_format=self.data_labels_number_format,
            font_size=self.data_labels_font_size,
        )
        self.apply_slice_colors(chart)

        return chart


@dataclass
class BarChart(BasePowerPointChart):
    """
    Create a bar or column chart in a PowerPoint slide.

    This class supports clustered, stacked and 100% stacked bar or column
    charts.

    Parameters
    ----------
    series_names : list[str]
        Names of the chart series.
    x_values : list[list]
        Category labels for each series. All series must share the same
        categories.
    y_values : list[list[float]]
        Numeric values for each series.
    colors : list[str]
        Hexadecimal colors applied to each bar or column series.

    Methods
    -------
    chart(chart_type="COLUMN_CLUSTERED")
        Insert the bar or column chart into the selected PowerPoint slide.

    Returns
    -------
    pptx.chart.chart.Chart
        The created chart object when calling chart().
    """

    series_names: list[str] = field(default_factory=list)
    x_values: list[list] = field(default_factory=list)
    y_values: list[list[float]] = field(default_factory=list)
    colors: list[str] = field(default_factory=lambda: PALETA_COLORES)

    title_show: bool = True

    data_labels_show: bool = False
    data_labels_position: str = "center"
    data_labels_number_format: str = "0.0"
    data_labels_font_size: float = 5

    x_axis_title_show: bool = False
    x_axis_title: str = ""
    x_axis_font_size: float = 6
    x_axis_number_format: str = "0.00"
    x_axis_position: str = "center"

    y_axis_title_show: bool = False
    y_axis_title: str = ""
    y_axis_font_size: float = 6
    y_axis_gridlines_show: bool = False
    y_axis_number_format: str = "0.00"
    y_axis_position: str = "center"
    y_axis_minimum_adjustment: float = 10.0
    y_axis_maximum_adjustment: float = 10.0

    def validate_inputs(self, chart_type: str) -> None:
        """
        Validate bar chart input data.

        Parameters
        ----------
        chart_type : str
            Chart type key to validate.

        Raises
        ------
        ValueError
            If data is missing, chart type is invalid or series lengths are
            inconsistent.
        """
        self.validate_base_inputs()

        validate_option(
            value=chart_type,
            options=BAR_CHART_TYPES,
            parameter_name="chart_type",
        )

        if not self.series_names:
            raise ValueError("series_names cannot be empty.")

        if not self.x_values:
            raise ValueError("x_values cannot be empty.")

        if not self.y_values:
            raise ValueError("y_values cannot be empty.")

        if not (
            len(self.series_names)
            == len(self.x_values)
            == len(self.y_values)
        ):
            raise ValueError(
                "series_names, x_values and y_values must have the same "
                "number of series."
            )

        reference_categories = self.x_values[0]

        for index, series_name in enumerate(self.series_names):
            if len(self.x_values[index]) != len(self.y_values[index]):
                raise ValueError(
                    f"Series '{series_name}' has inconsistent lengths: "
                    f"len(x_values)={len(self.x_values[index])}, "
                    f"len(y_values)={len(self.y_values[index])}."
                )

            if self.x_values[index] != reference_categories:
                raise ValueError(
                    "All bar chart series must share the same x-axis categories."
                )

    def build_chart_data(self) -> CategoryChartData:
        """
        Build the chart data object used by python-pptx.

        Returns
        -------
        CategoryChartData
            Chart data object ready to be inserted into PowerPoint.
        """
        chart_data = CategoryChartData()
        chart_data.categories = self.x_values[0]

        for series_name, values in zip(self.series_names, self.y_values):
            chart_data.add_series(series_name, values)

        return chart_data

    def apply_series_format(self, chart) -> None:
        """
        Apply fill colors to each bar or column series.

        Parameters
        ----------
        chart : pptx.chart.chart.Chart
            Chart object to format.
        """
        for index, series in enumerate(chart.series):
            series.invert_if_negative = False
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = hex_to_rgb(
                self.colors[index % len(self.colors)]
            )

    def chart(self, chart_type: str = "COLUMN_CLUSTERED"):
        """
        Insert the bar or column chart into the selected PowerPoint slide.

        Parameters
        ----------
        chart_type : str, default "COLUMN_CLUSTERED"
            Chart type key. Available options are defined in BAR_CHART_TYPES.

        Returns
        -------
        pptx.chart.chart.Chart
            Created PowerPoint chart object.
        """
        self.validate_inputs(chart_type=chart_type)

        chart_data = self.build_chart_data()
        slide = self.get_slide()
        x, y, width, height = self.get_chart_position()

        chart = slide.shapes.add_chart(
            BAR_CHART_TYPES[chart_type],
            x,
            y,
            width,
            height,
            chart_data,
        ).chart

        y_minimum, y_maximum = calculate_axis_bounds(
            values=flatten_nested_values(self.y_values),
            minimum_adjustment_factor=self.y_axis_minimum_adjustment,
            maximum_adjustment_factor=self.y_axis_maximum_adjustment,
        )

        self.apply_title(chart)
        self.apply_legend(chart)
        self.apply_plot_data_labels(
            chart=chart,
            show_labels=self.data_labels_show,
            label_position=self.data_labels_position,
            number_format=self.data_labels_number_format,
            font_size=self.data_labels_font_size,
        )
        self.apply_value_axis(
            chart=chart,
            title_show=self.y_axis_title_show,
            title=self.y_axis_title,
            font_size=self.y_axis_font_size,
            number_format=self.y_axis_number_format,
            show_gridlines=self.y_axis_gridlines_show,
            tick_label_position=self.y_axis_position,
            minimum_scale=y_minimum,
            maximum_scale=y_maximum,
        )
        self.apply_category_axis(
            chart=chart,
            title_show=self.x_axis_title_show,
            title=self.x_axis_title,
            font_size=self.x_axis_font_size,
            number_format=self.x_axis_number_format,
            tick_label_position=self.x_axis_position,
        )
        self.apply_series_format(chart)

        return chart


@dataclass
class BubbleChart(BasePowerPointChart):
    """
    Create a bubble chart in a PowerPoint slide.

    Each series requires x-values, y-values and bubble sizes.

    Parameters
    ----------
    series_names : list[str]
        Names of the chart series.
    x_values : list[list[float]]
        X-axis values for each series.
    y_values : list[list[float]]
        Y-axis values for each series.
    bubble_sizes : list[list[float]]
        Bubble size values for each series.
    colors : list[str]
        Hexadecimal colors applied to each bubble series.

    Methods
    -------
    chart()
        Insert the bubble chart into the selected PowerPoint slide.

    Returns
    -------
    pptx.chart.chart.Chart
        The created chart object when calling chart().
    """

    series_names: list[str] = field(default_factory=list)
    x_values: list[list[float]] = field(default_factory=list)
    y_values: list[list[float]] = field(default_factory=list)
    bubble_sizes: list[list[float]] = field(default_factory=list)
    colors: list[str] = field(default_factory=lambda: PALETA_COLORES)

    x_axis_title_show: bool = False
    x_axis_title: str = ""
    x_axis_font_size: float = 6
    x_axis_number_format: str = "0.00"
    x_axis_minimum_adjustment: float = 5.0
    x_axis_maximum_adjustment: float = 5.0

    y_axis_title_show: bool = False
    y_axis_title: str = ""
    y_axis_font_size: float = 6
    y_axis_gridlines_show: bool = False
    y_axis_number_format: str = "0.00"
    y_axis_minimum_adjustment: float = 5.0
    y_axis_maximum_adjustment: float = 5.0

    def validate_inputs(self) -> None:
        """
        Validate bubble chart input data.

        Raises
        ------
        ValueError
            If required series data is missing or lengths are inconsistent.
        """
        self.validate_base_inputs()

        if not self.series_names:
            raise ValueError("series_names cannot be empty.")

        if not self.x_values:
            raise ValueError("x_values cannot be empty.")

        if not self.y_values:
            raise ValueError("y_values cannot be empty.")

        if not self.bubble_sizes:
            raise ValueError("bubble_sizes cannot be empty.")

        if not (
            len(self.series_names)
            == len(self.x_values)
            == len(self.y_values)
            == len(self.bubble_sizes)
        ):
            raise ValueError(
                "series_names, x_values, y_values and bubble_sizes must have "
                "the same number of series."
            )

        for index, series_name in enumerate(self.series_names):
            if not (
                len(self.x_values[index])
                == len(self.y_values[index])
                == len(self.bubble_sizes[index])
            ):
                raise ValueError(
                    f"Series '{series_name}' has inconsistent lengths: "
                    f"len(x_values)={len(self.x_values[index])}, "
                    f"len(y_values)={len(self.y_values[index])}, "
                    f"len(bubble_sizes)={len(self.bubble_sizes[index])}."
                )

    def build_chart_data(self) -> BubbleChartData:
        """
        Build the bubble chart data object used by python-pptx.

        Returns
        -------
        BubbleChartData
            Chart data object ready to be inserted into PowerPoint.
        """
        chart_data = BubbleChartData()

        for series_name, x_series, y_series, size_series in zip(
            self.series_names,
            self.x_values,
            self.y_values,
            self.bubble_sizes,
        ):
            series = chart_data.add_series(series_name)

            for x_value, y_value, bubble_size in zip(
                x_series,
                y_series,
                size_series,
            ):
                series.add_data_point(x_value, y_value, bubble_size)

        return chart_data

    def apply_series_format(self, chart) -> None:
        """
        Apply bubble fill colors and remove bubble borders.

        Parameters
        ----------
        chart : pptx.chart.chart.Chart
            Chart object to format.
        """
        for index, series in enumerate(chart.series):
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = hex_to_rgb(
                self.colors[index % len(self.colors)]
            )
            series.format.line.fill.background()

    def chart(self):
        """
        Insert the bubble chart into the selected PowerPoint slide.

        Returns
        -------
        pptx.chart.chart.Chart
            Created PowerPoint chart object.
        """
        self.validate_inputs()

        chart_data = self.build_chart_data()
        slide = self.get_slide()
        x, y, width, height = self.get_chart_position()

        chart = slide.shapes.add_chart(
            XL_CHART_TYPE.BUBBLE,
            x,
            y,
            width,
            height,
            chart_data,
        ).chart

        x_minimum, x_maximum = calculate_axis_bounds(
            values=flatten_nested_values(self.x_values),
            minimum_adjustment_factor=self.x_axis_minimum_adjustment,
            maximum_adjustment_factor=self.x_axis_maximum_adjustment,
        )
        y_minimum, y_maximum = calculate_axis_bounds(
            values=flatten_nested_values(self.y_values),
            minimum_adjustment_factor=self.y_axis_minimum_adjustment,
            maximum_adjustment_factor=self.y_axis_maximum_adjustment,
        )

        self.apply_title(chart)
        self.apply_value_axis(
            chart=chart,
            title_show=self.y_axis_title_show,
            title=self.y_axis_title,
            font_size=self.y_axis_font_size,
            number_format=self.y_axis_number_format,
            show_gridlines=self.y_axis_gridlines_show,
            minimum_scale=y_minimum,
            maximum_scale=y_maximum,
        )
        self.apply_category_axis(
            chart=chart,
            title_show=self.x_axis_title_show,
            title=self.x_axis_title,
            font_size=self.x_axis_font_size,
            number_format=self.x_axis_number_format,
            minimum_scale=x_minimum,
            maximum_scale=x_maximum,
        )
        self.apply_legend(chart)
        self.apply_series_format(chart)

        return chart


@dataclass
class WaterfallChart(BasePowerPointChart):
    """
    Create a waterfall chart in PowerPoint using a stacked column chart.

    Since python-pptx does not expose a native waterfall chart type, this class
    builds a waterfall visualization using hidden base series and visible
    increase, decrease and total series.

    Parameters
    ----------
    categories : list[str]
        Category labels shown on the x-axis.
    values : list[float]
        Numeric values for each waterfall step. Values are expected in decimal
        format when using percentage labels, for example 0.012 means 1.2%.
    bar_types : list[str]
        Bar type for each category. Use "total" to mark total bars and an empty
        string or any other value for regular contribution bars.

    Methods
    -------
    chart()
        Insert the waterfall chart into the selected PowerPoint slide.

    Returns
    -------
    pptx.chart.chart.Chart
        The created chart object when calling chart().
    """

    categories: list[str] = field(default_factory=list)
    values: list[float] = field(default_factory=list)
    bar_types: list[str] = field(default_factory=list)

    increase_color: RGBColor = RGBColor(192, 51, 36)
    decrease_color: RGBColor = RGBColor(18, 43, 95)
    total_color: RGBColor = RGBColor(61, 120, 216)

    title_show: bool = True
    title_font_size: float = 9

    data_labels_show: bool = False
    data_labels_position: str = "inside_base"
    data_labels_number_format: str = "0.00%"
    data_labels_font_size: float = 8

    x_axis_title_show: bool = False
    x_axis_title: str = ""
    x_axis_position: str = "low"
    x_axis_font_size: float = 8
    x_axis_number_format: str = "0.0"

    y_axis_title_show: bool = False
    y_axis_title: str = ""
    y_axis_font_size: float = 8
    y_axis_number_format: str = "0.00%"
    y_axis_position: str = "low"
    y_axis_gridlines_show: bool = False
    y_axis_minimum_adjustment: float = 20
    y_axis_maximum_adjustment: float = 20

    reset_running_total_except_last: bool = True

    def validate_inputs(self) -> None:
        """
        Validate waterfall chart input data.

        Raises
        ------
        ValueError
            If required data is empty, lengths are inconsistent or data label
            position is invalid.
        """
        self.validate_base_inputs()

        if not self.categories:
            raise ValueError("categories cannot be empty.")

        if not self.values:
            raise ValueError("values cannot be empty.")

        if not self.bar_types:
            raise ValueError("bar_types cannot be empty.")

        if not (
            len(self.categories)
            == len(self.values)
            == len(self.bar_types)
        ):
            raise ValueError(
                "categories, values and bar_types must have the same length."
            )

        validate_option(
            value=self.data_labels_position,
            options=LABEL_POSITION,
            parameter_name="data_labels_position",
        )

    def build_waterfall_series(
        self,
    ) -> tuple[dict[str, list[float]], list[tuple[str, float] | None]]:
        """
        Build stacked-column series needed to emulate a waterfall chart.

        Returns
        -------
        tuple[dict[str, list[float]], list[tuple[str, float] | None]]
            Internal series dictionary and label target metadata.
        """
        series = {
            "BasePositive": [],
            "BaseNegative": [],
            "IncreasePositive": [],
            "IncreaseNegative": [],
            "DecreasePositive": [],
            "DecreaseNegative": [],
            "TotalPositive": [],
            "TotalNegative": [],
            "LabelCarrier": [],
        }

        label_targets: list[tuple[str, float] | None] = [None] * len(self.values)

        total_indexes = [
            index
            for index, bar_type in enumerate(self.bar_types)
            if (bar_type or "").lower() == "total"
        ]
        last_total_index = total_indexes[-1] if total_indexes else None

        running_value = 0.0

        for index, value in enumerate(self.values):
            bar_type = (self.bar_types[index] or "").lower()

            base_positive = 0.0
            base_negative = 0.0
            increase_positive = 0.0
            increase_negative = 0.0
            decrease_positive = 0.0
            decrease_negative = 0.0
            total_positive = 0.0
            total_negative = 0.0

            if bar_type == "total":
                if value >= 0:
                    total_positive = value
                    label_targets[index] = ("TotalPositive", value)
                else:
                    total_negative = value
                    label_targets[index] = ("TotalNegative", value)

                if (
                    self.reset_running_total_except_last
                    and index != last_total_index
                ):
                    running_value = value

            else:
                start_value = running_value
                end_value = running_value + value
                low_value = min(start_value, end_value)
                high_value = max(start_value, end_value)
                is_increase = end_value >= start_value

                if low_value >= 0:
                    base_positive = low_value
                    segment = high_value - low_value

                    if is_increase:
                        increase_positive = segment
                        label_targets[index] = ("IncreasePositive", value)
                    else:
                        decrease_positive = segment
                        label_targets[index] = ("DecreasePositive", value)

                elif high_value <= 0:
                    base_negative = high_value
                    segment = low_value - high_value

                    if is_increase:
                        increase_negative = segment
                        label_targets[index] = ("IncreaseNegative", value)
                    else:
                        decrease_negative = segment
                        label_targets[index] = ("DecreaseNegative", value)

                else:
                    if is_increase:
                        increase_positive = high_value
                        increase_negative = low_value
                        label_targets[index] = (
                            "IncreasePositive"
                            if end_value >= 0
                            else "IncreaseNegative",
                            value,
                        )
                    else:
                        decrease_positive = high_value
                        decrease_negative = low_value
                        label_targets[index] = (
                            "DecreasePositive"
                            if end_value >= 0
                            else "DecreaseNegative",
                            value,
                        )

                running_value = end_value

            label_carrier = (
                increase_positive
                + increase_negative
                + decrease_positive
                + decrease_negative
                + total_positive
                + total_negative
            )

            series["BasePositive"].append(base_positive)
            series["BaseNegative"].append(base_negative)
            series["IncreasePositive"].append(increase_positive)
            series["IncreaseNegative"].append(increase_negative)
            series["DecreasePositive"].append(decrease_positive)
            series["DecreaseNegative"].append(decrease_negative)
            series["TotalPositive"].append(total_positive)
            series["TotalNegative"].append(total_negative)
            series["LabelCarrier"].append(label_carrier)

        return series, label_targets

    def build_chart_data(self, series: dict[str, list[float]]) -> CategoryChartData:
        """
        Build the waterfall chart data object.

        Parameters
        ----------
        series : dict[str, list[float]]
            Internal waterfall series dictionary.

        Returns
        -------
        CategoryChartData
            Chart data object ready to be inserted into PowerPoint.
        """
        chart_data = CategoryChartData()
        chart_data.categories = self.categories

        for series_name in WATERFALL_SERIES_ORDER:
            chart_data.add_series(series_name, series[series_name])

        return chart_data

    def calculate_waterfall_axis_bounds(self) -> tuple[float, float]:
        """
        Calculate adjusted y-axis bounds for the waterfall chart.

        Returns
        -------
        tuple[float, float]
            Adjusted minimum and maximum y-axis values.
        """
        running_values = [0.0]
        running_value = 0.0

        total_indexes = [
            index
            for index, bar_type in enumerate(self.bar_types)
            if (bar_type or "").lower() == "total"
        ]
        last_total_index = total_indexes[-1] if total_indexes else None

        for index, value in enumerate(self.values):
            bar_type = (self.bar_types[index] or "").lower()

            if bar_type == "total":
                running_values.append(value)

                if (
                    self.reset_running_total_except_last
                    and index != last_total_index
                ):
                    running_value = value
            else:
                running_value += value
                running_values.append(running_value)

        return calculate_axis_bounds(
            values=running_values,
            minimum_adjustment_factor=self.y_axis_minimum_adjustment,
            maximum_adjustment_factor=self.y_axis_maximum_adjustment,
        )

    def apply_waterfall_series_format(self, chart) -> None:
        """
        Apply colors and hidden-series formatting to the waterfall chart.

        Parameters
        ----------
        chart : pptx.chart.chart.Chart
            Chart object to format.
        """
        chart.series[0].format.fill.background()
        chart.series[1].format.fill.background()

        label_carrier = chart.series[8]
        label_carrier.format.fill.background()
        label_carrier.format.line.fill.background()

        for series in chart.series:
            series.invert_if_negative = False

        for index in (2, 3):
            chart.series[index].format.fill.solid()
            chart.series[index].format.fill.fore_color.rgb = self.increase_color

        for index in (4, 5):
            chart.series[index].format.fill.solid()
            chart.series[index].format.fill.fore_color.rgb = self.decrease_color

        for index in (6, 7):
            chart.series[index].format.fill.solid()
            chart.series[index].format.fill.fore_color.rgb = self.total_color

    def apply_custom_data_labels(
        self,
        chart,
        label_targets: list[tuple[str, float] | None],
    ) -> None:
        """
        Apply custom value labels to the invisible label carrier series.

        Parameters
        ----------
        chart : pptx.chart.chart.Chart
            Chart object to format.
        label_targets : list[tuple[str, float] | None]
            Metadata returned by build_waterfall_series.
        """
        if not self.data_labels_show:
            return

        label_series = chart.series[8]
        label_series.has_data_labels = True

        for index, point in enumerate(label_series.points):
            target = label_targets[index]

            if target is None:
                continue

            _, value = target

            label = point.data_label
            label.show_value = False
            label.position = LABEL_POSITION[self.data_labels_position]

            text_frame = label.text_frame
            text_frame.clear()
            text_frame.auto_size = MSO_AUTO_SIZE.NONE
            text_frame.word_wrap = False

            paragraph = text_frame.paragraphs[0]
            run = paragraph.add_run()

            if self.data_labels_number_format == "0.00%":
                run.text = f"{value * 100:.2f}%"
            elif self.data_labels_number_format == "0.0%":
                run.text = f"{value * 100:.1f}%"
            elif self.data_labels_number_format == "0%":
                run.text = f"{value * 100:.0f}%"
            else:
                run.text = str(value)

            run.font.size = Pt(self.data_labels_font_size)
            run.font.name = self.font_name

    def chart(self):
        """
        Insert the waterfall chart into the selected PowerPoint slide.

        Returns
        -------
        pptx.chart.chart.Chart
            Created PowerPoint chart object.
        """
        self.validate_inputs()

        series, label_targets = self.build_waterfall_series()
        chart_data = self.build_chart_data(series)

        slide = self.get_slide()

        chart = slide.shapes.add_chart(
            XL_CHART_TYPE.COLUMN_STACKED,
            Cm(self.position_x),
            Cm(self.position_y),
            Cm(self.width),
            Cm(self.height),
            chart_data,
        ).chart

        y_minimum, y_maximum = self.calculate_waterfall_axis_bounds()

        self.apply_waterfall_series_format(chart)
        self.apply_title(chart)
        self.apply_value_axis(
            chart=chart,
            title_show=self.y_axis_title_show,
            title=self.y_axis_title,
            font_size=self.y_axis_font_size,
            number_format=self.y_axis_number_format,
            show_gridlines=self.y_axis_gridlines_show,
            tick_label_position=self.y_axis_position,
            minimum_scale=y_minimum,
            maximum_scale=y_maximum,
        )
        self.apply_category_axis(
            chart=chart,
            title_show=self.x_axis_title_show,
            title=self.x_axis_title,
            font_size=self.x_axis_font_size,
            number_format=self.x_axis_number_format,
            tick_label_position=self.x_axis_position,
        )
        self.apply_custom_data_labels(
            chart=chart,
            label_targets=label_targets,
        )

        return chart