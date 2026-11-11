from __future__ import annotations

import io
import warnings
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Self

import matplotlib
import numpy as np

from ..models import GridLayout, Panel
from ..rendering.browser import build_document
from ..rendering.cache import make_key
from ..rendering.images import array_to_rgb, rasterize_image
from .base import SheetBase

_FORMATS = {"png", "pdf", "svg", "jpg", "jpeg"}


class OutputMixin(SheetBase):
    """Render, preview and export the sheet."""

    # ------------------------------------------------------------------
    # Layout resolution
    # ------------------------------------------------------------------

    def _resolve_grid(self) -> GridLayout:
        """
        Return the grid of the sheet.

        An explicit layout is used as it is (panels added after it was set
        are left out, with a warning); otherwise the panels are placed in
        creation order according to ``nrows`` / ``ncols``.
        """
        if not self._panels:
            raise ValueError(
                "The sheet has no panels. Add one with add_table() or "
                "add_image()."
            )

        if self._mosaic is not None:
            grid = GridLayout(self._mosaic, self._width_ratios)
            left_out = [
                name for name in self.panel_names if name not in grid.spans
            ]
            if left_out:
                warnings.warn(
                    f"Panels not placed in the layout and left out: "
                    f"{left_out}.",
                    stacklevel=3,
                )
            return grid

        nrows, ncols = self._shape or (None, None)
        return GridLayout.filled(
            self.panel_names, nrows, ncols, self._width_ratios
        )

    def _visible_panels(self, grid: GridLayout) -> list[Panel]:
        by_name = {panel.name: panel for panel in self._panels}
        return [by_name[name] for name in grid.spans]

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _rasterize(self, panels: Iterable[Panel]) -> dict[str, np.ndarray]:
        """
        Return the RGB image of every given panel.

        Tables are looked up in the cache by content. Everything that is
        missing is rendered in a single batch (one browser launch).
        """
        style = self._style
        token = getattr(
            self._renderer, "cache_token", type(self._renderer).__qualname__
        )

        images: dict[str, np.ndarray] = {}
        key_of: dict[str, str] = {}
        pending: dict[str, str] = {}

        for panel in panels:
            if panel.kind == "image":
                images[panel.name] = rasterize_image(panel.source, style.dpi)
                continue

            document = build_document(
                panel.build_styler().to_html(),
                font_px=style.table_font_px,
                zebra=style.zebra,
            )
            key = make_key(token, style.dpi, document)
            key_of[panel.name] = key

            cached = self._cache.get(key)
            if cached is not None:
                images[panel.name] = cached
            else:
                pending.setdefault(key, document)

        if pending:
            rendered = list(self._renderer(list(pending.values()), style.dpi))
            if len(rendered) != len(pending):
                raise RuntimeError(
                    f"The renderer returned {len(rendered)} images for "
                    f"{len(pending)} documents."
                )

            fresh: dict[str, np.ndarray] = {}
            for key, image in zip(pending, rendered):
                fresh[key] = array_to_rgb(image)
                self._cache.put(key, fresh[key])

            for name, key in key_of.items():
                if name not in images:
                    images[name] = fresh[key]

        return images

    def render(self) -> Self:
        """
        Pre-render the tables.

        Renders (or fetches from the cache) the image of every visible
        table so that ``preview``, ``save`` and the other outputs are
        immediate afterwards. It is optional: those methods render on
        demand.

        Returns
        -------
        TableSheet
            The sheet, for chaining.
        """
        self._rasterize(self._visible_panels(self._resolve_grid()))
        return self

    @property
    def figure(self) -> Any:
        """
        The composed sheet as a matplotlib ``Figure``.

        It is rebuilt on every access from the cached table images, so it
        always reflects the current state of the sheet.
        """
        from ..rendering.composer import compose

        grid = self._resolve_grid()
        panels = self._visible_panels(grid)
        return compose(
            grid,
            {panel.name: panel for panel in panels},
            self._rasterize(panels),
            self._style,
            header=self._header,
            notes=self._notes,
            sources=self._sources,
        )

    # ------------------------------------------------------------------
    # Outputs
    # ------------------------------------------------------------------

    def to_bytes(self, fmt: str = "png", *, transparent: bool = False) -> bytes:
        """
        Return the sheet encoded as bytes.

        Parameters
        ----------
        fmt : {"png", "pdf", "svg", "jpg"}, default "png"
            Output format. ``png`` bytes can be inserted directly into a
            presentation, e.g. ``io.BytesIO(sheet.to_bytes())``.
        transparent : bool, default False
            Transparent background.

        Returns
        -------
        bytes
            Encoded image.
        """
        fmt = fmt.lower().lstrip(".")
        if fmt not in _FORMATS:
            raise ValueError(f"fmt must be one of {sorted(_FORMATS)}.")

        fig = self.figure
        buffer = io.BytesIO()
        # 'standard' bbox keeps the computed size even if the user has
        # ``savefig.bbox = "tight"`` in their matplotlib configuration.
        with matplotlib.rc_context({"savefig.bbox": "standard"}):
            fig.savefig(
                buffer,
                format="jpeg" if fmt == "jpg" else fmt,
                dpi=self._style.dpi,
                facecolor="none" if transparent else self._style.background,
                transparent=transparent,
            )
        return buffer.getvalue()

    def to_array(self) -> np.ndarray:
        """
        Return the sheet as an RGB ``uint8`` array ``(H, W, 3)``.

        Returns
        -------
        numpy.ndarray
            Pixels of the final image.
        """
        fig = self.figure
        fig.canvas.draw()
        return np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()

    @property
    def size_in(self) -> tuple[float, float]:
        """Final size ``(width, height)`` in inches."""
        width, height = self.figure.get_size_inches()
        return float(width), float(height)

    def save(
        self,
        path: str | Path | None = None,
        *,
        dir: str | Path | None = None,
        name: str | None = None,
        fmt: str | None = None,
        transparent: bool = False,
    ) -> Self:
        """
        Write the sheet to a file.

        Give either ``path`` or ``name`` (with an optional ``dir``), as in
        ``GraphMtplt.save``. The format comes from ``fmt`` or from the file
        extension (``png`` when there is none).

        Parameters
        ----------
        path : str | pathlib.Path | None, default None
            Complete output path.
        dir : str | pathlib.Path | None, default None
            Output folder (created if missing). Used with ``name``.
        name : str | None, default None
            File name, with or without extension.
        fmt : {"png", "pdf", "svg", "jpg"} | None, default None
            Output format. Overrides the extension.
        transparent : bool, default False
            Transparent background.

        Returns
        -------
        TableSheet
            The sheet, for chaining. See ``last_path``.

        Raises
        ------
        ValueError
            If neither ``path`` nor ``name`` is given, or ``fmt`` is not
            supported.

        Examples
        --------
        >>> sheet.save("out/lamina.png")
        >>> sheet.save(dir="out", name="lamina", fmt="pdf")
        """
        if path is None and name is None:
            raise ValueError("Give either path or name.")

        target = Path(path) if path is not None else Path(dir or ".") / name

        suffix = target.suffix.lstrip(".").lower()
        chosen = (fmt or suffix or "png").lower().lstrip(".")
        if chosen not in _FORMATS:
            raise ValueError(f"fmt must be one of {sorted(_FORMATS)}.")
        if suffix != chosen:
            # Replace a known image extension, append to anything else.
            target = (
                target.with_suffix(f".{chosen}")
                if suffix in _FORMATS
                else target.with_name(f"{target.name}.{chosen}")
            )

        data = self.to_bytes(chosen, transparent=transparent)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        self._last_path = target
        return self

    @property
    def last_path(self) -> Path | None:
        """Path written by the last ``save`` call."""
        return self._last_path

    # ------------------------------------------------------------------
    # Notebook display
    # ------------------------------------------------------------------

    def preview(self) -> Self:
        """
        Display the sheet in a Jupyter notebook without writing a file.

        Returns
        -------
        TableSheet
            The sheet, for chaining.
        """
        try:
            from IPython import get_ipython
            from IPython.display import Image, display
        except ImportError:
            get_ipython = None

        if get_ipython is None or get_ipython() is None:
            warnings.warn(
                "preview() only displays inside IPython/Jupyter.",
                stacklevel=2,
            )
            return self

        display(Image(data=self.to_bytes("png"), format="png"))
        return self

    def _repr_png_(self) -> bytes:
        """Rich display hook: a sheet shows itself as the last cell value."""
        return self.to_bytes("png")

    def __repr__(self) -> str:
        if self._mosaic is not None:
            layout = f"layout={self._mosaic}"
        elif self._shape is not None:
            layout = f"nrows={self._shape[0]}, ncols={self._shape[1]}"
        else:
            layout = "stacked"
        return (
            f"{type(self).__name__}("
            f"panels={[p.name for p in self._panels]}, "
            f"active={self._active}, "
            f"{layout}, width_in={self._style.width_in})"
        )
