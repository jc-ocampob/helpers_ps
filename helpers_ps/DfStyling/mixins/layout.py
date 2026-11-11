from __future__ import annotations

from collections.abc import Sequence
from dataclasses import fields, replace
from typing import Self, Unpack

from ..models import (
    EMPTY_CELL,
    GridLayout,
    Header,
    Key,
    SheetStyle,
    SheetStyleOptions,
)
from .base import SheetBase
from .panels import _as_list


class LayoutMixin(SheetBase):
    """Sheet texts, spacing, rules and arrangement of the panels."""

    # ------------------------------------------------------------------
    # Texts
    # ------------------------------------------------------------------

    def add_title(
        self,
        text: str,
        *,
        size: float | None = None,
        color: str | None = None,
        weight: str | None = None,
    ) -> Self:
        """
        Set the sheet title, drawn above all panels.

        Parameters
        ----------
        text : str
            Title text. An empty string removes it.
        size, color, weight : optional
            Overrides of ``header_size``, ``header_color`` and
            ``header_weight``.

        Returns
        -------
        TableSheet
            The sheet, for chaining.
        """
        self._header = Header(text, size, color, weight) if text else None
        return self

    def add_note(
        self,
        *notes: str | Sequence[str],
        size: float | None = None,
        color: str | None = None,
    ) -> Self:
        """
        Append general notes below the panels (above the sources).

        Parameters
        ----------
        *notes : str | Sequence[str]
            One or several notes.
        size : float | None, default None
            Font size in points of **all** notes: the general ones and the
            ones under each panel. ``None`` leaves the current size
            unchanged (``footer_size`` unless it was set before). To go
            back to ``footer_size`` use ``config_layout(note_size=None)``.
        color : str | None, default None
            Color of all notes. ``None`` leaves it unchanged.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Raises
        ------
        ValueError
            If ``size`` is not positive. Nothing is changed in that case.

        Examples
        --------
        >>> sheet.add_note("MTD: month to date.", "YTD: year to date.", size=6)
        """
        self._set_text_style("note", size, color)
        for note in notes:
            self._notes.extend(_as_list(note))
        return self

    def add_source(
        self,
        *sources: str | Sequence[str],
        size: float | None = None,
        color: str | None = None,
    ) -> Self:
        """
        Set the source lines at the bottom (replaces previous ones).

        Lines are printed exactly as given: add any prefix, license or
        copyright text yourself. Nothing is added automatically.

        Parameters
        ----------
        *sources : str | Sequence[str]
            One or several lines. Call with no arguments to clear.
        size : float | None, default None
            Font size in points of the source lines. ``None`` leaves the
            current size unchanged (``footer_size`` unless it was set
            before). To go back to ``footer_size`` use
            ``config_layout(source_size=None)``.
        color : str | None, default None
            Color of the source lines. ``None`` leaves it unchanged.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Raises
        ------
        ValueError
            If ``size`` is not positive. Nothing is changed in that case.

        Examples
        --------
        >>> sheet.add_source("Fuente: Example Data", "© My Company", size=6)
        """
        self._set_text_style("source", size, color)
        self._sources = [
            line for source in sources for line in _as_list(source)
        ]
        return self

    def _set_text_style(
        self,
        kind: str,
        size: float | None,
        color: str | None,
    ) -> None:
        """Set ``note_*`` / ``source_*`` style fields that were given."""
        given = {f"{kind}_size": size, f"{kind}_color": color}
        changes = {name: value for name, value in given.items() if value is not None}
        if changes:
            self.config_layout(**changes)

    # ------------------------------------------------------------------
    # Visual parameters
    # ------------------------------------------------------------------

    def config_layout(self, **changes: Unpack[SheetStyleOptions]) -> Self:
        """
        Change visual parameters of the sheet.

        Parameters
        ----------
        **changes
            Any ``SheetStyle`` field: ``width_in``, ``height_in``,
            ``dpi``, ``left``, ``wspace``, ``line_width``, ``scale``,
            ``font_family``... Fields that accept ``None`` (``height_in``,
            ``left``, ``right``, ``bottom``, ``top``, ``wspace``,
            ``hspace``) go back to *automatic* when set to ``None``.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Raises
        ------
        TypeError
            If a name is not a ``SheetStyle`` field.
        ValueError
            If a value is invalid. Nothing is changed in that case.

        Examples
        --------
        >>> sheet.config_layout(width_in=13.33, height_in=7.5, scale="fit")
        >>> sheet.config_layout(wspace=None)        # back to col_gap_in
        """
        valid = {item.name for item in fields(SheetStyle)}
        unknown = sorted(set(changes) - valid)
        if unknown:
            raise TypeError(
                f"Unknown layout option(s): {unknown}. "
                f"Valid options: {sorted(valid)}."
            )

        self._style = replace(self._style, **changes)
        return self

    def subplots_adjust(
        self,
        left: float | None = None,
        bottom: float | None = None,
        right: float | None = None,
        top: float | None = None,
        wspace: float | None = None,
        hspace: float | None = None,
    ) -> Self:
        """
        Position the grid of panels, like ``matplotlib.pyplot.subplots_adjust``.

        Only the values you pass are changed. Every value is a *fraction*:

        * ``left``, ``right``: edges of the grid, as a fraction of the
          image width (0 is the left border).
        * ``bottom``, ``top``: edges of the grid, as a fraction of the
          image height measured **from the bottom** (``top=0.9`` leaves
          10% above the grid). They need a fixed ``height_in``.
        * ``wspace``, ``hspace``: space between columns / rows, as a
          fraction of the average column width / average row height.

        Anything not set stays *automatic*: the grid fills the width
        between ``margin_in`` margins, sits between the sheet title and the
        sources, and uses ``col_gap_in`` / ``row_gap_in`` as spacing. To go
        back to automatic use ``config_layout(left=None, ...)``.

        The sheet title and the sources are aligned to the left edge of the
        grid.

        Parameters
        ----------
        left, bottom, right, top : float | None, default None
            Edges of the grid (0-1).
        wspace, hspace : float | None, default None
            Spacing between panels (>= 0).

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Raises
        ------
        ValueError
            If ``left >= right``, ``bottom >= top`` or a value is out of
            range. Using ``top``/``bottom`` without ``height_in`` raises
            when the sheet is rendered.

        Examples
        --------
        >>> sheet.config_layout(width_in=13.33, height_in=7.5)
        >>> sheet.subplots_adjust(left=0.06, right=0.94, top=0.82, bottom=0.12,
        ...                       wspace=0.15, hspace=0.25)
        """
        given = {
            "left": left,
            "bottom": bottom,
            "right": right,
            "top": top,
            "wspace": wspace,
            "hspace": hspace,
        }
        return self.config_layout(
            **{name: value for name, value in given.items() if value is not None}
        )

    # ------------------------------------------------------------------
    # Arrangement
    # ------------------------------------------------------------------

    def layout(
        self,
        rows: Sequence[Sequence[Key | None]] | None = None,
        *,
        nrows: int | None = None,
        ncols: int | None = None,
        width_ratios: Sequence[float] | None = None,
    ) -> Self:
        """
        Arrange the panels on a grid.

        With no arguments the panels are stacked vertically (one per row),
        which is the default. Panels can be arranged in three ways:

        * ``nrows`` / ``ncols``: fill a grid row by row in creation order.
        * ``rows``: an explicit grid, like ``matplotlib.pyplot.subplot_mosaic``.
          Repeat a panel to make it span several cells; use ``None`` or
          ``"."`` for an empty cell. A shorter row is stretched when its
          length divides the number of columns.
        * ``width_ratios``: relative width of each column.

        Row heights follow the content of each row.

        Parameters
        ----------
        rows : Sequence[Sequence[int | str | None]] | None, default None
            Explicit grid of panel names or positions.
        nrows, ncols : int | None, default None
            Shape of the automatic grid. If only one is given the other is
            the smallest that holds every panel. Cells left over stay
            empty. Cannot be combined with ``rows``.
        width_ratios : Sequence[float] | None, default None
            Relative column widths. Needs one value per column.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Raises
        ------
        ValueError
            If ``rows`` and ``nrows``/``ncols`` are combined, a value is
            invalid, a panel repeats in cells that do not form a
            rectangle, or a row cannot be stretched evenly.
        KeyError
            If a panel does not exist.

        Examples
        --------
        >>> sheet.layout()                           # vertical (default)
        >>> sheet.layout(nrows=1)                    # horizontal: one row
        >>> sheet.layout(ncols=2)                    # two columns
        >>> sheet.layout(nrows=2)                    # two rows
        >>> sheet.layout([["a", "b"], ["c", "c"]])   # c spans both columns
        >>> sheet.layout([["a", "c"], ["b", "c"]], width_ratios=[1, 2])
        >>> sheet.layout([["a", "b", "c"], ["d", "d", "e"]])
        """
        if rows is not None and (nrows is not None or ncols is not None):
            raise ValueError(
                "Use either rows (explicit grid) or nrows/ncols, not both."
            )
        for label, value in (("nrows", nrows), ("ncols", ncols)):
            if value is not None and (not isinstance(value, int) or value < 1):
                raise ValueError(f"{label} must be an integer >= 1.")

        ratios = None
        if width_ratios is not None:
            ratios = [float(value) for value in width_ratios]
            if any(value <= 0 for value in ratios):
                raise ValueError("width_ratios must be > 0.")

        if rows is None:
            self._mosaic = None
            self._shape = (
                (nrows, ncols) if nrows is not None or ncols is not None else None
            )
            self._width_ratios = ratios
            return self

        if isinstance(rows, (str, int)):
            raise TypeError(
                "rows must be a sequence of sequences, e.g. [['a', 'b'], ['c']]."
            )

        cells: list[list[str | None]] = []
        for row in rows:
            if isinstance(row, (str, int)):
                raise TypeError(
                    "rows must be a sequence of sequences, e.g. "
                    "[['a', 'b'], ['c']]."
                )
            if not len(row):
                raise ValueError("A layout row cannot be empty.")
            cells.append(
                [
                    None
                    if key is None or key == EMPTY_CELL
                    else self._find(key).name
                    for key in row
                ]
            )

        grid = GridLayout.from_rows(cells, ratios)  # validates everything
        self._mosaic = grid.cells
        self._shape = None
        self._width_ratios = ratios
        return self
