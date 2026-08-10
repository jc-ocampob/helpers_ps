from __future__ import annotations
import io
import matplotlib.pyplot as plt
from ..config import buffers
from typing import Self

class ExportMixin:
    """
    Provide display and export helpers.
    """

    def show(self: Self) -> Self:
        """
        Display the active Matplotlib figure and keep the chain alive.

        Returns
        -------
        Graph_base
            The current graph object.
        """
        if self._fig:
            return self._fig

        raise RuntimeError("Plot must exist")


    def save(
        self,
        dir: dict = buffers,
        name: str = "graph_1",
        dpi: int = 400,
        reset_buffers: bool = True
    ) -> Self:
        """
        Save the active figure into an in-memory PNG buffer.

        This method exports the current figure as a PNG image into a `BytesIO`
        buffer and stores it in the provided dictionary-like object using `name`
        as the key. It is useful when charts need to be passed to PowerPoint,
        reports, dashboards, or other downstream workflows without writing files
        to disk.

        Parameters
        ----------
        dir : dict, default buffers
            Dictionary-like object where the image buffer will be stored.
        name : str, default "graph_1"
            Key assigned to the saved image buffer.
        dpi : int, default 400
            Resolution used when exporting the figure.
        reset_buffers : bool, default True
            Whether to reset internal figure, axis, layout, and metadata references
            after saving.

        Returns
        -------
        None
            The image buffer is stored in `dir[name]`.

        Notes
        -----
        The Matplotlib figure is closed after being saved.
        """
        buf = io.BytesIO()
        self._fig.savefig(buf, format="png", dpi=dpi)   # use figure-level save
        buf.seek(0)
        dir[name] = buf
        plt.close(self._fig)

        if reset_buffers:
            self._reset_figure_metadata()

        return self
