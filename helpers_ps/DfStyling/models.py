from __future__ import annotations

import copy
import math
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from numbers import Real
from typing import Any, Literal, TypeAlias, TypedDict

import numpy as np
from pandas import DataFrame
from pandas.io.formats.style import Styler

from .constants import (
    DEFAULT_DPI,
    DEFAULT_FONT_FAMILY,
    STYLER_UUID,
)


# ---------------------------------------------------------------------
# Styling type aliases (used by formating.py, mapping.py, table.py)
# ---------------------------------------------------------------------

StylerLike: TypeAlias = DataFrame | Styler

Label: TypeAlias = Hashable
Labels: TypeAlias = Hashable | Iterable[Hashable]
LabelCollection: TypeAlias = Iterable[Hashable]

CSSProperties: TypeAlias = Mapping[str, str]
OptionalCSSProperties: TypeAlias = Mapping[str, str] | None

BorderPosition: TypeAlias = Literal[
    "top",
    "bottom",
    "left",
    "right",
]

RowBorderPosition: TypeAlias = Literal[
    "top",
    "bottom",
]

ColumnBorderPosition: TypeAlias = Literal[
    "left",
    "right",
]

BorderLineStyle: TypeAlias = Literal[
    "none",
    "hidden",
    "dotted",
    "dashed",
    "solid",
    "double",
    "groove",
    "ridge",
    "inset",
    "outset",
]

ColorRanges: TypeAlias = Mapping[tuple[Real, Real], str]


# ---------------------------------------------------------------------
# TableSheet type aliases
# ---------------------------------------------------------------------

#: Panel reference: position (``int``) or name (``str``).
Key: TypeAlias = int | str

#: One note or several notes.
Notes: TypeAlias = str | Sequence[str] | None

Align: TypeAlias = Literal["left", "center", "right"]
ScaleMode: TypeAlias = Literal["uniform", "fit", "natural"]
VAlign: TypeAlias = Literal["top", "center", "bottom"]
Resampling: TypeAlias = Literal["lanczos", "bicubic", "bilinear", "nearest"]
PanelKind: TypeAlias = Literal["table", "image"]

#: ``renderer(documents, dpi) -> images``. Receives complete HTML
#: documents and returns one RGB ``uint8`` array per document.
Renderer: TypeAlias = Callable[[Sequence[str], int], Sequence[np.ndarray]]

#: Function applied to a ``Styler``: ``func(styler, *args, **kwargs)``.
StylerFunc: TypeAlias = Callable[..., Styler]

SCALE_MODES = ("uniform", "fit", "natural")
VALIGNS = ("top", "center", "bottom")
RESAMPLINGS = ("lanczos", "bicubic", "bilinear", "nearest")
ALIGNS = ("left", "center", "right")

#: Marker of an empty cell in a layout (``None`` works as well).
EMPTY_CELL = "."


# ---------------------------------------------------------------------
# Sheet style
# ---------------------------------------------------------------------

