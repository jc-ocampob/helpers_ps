from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import numpy as np

from ..constants import FALLBACK_FONT
from ..models import GridLayout, Header, Panel, SheetStyle, Span

_GENERIC_FAMILIES = {
    "sans-serif",
    "serif",
    "monospace",
    "cursive",
    "fantasy",
}

#: Vertical gaps (inches) between the blocks of the sheet.
_GAP_AFTER_TOP_RULE = 0.15
_GAP_AFTER_HEADER = 0.15
_GAP_NO_HEADER = 0.05
_GAP_BEFORE_BOTTOM_RULE = 0.18
_GAP_AFTER_BOTTOM_RULE = 0.12
_GAP_BEFORE_NOTES = 0.04

#: Smallest panel scale tried when fitting a fixed height.
_MIN_SHRINK = 1e-4


# ---------------------------------------------------------------------
# Fonts and text measurement
# ---------------------------------------------------------------------

@lru_cache(maxsize=None)
def resolve_font(family: str) -> str:
    """
    Pick the first installed font of a CSS-like family list.

    Parameters
    ----------
    family : str
        Font name or comma-separated list, e.g. ``"Inter, Arial"``.

    Returns
    -------
    str
        An installed font, or ``DejaVu Sans`` (with a warning, emitted
        once per family) when none is available.
    """
    from matplotlib import font_manager

    candidates = [
        part.strip().strip("'\"") for part in family.split(",")
    ]
    for candidate in candidates:
        if not candidate:
            continue
        if candidate.lower() in _GENERIC_FAMILIES:
            return candidate
        try:
            font_manager.findfont(candidate, fallback_to_default=False)
            return candidate
        except Exception:
            continue

    warnings.warn(
        f"Font {family!r} not found; using {FALLBACK_FONT!r}.",
        stacklevel=2,
    )
    return FALLBACK_FONT


class TextMeter:
    """
    Measure and wrap text with matplotlib's own text engine.

    Wrapping with real glyph widths keeps the estimated height of titles
    and notes identical to what is finally drawn.
    """

    def __init__(self) -> None:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure

        self._fig = Figure(dpi=100)
        FigureCanvasAgg(self._fig)
        self._renderer = self._fig.canvas.get_renderer()
        self._widths: dict[tuple, float] = {}

    def width(
        self,
        text: str,
        size: float,
        weight: str,
        family: str,
    ) -> float:
        """Width of a single line of text in inches."""
        key = (text, size, weight, family)
        cached = self._widths.get(key)
        if cached is not None:
            return cached

        artist = self._fig.text(
            0,
            0,
            text,
            fontsize=size,
            fontweight=weight,
            family=family,
        )
        value = artist.get_window_extent(self._renderer).width / self._fig.dpi
        artist.remove()

        self._widths[key] = value
        return value

    def wrap(
        self,
        text: str,
        max_width: float,
        size: float,
        weight: str,
        family: str,
    ) -> list[str]:
        """
        Wrap ``text`` to ``max_width`` inches.

        Explicit line breaks are preserved. A word longer than the width
        stays on its own line.
        """
        lines: list[str] = []

        for paragraph in text.split("\n"):
            words = paragraph.split()
            if not words:
                lines.append("")
                continue

            current = words[0]
            for word in words[1:]:
                candidate = f"{current} {word}"
                if self.width(candidate, size, weight, family) <= max_width:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            lines.append(current)

        return lines


def _resize(
    image: np.ndarray,
    width_px: int,
    height_px: int,
    resampling: str,
) -> np.ndarray:
    """
    Resize an RGB image to an exact pixel size with PIL.

    Doing it here, once, is much faster than letting matplotlib resample
    on every draw, and it makes the final placement pixel-exact.
    """
    from PIL import Image

    if image.shape[1] == width_px and image.shape[0] == height_px:
        return image

    filters = {
        "lanczos": Image.Resampling.LANCZOS,
        "bicubic": Image.Resampling.BICUBIC,
        "bilinear": Image.Resampling.BILINEAR,
        "nearest": Image.Resampling.NEAREST,
    }
    resized = Image.fromarray(image).resize(
        (width_px, height_px), filters[resampling]
    )
    return np.asarray(resized)


# ---------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------

