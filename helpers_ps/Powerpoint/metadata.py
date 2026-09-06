# metadata.py

"""
Metadata objects used by PowerPoint graphs.
"""

from __future__ import annotations

from dataclasses import dataclass

from pptx.chart.chart import Chart


@dataclass
class GraphPptMetaData:
    """
    Store the mutable state of a GraphPpt object.

    Parameters
    ----------
    chart : Chart, optional
        Active native PowerPoint chart.
    source_shape : object, optional
        Text box containing the chart source.
    title_shape : object, optional
        External title shape, when applicable.
    subtitle_shape : object, optional
        External subtitle shape, when applicable.
    note_shape : object, optional
        Text box containing an explanatory note.
    """

    chart: Chart | None = None
    source_shape: object | None = None
    title_shape: object | None = None
    subtitle_shape: object | None = None
    note_shape: object | None = None

    def clear_chart(self) -> None:
        """
        Clear the active chart and its associated shapes.
        """

        self.chart = None
        self.source_shape = None
        self.title_shape = None
        self.subtitle_shape = None
        self.note_shape = None