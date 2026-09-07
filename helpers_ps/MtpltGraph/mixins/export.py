from __future__ import annotations
import io
import matplotlib.pyplot as plt
from ..config import buffers
from typing import Self
import os

class ExportMixin:
    """
    Display and export utilities.

    This mixin provides helpers for accessing, exporting, and rendering
    generated charts. Figures can be returned directly, exported to
    in-memory buffers for downstream workflows, or written to disk as
    image files.

    Features
    --------
    - Access to the current Matplotlib figure.
    - Export charts to PNG buffers.
    - Store exported images in shared buffer registries.
    - Render charts directly to disk.
    - Automatic cleanup of figure metadata after export.

    Notes
    -----
    Exported images are generated using the current figure state at the
    time the export method is called.
    """

    def show(self: Self) -> Self:
        """
        Return the active Matplotlib figure.

        This method provides access to the currently active figure and is
        typically used in notebook environments, custom display workflows,
        or when additional figure-level operations must be performed after
        chart construction.

        Returns
        -------
        matplotlib.figure.Figure
            The active Matplotlib figure.

        Raises
        ------
        RuntimeError
            If no figure has been created.

        Examples
        --------
        Display a chart in a notebook:

        >>> (
        ...     graph
        ...     .graph_line(series)
        ...     .show()
        ... )

        Access the underlying figure:

        >>> fig = (
        ...     graph
        ...     .graph_line(series)
        ...     .show()
        ... )
        """
        
        if self._fig:
            return self._fig

        raise RuntimeError("Plot must exist")


    def save(
        self,
        dir: dict | None = None,
        name: str = "graph_1",
        dpi: int = 400,
        reset_buffers: bool = True
    ) -> io.BytesIO | None:
        """
        Export the active figure to an in-memory PNG buffer.

        This method saves the current chart as a PNG image stored inside a
        `BytesIO` object. The resulting buffer can be returned directly or
        stored in a shared dictionary for later use by PowerPoint, Word,
        dashboards, reporting pipelines, or other export workflows.

        Parameters
        ----------
        dir : dict or None, optional
            Dictionary-like object where the image buffer will be stored.
            When omitted, the image buffer is returned directly.

        name : str, default "graph_1"
            Key assigned to the exported image buffer.

        dpi : int, default 400
            Export resolution.

        reset_buffers : bool, default True
            Whether internal figure, axis, and metadata references should
            be reset after the export operation.

        Returns
        -------
        io.BytesIO or None
            Returns an image buffer when `dir` is None. Otherwise the image
            buffer is stored in `dir[name]` and None is returned.

        Notes
        -----
        The Matplotlib figure is closed after export to free memory.

        Examples
        --------
        Return a buffer directly:

        >>> buffer = (
        ...     graph
        ...     .graph_line(series)
        ...     .save()
        ... )

        Store into a buffer registry:

        >>> (
        ...     graph
        ...     .graph_line(series)
        ...     .save(
        ...         dir=buffers,
        ...         name="performance_chart"
        ...     )
        ... )

        Export at higher resolution:

        >>> (
        ...     graph
        ...     .graph_line(series)
        ...     .save(
        ...         dpi=600
        ...     )
        ... )
        """
        
        buf = io.BytesIO()
        self._fig.savefig(buf, format="png", dpi=dpi)   # use figure-level save
        buf.seek(0)

        if dir is not None:
            dir[name] = buf
        
        plt.close(self._fig)

        if reset_buffers:
            self._reset_figure_metadata()

        if dir is None:
            return buf

        else:
            return None


    def render(
        self,
        name: str,
        dir: str,
        dpi: int = 400
    ) -> None:
        """
        Render the active chart to a PNG file on disk.

        This method exports the current figure and writes it directly to the
        specified directory as a PNG file. It is a convenience wrapper around
        `save()` when a physical image file is required.

        Parameters
        ----------
        name : str
            Output file name without extension.

        dir : str
            Directory where the PNG file should be created.

        dpi : int, default 400
            Export resolution.

        Returns
        -------
        None
            The image is written directly to disk.

        Examples
        --------
        Save a chart to a local directory:

        >>> (
        ...     graph
        ...     .graph_line(series)
        ...     .render(
        ...         name="performance_chart",
        ...         dir="C:/Charts"
        ...     )
        ... )

        Export a high-resolution image:

        >>> (
        ...     graph
        ...     .graph_line(series)
        ...     .render(
        ...         name="report_chart",
        ...         dir="C:/Reports",
        ...         dpi=600
        ...     )
        ... )
        """

        buf = self.save(dpi=dpi)
        buf.seek(0)

        file_path = os.path.join(dir, f"{name}.png")
        with open(file_path, "wb") as f:
            f.write(buf.getvalue())

        return None