@dataclass
class _Cell:
    """A panel placed on the grid, with every derived measure."""

    panel: Panel
    span: Span
    image: np.ndarray
    x: float
    width: float
    fit: float
    mode: str = "uniform"
    scale: float = 0.0
    img_w: float = 0.0
    img_h: float = 0.0
    x_table: float = 0.0
    title: list[str] = field(default_factory=list)
    title_size: float = 0.0
    subtitle: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    head_h: float = 0.0
    foot_h: float = 0.0
    need: float = 0.0


def _step(size: float, style: SheetStyle) -> float:
    """Height in inches of one text line of ``size`` points."""
    return size / 72 * style.line_spacing


def column_geometry(
    ratios: Sequence[float],
    left: float,
    width: float,
    wspace: float | None,
    col_gap_in: float,
) -> tuple[list[float], list[float], float]:
    """
    Compute the position and width of every grid column.

    Parameters
    ----------
    ratios : Sequence[float]
        Relative column widths.
    left, width : float
        Left edge and width of the grid, in inches.
    wspace : float | None
        Space between columns as a fraction of the average column width
        (the formula of ``matplotlib.gridspec.GridSpec``). ``None`` uses
        ``col_gap_in``.
    col_gap_in : float
        Space between columns in inches.

    Returns
    -------
    tuple[list[float], list[float], float]
        Left edge of every column, width of every column and the gap, all
        in inches.

    Raises
    ------
    ValueError
        If the gaps leave no room for the columns.
    """
    count = len(ratios)

    if wspace is None:
        gap = col_gap_in
    else:
        gap = wspace * width / (count + wspace * (count - 1))

    available = width - gap * (count - 1)
    if available <= 0:
        raise ValueError(
            "The space between columns (col_gap_in / wspace) leaves no "
            "room for the panels."
        )

    total = sum(ratios)
    widths = [available * ratio / total for ratio in ratios]

    xs: list[float] = []
    x = left
    for column_width in widths:
        xs.append(x)
        x += column_width + gap
    return xs, widths, gap


def _place_cell(cell: _Cell, shrink: float = 1.0) -> None:
    """Set the drawn size and the left edge of a cell's image."""
    height_px, width_px = cell.image.shape[:2]
    cell.img_w = width_px * cell.scale * shrink
    cell.img_h = height_px * cell.scale * shrink

    offset = {
        "left": 0.0,
        "center": (cell.width - cell.img_w) / 2,
        "right": cell.width - cell.img_w,
    }[cell.panel.align]
    cell.x_table = cell.x + offset


def _build_cells(
    grid: GridLayout,
    panels: Mapping[str, Panel],
    images: Mapping[str, np.ndarray],
    style: SheetStyle,
    left: float,
    width: float,
) -> list[_Cell]:
    """Place every panel on the columns and resolve its scale mode."""
    xs, widths, _ = column_geometry(
        grid.width_ratios, left, width, style.wspace, style.col_gap_in
    )

    cells: list[_Cell] = []
    for name, span in grid.spans.items():
        x = xs[span.col]
        cell_width = xs[span.col_end - 1] + widths[span.col_end - 1] - x
        image = images[name]
        cells.append(
            _Cell(
                panel=panels[name],
                span=span,
                image=image,
                x=x,
                width=cell_width,
                fit=cell_width / image.shape[1],
            )
        )

    # Effective mode of every panel. A chart has no "same font size" to
    # keep, so "uniform" means "natural" for it.
    for cell in cells:
        mode = cell.panel.scale or style.scale
        if mode == "uniform" and cell.panel.kind == "image":
            mode = "natural"
        cell.mode = mode

    uniform = min(
        (cell.fit for cell in cells if cell.mode == "uniform"),
        default=0.0,
    )
    natural = 1 / style.dpi

    for cell in cells:
        if cell.mode == "fit":
            cell.scale = cell.fit
        elif cell.mode == "uniform":
            cell.scale = uniform
        else:  # natural
            cell.scale = min(natural, cell.fit)
        _place_cell(cell)

    return cells


