# graph.py

"""
DataFrame-centered interface for PowerPoint charts.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd
from pptx import Presentation
from pptx.chart.chart import Chart
from pptx.slide import Slide

from .metadata import GraphPptMetaData


class GraphPpt:
    """
    Create and format native PowerPoint charts from a pandas DataFrame.

    GraphPpt provides a chainable interface similar to GraphMtplt. Chart
    creation and formatting methods modify the current object and return
    ``self``.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame used as the source for charts.
    presentation : pptx.Presentation
        PowerPoint presentation where charts will be inserted.
    slide : int, default 0
        Position of the active slide in the presentation.
    font_name : str, default "Inter"
        Default font family used by chart elements.

    Examples
    --------
    >>> graph = GraphPpt(
    ...     data=df,
    ...     presentation=prs,
    ...     slide=0,
    ... )
    """

    def __init__(
        self,
        data: pd.DataFrame,
        presentation: Presentation,
        slide: int = 0,
        font_name: str = "Inter",
    ) -> None:
        self.data = data
        self.presentation = presentation
        self.slide_index = slide
        self.font_name = font_name

        self.metadata = GraphPptMetaData()

        self._validate_data()
        self._validate_presentation()
        self._validate_slide_index()

    def _validate_data(self) -> None:
        """
        Validate the graph DataFrame.
        """

        if not isinstance(self.data, pd.DataFrame):
            raise TypeError(
                "data must be a pandas DataFrame. "
                f"Received {type(self.data).__name__}."
            )

    def _validate_presentation(self) -> None:
        """
        Validate the PowerPoint presentation.
        """

        if self.presentation is None:
            raise ValueError("presentation cannot be None.")

        if not isinstance(self.presentation, Presentation):
            raise TypeError(
                "presentation must be a pptx.Presentation object."
            )

    def _validate_slide_index(
        self,
        slide_index: int | None = None,
    ) -> None:
        """
        Validate a slide position.

        Parameters
        ----------
        slide_index : int, optional
            Slide position to validate. If omitted, the current active slide
            position is used.
        """

        index = (
            self.slide_index
            if slide_index is None
            else slide_index
        )

        if not isinstance(index, int):
            raise TypeError("slide must be an integer.")

        if index < 0:
            raise ValueError(
                "slide must be greater than or equal to zero."
            )

        number_of_slides = len(self.presentation.slides)

        if index >= number_of_slides:
            raise IndexError(
                f"slide {index} is out of range. "
                f"The presentation contains {number_of_slides} slides."
            )

    @property
    def df(self) -> pd.DataFrame:
        """
        Return the graph DataFrame.

        Returns
        -------
        pandas.DataFrame
            DataFrame used by the graph.
        """

        return self.data

    @property
    def slide(self) -> Slide:
        """
        Return the active PowerPoint slide.

        Returns
        -------
        pptx.slide.Slide
            Active slide.
        """

        self._validate_slide_index()

        return self.presentation.slides[self.slide_index]

    @property
    def chart(self) -> Chart | None:
        """
        Return the active native PowerPoint chart.

        Returns
        -------
        pptx.chart.chart.Chart or None
            Active chart, if one has been created.
        """

        return self.metadata.chart

    def _set_chart(
        self,
        chart: Chart,
    ) -> GraphPpt:
        """
        Register a native PowerPoint chart as the active chart.

        Parameters
        ----------
        chart : pptx.chart.chart.Chart
            Native PowerPoint chart.

        Returns
        -------
        GraphPpt
            Current graph object.
        """

        self.metadata.chart = chart

        return self

    def _require_chart(self) -> Chart:
        """
        Return the active chart or raise an informative error.

        Returns
        -------
        pptx.chart.chart.Chart
            Active PowerPoint chart.

        Raises
        ------
        RuntimeError
            If a chart has not been created.
        """

        if self.metadata.chart is None:
            raise RuntimeError(
                "No active chart is available. "
                "Create a chart using graph_line(), graph_bar(), "
                "graph_pie(), graph_bubble() or graph_waterfall() "
                "before applying formatting."
            )

        return self.metadata.chart

    def use_slide(
        self,
        slide: int,
    ) -> GraphPpt:
        """
        Change the active PowerPoint slide.

        Parameters
        ----------
        slide : int
            Position of the new active slide.

        Returns
        -------
        GraphPpt
            Current graph object.
        """

        self._validate_slide_index(slide)

        self.slide_index = slide
        self.metadata.clear_chart()

        return self

    def copy_data(
        self,
        deep: bool = True,
    ) -> GraphPpt:
        """
        Copy the underlying DataFrame.

        Parameters
        ----------
        deep : bool, default True
            Whether to create a deep DataFrame copy.

        Returns
        -------
        GraphPpt
            Current graph object.
        """

        self.data = self.data.copy(deep=deep)

        return self

    def pipe(
        self,
        function: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Apply a callable to the current GraphPpt object.

        Parameters
        ----------
        function : callable
            Function receiving the GraphPpt object as its first argument.
        *args
            Additional positional arguments.
        **kwargs
            Additional keyword arguments.

        Returns
        -------
        Any
            Result returned by the callable. If the callable returns None,
            the current GraphPpt object is returned.
        """

        result = function(
            self,
            *args,
            **kwargs,
        )

        if result is None:
            return self

        return result

    def tap(
        self,
        function: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> GraphPpt:
        """
        Execute a callable without interrupting method chaining.

        Parameters
        ----------
        function : callable
            Function receiving the GraphPpt object as its first argument.
        *args
            Additional positional arguments.
        **kwargs
            Additional keyword arguments.

        Returns
        -------
        GraphPpt
            Current graph object.
        """

        function(
            self,
            *args,
            **kwargs,
        )

        return self