@dataclass
class SheetStyle:
    """
    Visual parameters of a ``TableSheet``.

    Every field can be changed with ``TableSheet.config_layout`` (or with
    the shortcut ``subplots_adjust``) and passed as a
    keyword argument of the ``TableSheet`` constructor.

    Size
    ----
    font_family : str
        Font of titles, notes and sources. A comma-separated list is
        accepted; the first installed font is used, with a fallback to
        ``DejaVu Sans``.
    width_in : float
        Image width in inches.
    height_in : float | None
        Image height in inches. ``None`` (default) computes it from the
        content. When set, the image has exactly this height: the source
        lines are anchored to the bottom, panels that do not fit are
        scaled down keeping their proportions, and free space is
        distributed according to ``valign``. For a 16:9 slide use
        ``width_in=13.33, height_in=7.5``.
    valign : {"top", "center", "bottom"}
        Where the panels sit when ``height_in`` leaves free space.
    dpi : int
        Resolution of rendered tables and of the exported image.

    Spacing (``subplots_adjust`` semantics)
    ---------------------------------------
    The panels live in a grid. ``left``, ``right``, ``bottom``, ``top``,
    ``wspace`` and ``hspace`` work like ``matplotlib.pyplot.subplots_adjust``.
    ``None`` means *automatic* and falls back to the inch-based values.

    left, right : float | None
        Left and right edge of the grid, as a fraction of the image width
        (0-1). ``None`` uses ``margin_in`` on each side. Titles and
        sources are aligned to the left edge.
    bottom, top : float | None
        Bottom and top edge of the grid, as a fraction of the image
        height measured from the bottom (0-1, like matplotlib). Require
        ``height_in``. ``None`` places the grid between the sheet title
        and the sources.
    wspace, hspace : float | None
        Space between columns / rows, as a fraction of the average column
        width / average row height (like matplotlib). ``None`` uses
        ``col_gap_in`` / ``row_gap_in``.
    margin_in : float
        Side margin in inches when ``left`` / ``right`` are ``None``.
    col_gap_in, row_gap_in : float
        Space between columns / rows in inches when ``wspace`` /
        ``hspace`` are ``None``.
    pad_top_in, pad_bottom_in : float
        Space above the top rule and below the last source line.

    Text
    ----
    header_size, header_color, header_weight
        Style of the sheet title (``add_title``).
    title_size, title_color, title_weight
        Default style of panel titles.
    subtitle_size, subtitle_color
        Style of panel subtitles.
    title_gap_in : float
        Gap between a panel title block and its table.
    footer_size, footer_color
        Default size and color of panel notes, general notes and sources.
    note_size, note_color : float | None, str | None
        Size and color of the notes: the ones under each panel
        (``panel(notes=...)``) and the general ones (``add_note``).
        ``None`` uses ``footer_size`` / ``footer_color``.
    source_size, source_color : float | None, str | None
        Size and color of the source lines (``add_source``). ``None``
        uses ``footer_size`` / ``footer_color``.
    line_spacing : float
        Line height as a multiple of the font size.
    wrap_text : bool
        Wrap titles and notes to the width of their cell.

    Horizontal rules
    ----------------
    line_color : str
        Color of both rules.
    line_width : float
        Thickness of both rules, in points.
    top_line, bottom_line : bool
        Show the rule above the content / above the sources.

    Panels
    ------
    background : str
        Canvas color.
    scale : {"uniform", "fit", "natural"}
        How panel images are scaled (each panel can override it with
        ``panel(scale=...)``). ``"uniform"`` uses the same scale for all
        tables (same visual font size), the largest that fits every cell.
        ``"fit"`` stretches the panel to its cell width. ``"natural"``
        keeps the real size (``px / dpi`` inches) and only shrinks panels
        that do not fit. Image panels treat ``"uniform"`` as
        ``"natural"``, so a chart is never stretched unless it is set to
        ``"fit"``.
    resampling : {"lanczos", "bicubic", "bilinear", "nearest"}
        Filter used to resize table images (done once with PIL).
    table_font_px : int
        Base font size of rendered tables in CSS pixels. Styles set with
        ``style_table(font_size=...)`` override it.
    zebra : bool
        Alternate row shading (``#f5f5f5`` on odd rows) in the base table
        CSS.
    """

    font_family: str = DEFAULT_FONT_FAMILY
    width_in: float = 8.0
    height_in: float | None = None
    valign: VAlign = "top"
    dpi: int = DEFAULT_DPI

    left: float | None = None
    right: float | None = None
    bottom: float | None = None
    top: float | None = None
    wspace: float | None = None
    hspace: float | None = None
    margin_in: float = 0.45
    col_gap_in: float = 0.30
    row_gap_in: float = 0.30
    pad_top_in: float = 0.15
    pad_bottom_in: float = 0.20

    header_size: float = 18
    header_color: str = "#111111"
    header_weight: str = "bold"
    title_size: float = 12
    title_color: str = "#111111"
    title_weight: str = "bold"
    subtitle_size: float = 9
    subtitle_color: str = "#666666"
    title_gap_in: float = 0.08
    footer_size: float = 9
    footer_color: str = "#666666"
    note_size: float | None = None
    note_color: str | None = None
    source_size: float | None = None
    source_color: str | None = None
    line_spacing: float = 1.5
    wrap_text: bool = True

    line_color: str = "#D9D9D9"
    line_width: float = 1.2
    top_line: bool = True
    bottom_line: bool = True

    background: str = "white"
    scale: ScaleMode = "uniform"
    resampling: Resampling = "lanczos"
    table_font_px: int = 14
    zebra: bool = True

    def __post_init__(self) -> None:
        if self.width_in <= 0:
            raise ValueError("width_in must be > 0.")
        if self.height_in is not None and self.height_in <= 0:
            raise ValueError("height_in must be > 0 (or None for automatic).")
        if self.dpi <= 0:
            raise ValueError("dpi must be > 0.")
        if self.table_font_px <= 0:
            raise ValueError("table_font_px must be > 0.")
        if self.line_spacing <= 0:
            raise ValueError("line_spacing must be > 0.")
        for name in ("note_size", "source_size"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(
                    f"{name} must be > 0 (or None to use footer_size)."
                )
        for name, allowed in (
            ("valign", VALIGNS),
            ("scale", SCALE_MODES),
            ("resampling", RESAMPLINGS),
        ):
            if getattr(self, name) not in allowed:
                raise ValueError(
                    f"{name} must be one of {allowed}, "
                    f"got {getattr(self, name)!r}."
                )

        for name in ("left", "right", "bottom", "top"):
            value = getattr(self, name)
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1.")
        if None not in (self.left, self.right) and self.left >= self.right:
            raise ValueError("left must be smaller than right.")
        if None not in (self.bottom, self.top) and self.bottom >= self.top:
            raise ValueError("bottom must be smaller than top.")

        for name in ("wspace", "hspace"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be >= 0.")
        if self.line_width < 0:
            raise ValueError("line_width must be >= 0.")
        for name in (
            "margin_in",
            "pad_top_in",
            "pad_bottom_in",
            "col_gap_in",
            "row_gap_in",
            "title_gap_in",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0.")
        if 2 * self.margin_in >= self.width_in:
            raise ValueError("margin_in is too large for width_in.")


class SheetStyleOptions(TypedDict, total=False):
    """Keyword options accepted by ``TableSheet`` (mirror of ``SheetStyle``)."""

    font_family: str
    width_in: float
    height_in: float | None
    valign: VAlign
    dpi: int
    left: float | None
    right: float | None
    bottom: float | None
    top: float | None
    wspace: float | None
    hspace: float | None
    margin_in: float
    col_gap_in: float
    row_gap_in: float
    pad_top_in: float
    pad_bottom_in: float
    header_size: float
    header_color: str
    header_weight: str
    title_size: float
    title_color: str
    title_weight: str
    subtitle_size: float
    subtitle_color: str
    title_gap_in: float
    footer_size: float
    footer_color: str
    note_size: float | None
    note_color: str | None
    source_size: float | None
    source_color: str | None
    line_spacing: float
    wrap_text: bool
    line_color: str
    line_width: float
    top_line: bool
    bottom_line: bool
    background: str
    scale: ScaleMode
    resampling: Resampling
    table_font_px: int
    zebra: bool


# ---------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Span:
    """Block of grid cells occupied by a panel (``row``/``col`` are 0-based)."""

    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1

    @property
    def row_end(self) -> int:
        return self.row + self.rowspan

    @property
    def col_end(self) -> int:
        return self.col + self.colspan


class GridLayout:
    """
    Rectangular grid of panel names.

    A name that appears in several adjacent cells *spans* them, as in
    ``matplotlib.pyplot.subplot_mosaic``. ``None`` is an empty cell.

    Parameters
    ----------
    cells : Sequence[Sequence[str | None]]
        Panel names by row. All rows must have the same length.
    width_ratios : Sequence[float] | None, default None
        Relative width of every column (like ``GridSpec``). ``None``
        makes all columns equal.

    Attributes
    ----------
    nrows, ncols : int
        Grid shape.
    spans : dict[str, Span]
        Block of cells of every panel, in reading order.
    width_ratios : list[float]
        Relative column widths.

    Raises
    ------
    ValueError
        If the grid is empty or ragged, a panel does not form a
        rectangle, or ``width_ratios`` has the wrong length or a
        non-positive value.

    Examples
    --------
    >>> GridLayout([["a", "b"], ["c", "c"]]).spans["c"]
    Span(row=1, col=0, rowspan=1, colspan=2)
    """

    def __init__(
        self,
        cells: Sequence[Sequence[str | None]],
        width_ratios: Sequence[float] | None = None,
    ) -> None:
        if not cells or not len(cells[0]):
            raise ValueError("The grid is empty.")

        ncols = len(cells[0])
        if any(len(row) != ncols for row in cells):
            raise ValueError("All grid rows must have the same length.")

        self.cells: list[list[str | None]] = [list(row) for row in cells]
        self.nrows = len(self.cells)
        self.ncols = ncols

        if width_ratios is None:
            self.width_ratios = [1.0] * ncols
        else:
            self.width_ratios = [float(value) for value in width_ratios]
            if len(self.width_ratios) != ncols:
                raise ValueError(
                    f"width_ratios has {len(self.width_ratios)} values but "
                    f"the grid has {ncols} columns."
                )
            if any(value <= 0 for value in self.width_ratios):
                raise ValueError("width_ratios must be > 0.")

        self.spans = self._compute_spans()

    def _compute_spans(self) -> dict[str, Span]:
        positions: dict[str, list[tuple[int, int]]] = {}
        for r, row in enumerate(self.cells):
            for c, name in enumerate(row):
                if name is not None:
                    positions.setdefault(name, []).append((r, c))

        spans: dict[str, Span] = {}
        for name, found in positions.items():
            rows = [r for r, _ in found]
            cols = [c for _, c in found]
            r0, r1 = min(rows), max(rows) + 1
            c0, c1 = min(cols), max(cols) + 1
            if (r1 - r0) * (c1 - c0) != len(found):
                raise ValueError(
                    f"Panel {name!r} must occupy a rectangular block of "
                    "cells; it is repeated in cells that do not form a "
                    "rectangle."
                )
            spans[name] = Span(r0, c0, r1 - r0, c1 - c0)
        return spans

    @property
    def names(self) -> list[str]:
        """Panel names in reading order."""
        return list(self.spans)

    # -- constructors ----------------------------------------------------

    @classmethod
    def stacked(cls, names: Sequence[str]) -> GridLayout:
        """One panel per row (vertical arrangement)."""
        return cls([[name] for name in names])

    @classmethod
    def filled(
        cls,
        names: Sequence[str],
        nrows: int | None = None,
        ncols: int | None = None,
        width_ratios: Sequence[float] | None = None,
    ) -> GridLayout:
        """
        Fill a grid row by row.

        Parameters
        ----------
        names : Sequence[str]
            Panels, in order.
        nrows, ncols : int | None, default None
            Grid shape. If only one is given the other is the smallest
            that holds every panel; if none is given the panels are
            stacked in one column. Cells left over stay empty.
        width_ratios : Sequence[float] | None, default None
            Relative column widths.

        Raises
        ------
        ValueError
            If the panels do not fit in ``nrows x ncols``.
        """
        count = len(names)
        if nrows is None and ncols is None:
            ncols = 1
        if ncols is None:
            ncols = math.ceil(count / nrows)
        if nrows is None:
            nrows = math.ceil(count / ncols)
        elif count and nrows * ncols >= count:
            # Never create rows that would stay empty.
            nrows = min(nrows, math.ceil(count / ncols))

        if nrows * ncols < count:
            raise ValueError(
                f"{count} panels do not fit in a grid of {nrows} rows x "
                f"{ncols} columns."
            )

        padded = [*names] + [None] * (nrows * ncols - count)
        cells = [padded[i * ncols : (i + 1) * ncols] for i in range(nrows)]
        return cls(cells, width_ratios)

    @classmethod
    def from_rows(
        cls,
        rows: Sequence[Sequence[str | None]],
        width_ratios: Sequence[float] | None = None,
    ) -> GridLayout:
        """
        Build a grid from rows that may have different lengths.

        The grid has as many columns as the longest row. A shorter row
        is stretched when its length divides that number (so
        ``[["a", "b"], ["c"]]`` makes ``c`` span both columns). Otherwise
        repeat names to span explicitly.

        Raises
        ------
        ValueError
            If a row cannot be stretched evenly.
        """
        if not rows:
            raise ValueError("The grid is empty.")

        width = max(len(row) for row in rows)
        cells: list[list[str | None]] = []
        for index, row in enumerate(rows):
            if len(row) == width:
                cells.append(list(row))
            elif width % len(row) == 0:
                factor = width // len(row)
                cells.append([name for name in row for _ in range(factor)])
            else:
                raise ValueError(
                    f"Row {index} has {len(row)} entries but the grid has "
                    f"{width} columns. Repeat a name to make it span, e.g. "
                    "[['a', 'b', 'c'], ['d', 'd', 'e']]."
                )
        return cls(cells, width_ratios)

    @staticmethod
    def without(
        cells: Sequence[Sequence[str | None]],
        width_ratios: Sequence[float] | None,
        doomed: set[str],
    ) -> tuple[list[list[str | None]] | None, list[float] | None]:
        """
        Remove panels from a grid, dropping rows/columns left empty.

        Returns ``(None, None)`` if nothing remains.
        """
        blank = [
            [None if name in doomed else name for name in row] for row in cells
        ]
        keep_rows = [i for i, row in enumerate(blank) if any(n for n in row)]
        if not keep_rows:
            return None, None

        keep_cols = [
            j
            for j in range(len(blank[0]))
            if any(blank[i][j] is not None for i in keep_rows)
        ]
        trimmed = [[blank[i][j] for j in keep_cols] for i in keep_rows]
        ratios = (
            [list(width_ratios)[j] for j in keep_cols]
            if width_ratios is not None
            else None
        )
        return trimmed, ratios


# ---------------------------------------------------------------------
# Panels
# ---------------------------------------------------------------------

@dataclass
class Header:
    """Sheet title. ``None`` fields fall back to the ``SheetStyle``."""

    text: str
    size: float | None = None
    color: str | None = None
    weight: str | None = None


@dataclass
class Op:
    """
    One recorded styling operation.

    A table is described by its source plus an ordered list of operations
    (a *recipe*). The ``Styler`` is rebuilt from scratch whenever it is
    needed, so re-running a notebook cell never accumulates CSS.

    Attributes
    ----------
    label : str
        Human-readable name, shown by ``TableSheet.recipe``.
    func : Callable
        ``func(styler, *args, **kwargs)`` returning a ``Styler``.
    args, kwargs
        Extra arguments for ``func``.
    """

    label: str
    func: StylerFunc
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)

    def apply(self, styler: Styler) -> Styler:
        result = self.func(styler, *self.args, **self.kwargs)
        if not isinstance(result, Styler):
            raise TypeError(
                f"Operation {self.label!r} must return a Styler, "
                f"got {type(result).__name__}."
            )
        return result


@dataclass(eq=False)
class Panel:
    """
    One element of the sheet: a table (recipe over a DataFrame/Styler) or
    an image (chart).

    Attributes
    ----------
    name : str
        Unique name inside the sheet.
    kind : {"table", "image"}
        Panel type.
    source : DataFrame | Styler | numpy.ndarray | matplotlib.figure.Figure
        Table source or image source.
    ops : list[Op]
        Styling recipe (tables only).
    title, subtitle : str
        Text above the table. Empty strings are not drawn.
    notes : list[str]
        Notes below the table.
    align : {"left", "center", "right"}
        Horizontal alignment when narrower than its cell.
    valign : {"top", "center", "bottom"}
        Vertical alignment when its cell is taller than the panel (for
        example a panel that spans several rows).
    scale : {"uniform", "fit", "natural"} | None
        Overrides ``SheetStyle.scale`` for this panel.
    title_size, title_color, title_weight
        Per-panel overrides of the title style.
    """

    name: str
    kind: PanelKind
    source: Any
    ops: list[Op] = field(default_factory=list)
    title: str = ""
    subtitle: str = ""
    notes: list[str] = field(default_factory=list)
    align: Align = "left"
    valign: VAlign = "top"
    scale: ScaleMode | None = None
    title_size: float | None = None
    title_color: str | None = None
    title_weight: str | None = None

    def build_styler(self) -> Styler:
        """Build a fresh ``Styler`` by replaying the recipe."""
        if self.kind != "table":
            raise TypeError(f"Panel {self.name!r} is an image, not a table.")

        base = self.source
        styler = (
            copy.deepcopy(base) if isinstance(base, Styler) else base.style
        )
        for op in self.ops:
            styler = op.apply(styler)

        return styler.set_uuid(STYLER_UUID)