def row_layout(
    needs: Sequence[tuple[Span, float]],
    nrows: int,
    hspace: float | None,
    row_gap_in: float,
) -> tuple[list[float], float]:
    """
    Compute the height of every grid row and the gap between rows.

    A row is as tall as the tallest panel that sits in it alone. A panel
    spanning several rows that needs more room than its rows provide
    enlarges them equally.

    Parameters
    ----------
    needs : Sequence[tuple[Span, float]]
        Block of cells and height in inches needed by every panel (title,
        image and notes).
    nrows : int
        Number of grid rows.
    hspace : float | None
        Space between rows as a fraction of the average row height (as
        ``hspace`` in matplotlib). ``None`` uses ``row_gap_in``.
    row_gap_in : float
        Space between rows in inches.

    Returns
    -------
    tuple[list[float], float]
        Row heights and the gap between rows, in inches.
    """
    base = [0.0] * nrows
    spanning: list[tuple[Span, float]] = []
    for span, need in needs:
        if span.rowspan == 1:
            base[span.row] = max(base[span.row], need)
        else:
            spanning.append((span, need))
    spanning.sort(key=lambda item: item[0].rowspan)

    def solve(gap: float) -> list[float]:
        heights = base[:]
        for span, need in spanning:
            rows = range(span.row, span.row_end)
            current = sum(heights[r] for r in rows) + gap * (span.rowspan - 1)
            if need > current:
                extra = (need - current) / span.rowspan
                for r in rows:
                    heights[r] += extra
        return heights

    if hspace is None:
        return solve(row_gap_in), row_gap_in
    if nrows == 1:
        return solve(0.0), 0.0

    # gap = hspace * mean(heights); the heights shrink as the gap grows,
    # so the equation has a single root, found by bisection.
    low, high = 0.0, hspace * sum(solve(0.0)) / nrows
    for _ in range(60):
        mid = (low + high) / 2
        if mid - hspace * sum(solve(mid)) / nrows > 0:
            high = mid
        else:
            low = mid
    gap = (low + high) / 2
    return solve(gap), gap


# ---------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------

