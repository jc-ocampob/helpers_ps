from __future__ import annotations

from pathlib import Path

from ..models import Header, Key, Panel, Renderer, SheetStyle
from ..rendering.cache import RenderCache


class SheetBase:
    """
    State shared by the ``TableSheet`` mixins.

    Attributes
    ----------
    _panels : list[Panel]
        Tables and images of the sheet, in creation order.
    _active : list[str]
        Names of the panels targeted by styling methods (see ``on``).
    _style : SheetStyle
        Visual parameters.
    _header : Header | None
        Sheet title.
    _notes, _sources : list[str]
        General notes and source lines.
    _mosaic : list[list[str | None]] | None
        Explicit grid (panel names, repeated to span, ``None`` empty).
    _shape : tuple[int | None, int | None] | None
        ``(nrows, ncols)`` of the automatic grid. With no mosaic and no
        shape the panels are stacked in one column.
    _width_ratios : list[float] | None
        Relative column widths.
    _renderer : Renderer
        Converts HTML documents to images.
    _cache : RenderCache
        Cache of rendered tables.
    _counter : int
        Number of panels ever created (used for automatic names).
    _last_path : Path | None
        Path written by the last ``save``.
    """

    _panels: list[Panel]
    _active: list[str]
    _style: SheetStyle
    _header: Header | None
    _notes: list[str]
    _sources: list[str]
    _mosaic: list[list[str | None]] | None
    _shape: tuple[int | None, int | None] | None
    _width_ratios: list[float] | None
    _renderer: Renderer
    _cache: RenderCache
    _counter: int
    _last_path: Path | None

    # ------------------------------------------------------------------
    # Panel lookup
    # ------------------------------------------------------------------

    def _find(self, key: Key) -> Panel:
        """
        Return the panel referenced by a position or a name.

        Raises
        ------
        KeyError
            If the position or name does not exist.
        TypeError
            If ``key`` is neither ``int`` nor ``str``.
        """
        if isinstance(key, bool) or not isinstance(key, (int, str)):
            raise TypeError(
                f"A panel key must be an int position or a str name, "
                f"got {type(key).__name__}."
            )

        if isinstance(key, int):
            try:
                return self._panels[key]
            except IndexError:
                raise KeyError(
                    f"Panel position {key} is out of range "
                    f"(0..{len(self._panels) - 1})."
                ) from None

        for panel in self._panels:
            if panel.name == key:
                return panel

        raise KeyError(
            f"Unknown panel {key!r}. Available: "
            f"{[panel.name for panel in self._panels]}."
        )

    def _targets(self, *, tables_only: bool = False) -> list[Panel]:
        """
        Return the active panels.

        Parameters
        ----------
        tables_only : bool, default False
            Require every active panel to be a table.

        Raises
        ------
        ValueError
            If the sheet has no panels.
        TypeError
            If ``tables_only`` and an active panel is an image.
        """
        if not self._panels:
            raise ValueError(
                "The sheet has no panels. Add one with add_table() or "
                "add_image()."
            )

        panels = [self._find(name) for name in self._active]

        if tables_only:
            images = [p.name for p in panels if p.kind != "table"]
            if images:
                raise TypeError(
                    f"Styling applies to tables only; image panels are "
                    f"active: {images}. Use on(...) to select tables."
                )

        return panels