def compose(
    grid: GridLayout,
    panels: Mapping[str, Panel],
    images: Mapping[str, np.ndarray],
    style: SheetStyle,
    *,
    header: Header | None = None,
    notes: Sequence[str] = (),
    sources: Sequence[str] = (),
) -> Any:
    """
    Draw a grid of table/chart images with titles, notes and sources.

    Parameters
    ----------
    grid : GridLayout
        Arrangement of the panels (rows, columns and spans).
    panels : Mapping[str, Panel]
        Panels by name. Every name in ``grid`` must be present.
    images : Mapping[str, numpy.ndarray]
        RGB ``uint8`` image of every panel, by panel name.
    style : SheetStyle
        Visual parameters.
    header : Header | None, default None
        Sheet title.
    notes : Sequence[str], default ()
        General notes, printed first below the content.
    sources : Sequence[str], default ()
        Source lines, printed after the notes.

    Returns
    -------
    matplotlib.figure.Figure
        Figure with an Agg canvas. Its width is ``style.width_in``; its
        height is ``style.height_in`` if set, otherwise computed from the
        content.

    Raises
    ------
    ValueError
        If ``top``/``bottom`` are used without ``height_in``, the grid
        area is empty, the columns do not fit, or ``height_in`` cannot
        hold the titles, notes and spacing.
    """
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D

    font = resolve_font(style.font_family)
    meter = TextMeter()
    width = style.width_in

    left_in = style.left * width if style.left is not None else style.margin_in
    right_in = (
        style.right * width
        if style.right is not None
        else width - style.margin_in
    )
    grid_w = right_in - left_in
    if grid_w <= 0:
        raise ValueError(
            "left/right (or margin_in) leave no room for the panels."
        )

    def wrap(text: str, max_width: float, size: float, weight: str) -> list[str]:
        if not text:
            return []
        if style.wrap_text:
            return meter.wrap(text, max_width, size, weight, font)
        return text.split("\n")

    cells = _build_cells(grid, panels, images, style, left_in, grid_w)

    def measure(shrink: float) -> tuple[list[float], float]:
        """
        Scale every panel image by ``shrink``, wrap the texts and compute
        the row heights. Returns ``(row_heights, row_gap)``.
        """
        for cell in cells:
            _place_cell(cell, shrink)
            panel = cell.panel
            text_w = cell.width - (cell.x_table - cell.x)

            cell.title_size = panel.title_size or style.title_size
            cell.title = wrap(
                panel.title,
                text_w,
                cell.title_size,
                panel.title_weight or style.title_weight,
            )
            cell.subtitle = wrap(
                panel.subtitle, text_w, style.subtitle_size, "normal"
            )
            cell.notes = [
                line
                for note in panel.notes
                for line in wrap(note, text_w, style.footer_size, "normal")
            ]

            head = _step(cell.title_size, style) * len(cell.title)
            head += _step(style.subtitle_size, style) * len(cell.subtitle)
            if cell.title or cell.subtitle:
                head += style.title_gap_in
            cell.head_h = head
            cell.foot_h = (
                _step(style.footer_size, style) * len(cell.notes)
                + _GAP_BEFORE_NOTES
                if cell.notes
                else 0.0
            )
            cell.need = cell.head_h + cell.img_h + cell.foot_h

        return row_layout(
            [(cell.span, cell.need) for cell in cells],
            grid.nrows,
            style.hspace,
            style.row_gap_in,
        )

    def content_height(shrink: float) -> float:
        heights, gap = measure(shrink)
        return sum(heights) + gap * (grid.nrows - 1)

    # -- sheet title and sources ----------------------------------------
    header_size = (header.size if header and header.size else None) or (
        style.header_size
    )
    header_weight = (header.weight if header and header.weight else None) or (
        style.header_weight
    )
    header_color = (header.color if header and header.color else None) or (
        style.header_color
    )
    header_lines = (
        wrap(header.text, grid_w, header_size, header_weight)
        if header and header.text
        else []
    )
    footer_lines = [
        line
        for text in [*notes, *sources]
        for line in wrap(text, grid_w, style.footer_size, "normal")
    ]

    header_block = (
        _step(header_size, style) * len(header_lines) + _GAP_AFTER_HEADER
        if header_lines
        else _GAP_NO_HEADER
    )
    top_block = style.pad_top_in + _GAP_AFTER_TOP_RULE + header_block
    footer_block = _step(style.footer_size, style) * len(footer_lines)
    bottom_block = (
        _GAP_BEFORE_BOTTOM_RULE
        + _GAP_AFTER_BOTTOM_RULE
        + footer_block
        + style.pad_bottom_in
    )

    # -- vertical size and grid area (inches from the top) ---------------
    if style.height_in is None:
        if style.top is not None or style.bottom is not None:
            raise ValueError(
                "top/bottom (subplots_adjust) are fractions of the image "
                "height and need a fixed height_in. With an automatic "
                "height the image grows to fit its content; set height_in "
                "or leave top/bottom as None."
            )
        shrink = 1.0
        heights, gap = measure(shrink)
        content = sum(heights) + gap * (grid.nrows - 1)
        height = top_block + content + bottom_block
        region_top = top_block
        extra = 0.0
    else:
        height = style.height_in
        region_top = (
            (1 - style.top) * height if style.top is not None else top_block
        )
        region_bottom = (
            (1 - style.bottom) * height
            if style.bottom is not None
            else height - bottom_block
        )
        available = region_bottom - region_top

        # Even with the panels reduced to nothing the texts need room.
        minimum = content_height(_MIN_SHRINK)
        if minimum > available:
            if style.top is None and style.bottom is None:
                raise ValueError(
                    f"height_in={style.height_in:g} is too small: titles, "
                    "notes and spacing alone need at least "
                    f"{top_block + bottom_block + minimum:.2f} in."
                )
            raise ValueError(
                f"The area between bottom and top is {max(available, 0):.2f} "
                "in; titles, notes and spacing alone need at least "
                f"{minimum:.2f} in."
            )

        if content_height(1.0) <= available:
            shrink = 1.0
        else:
            # Largest scale that fits (content height grows with it).
            low, high = _MIN_SHRINK, 1.0
            for _ in range(40):
                mid = (low + high) / 2
                if content_height(mid) <= available:
                    low = mid
                else:
                    high = mid
                if high - low < 1e-5:
                    break
            shrink = low

        heights, gap = measure(shrink)
        content = sum(heights) + gap * (grid.nrows - 1)
        free = max(0.0, available - content)
        extra = {"top": 0.0, "center": free / 2, "bottom": free}[style.valign]

        if shrink < 0.5:
            warnings.warn(
                f"Panels were reduced to {shrink:.0%} of their size to fit "
                f"height_in={style.height_in:g}; text may be hard to read. "
                "Increase height_in or reduce the content.",
                stacklevel=3,
            )
        if style.top is not None and region_top < top_block - 1e-6:
            warnings.warn(
                f"top={style.top:g} places the panels over the title area; "
                f"use top <= {1 - top_block / height:.3f}.",
                stacklevel=3,
            )
        if style.bottom is not None and region_bottom > height - bottom_block + 1e-6:
            warnings.warn(
                f"bottom={style.bottom:g} places the panels over the "
                f"sources; use bottom >= {bottom_block / height:.3f}.",
                stacklevel=3,
            )

    y_top_rule = style.pad_top_in
    y_header = style.pad_top_in + _GAP_AFTER_TOP_RULE
    y_bottom_rule = (
        height - style.pad_bottom_in - footer_block - _GAP_AFTER_BOTTOM_RULE
    )
    y_footer = y_bottom_rule + _GAP_AFTER_BOTTOM_RULE

    row_y: list[float] = []
    y = region_top + extra
    for row_height in heights:
        row_y.append(y)
        y += row_height + gap

    def fx(inches: float) -> float:
        return inches / width

    def fy(inches: float) -> float:
        return 1 - inches / height

    # -- draw ------------------------------------------------------------
    fig = Figure(
        figsize=(width, height),
        dpi=style.dpi,
        facecolor=style.background,
    )
    FigureCanvasAgg(fig)

    def rule(y_in: float) -> None:
        fig.add_artist(
            Line2D(
                [0, 1],
                [fy(y_in)] * 2,
                transform=fig.transFigure,
                color=style.line_color,
                linewidth=style.line_width,
            )
        )

    def text(
        x_in: float,
        y_in: float,
        value: str,
        size: float,
        color: str,
        weight: str = "normal",
    ) -> None:
        fig.text(
            fx(x_in),
            fy(y_in),
            value,
            ha="left",
            va="top",
            fontsize=size,
            fontweight=weight,
            family=font,
            color=color,
        )

    if style.top_line:
        rule(y_top_rule)
    if style.bottom_line:
        rule(y_bottom_rule)

    for k, line in enumerate(header_lines):
        text(
            left_in,
            y_header + k * _step(header_size, style),
            line,
            header_size,
            header_color,
            header_weight,
        )

    footer_step = _step(style.footer_size, style)

    for cell in cells:
        panel = cell.panel
        span = cell.span

        cell_top = row_y[span.row]
        cell_height = (
            sum(heights[span.row : span.row_end]) + gap * (span.rowspan - 1)
        )
        slack = max(0.0, cell_height - cell.need)
        y_text = cell_top + {
            "top": 0.0,
            "center": slack / 2,
            "bottom": slack,
        }[panel.valign]
        y_image = y_text + cell.head_h

        for line in cell.title:
            text(
                cell.x_table,
                y_text,
                line,
                cell.title_size,
                panel.title_color or style.title_color,
                panel.title_weight or style.title_weight,
            )
            y_text += _step(cell.title_size, style)

        for line in cell.subtitle:
            text(
                cell.x_table,
                y_text,
                line,
                style.subtitle_size,
                style.subtitle_color,
            )
            y_text += _step(style.subtitle_size, style)

        axes = fig.add_axes(
            [
                fx(cell.x_table),
                fy(y_image + cell.img_h),
                cell.img_w / width,
                cell.img_h / height,
            ]
        )
        axes.imshow(
            _resize(
                cell.image,
                max(1, round(cell.img_w * style.dpi)),
                max(1, round(cell.img_h * style.dpi)),
                style.resampling,
            ),
            interpolation="nearest",
            aspect="auto",
        )
        axes.axis("off")

        y_note = y_image + cell.img_h + _GAP_BEFORE_NOTES
        for line in cell.notes:
            text(
                cell.x_table,
                y_note,
                line,
                style.footer_size,
                style.footer_color,
            )
            y_note += footer_step

    for k, line in enumerate(footer_lines):
        text(
            left_in,
            y_footer + k * footer_step,
            line,
            style.footer_size,
            style.footer_color,
        )

    return fig
