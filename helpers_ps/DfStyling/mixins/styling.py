from __future__ import annotations

import warnings
from collections.abc import Callable, Sequence
from typing import Any, Self

from pandas.io.formats.style import Styler

from ..formating import (
    border_cell,
    border_cells,
    border_columns,
    border_rows,
    highlight_columns,
    highlight_rows,
    style_cell,
    style_cells,
)
from ..mapping import background_color_by_range, text_color_by_range
from ..models import (
    BorderLineStyle,
    BorderPosition,
    ColorRanges,
    ColumnBorderPosition,
    CSSProperties,
    Label,
    LabelCollection,
    Labels,
    Op,
    OptionalCSSProperties,
    RowBorderPosition,
    StylerFunc,
)
from ..selectors import get_column_header_selectors, get_index_value_selectors
from ..table import HeaderStyleConfig, IndexStyleConfig, style_table
from .base import SheetBase


# ---------------------------------------------------------------------
# Operation functions (module level, so recipes stay inspectable)
# ---------------------------------------------------------------------

def _styler_method(
    styler: Styler,
    name: str,
    *args: Any,
    **kwargs: Any,
) -> Styler:
    """Call the ``Styler`` method ``name``."""
    return getattr(styler, name)(*args, **kwargs)


def _map_cells(
    styler: Styler,
    mapper: Callable[..., str],
    subset: Any,
    **kwargs: Any,
) -> Styler:
    """Apply an element-wise CSS function (``Styler.map``)."""
    method = getattr(styler, "map", None) or styler.applymap
    return method(mapper, subset=subset, **kwargs)


class StylingMixin(SheetBase):
    """
    Styling methods for the active tables.

    Every method records an operation in the recipe of each active table
    and returns the sheet. Operations are validated immediately (a wrong
    label fails on the offending line, not at render time) and replayed
    in order whenever the table is rendered.
    """

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _record(
        self,
        label: str,
        func: StylerFunc,
        *args: Any,
        _expects_styles: bool = False,
        **kwargs: Any,
    ) -> Self:
        """
        Append an operation to every active table, atomically.

        If the operation fails on any panel it is removed from all of
        them and the error is re-raised with the panel name attached.

        Parameters
        ----------
        label : str
            Name shown by ``recipe``.
        func : Callable
            ``func(styler, *args, **kwargs)`` returning a ``Styler``.
        _expects_styles : bool, default False
            For operations selecting rows or columns by label: warn when
            the operation added no CSS at all, which means that none of
            the labels matched (the underlying selectors ignore unknown
            labels silently).
        """
        panels = self._targets(tables_only=True)
        done = []

        for panel in panels:
            before = (
                len(panel.build_styler().table_styles or [])
                if _expects_styles
                else 0
            )

            panel.ops.append(Op(label, func, args, dict(kwargs)))
            done.append(panel)
            try:
                built = panel.build_styler()
            except Exception as error:
                for item in done:
                    item.ops.pop()
                if hasattr(error, "add_note"):
                    error.add_note(
                        f"while applying {label!r} to panel {panel.name!r}"
                    )
                raise

            if _expects_styles and len(built.table_styles or []) <= before:
                warnings.warn(
                    f"{label} matched nothing on panel {panel.name!r}; "
                    "check the labels.",
                    stacklevel=3,
                )
        return self

    def _warn_unmatched_style_table(
        self,
        row_index_styles: Sequence[IndexStyleConfig] | None,
        column_header_styles: Sequence[HeaderStyleConfig] | None,
    ) -> None:
        """Warn about targeted ``style_table`` rules that match nothing."""
        for panel in self._targets(tables_only=True):
            data = panel.build_styler().data

            for config in row_index_styles or ():
                if not get_index_value_selectors(
                    df=data,
                    values=config["values"],
                    level=config["level"],
                    parent=config.get("parent"),
                ):
                    warnings.warn(
                        f"row_index_styles {config['values']!r} matched "
                        f"nothing on panel {panel.name!r}; check the "
                        "values, level and parent.",
                        stacklevel=3,
                    )

            for config in column_header_styles or ():
                if not get_column_header_selectors(
                    df=data,
                    columns=config["columns"],
                    header_level=config.get("level"),
                ):
                    warnings.warn(
                        f"column_header_styles {config['columns']!r} "
                        f"matched nothing on panel {panel.name!r}; check "
                        "the columns and level.",
                        stacklevel=3,
                    )

    def clear_styles(self) -> Self:
        """
        Remove every recorded operation from the active tables.

        Returns
        -------
        TableSheet
            The sheet, for chaining.
        """
        for panel in self._targets(tables_only=True):
            panel.ops.clear()
        return self

    def recipe(self) -> dict[str, list[str]]:
        """
        Describe the recorded operations of every table.

        Returns
        -------
        dict[str, list[str]]
            Operation labels, in order, by panel name.
        """
        return {
            panel.name: [op.label for op in panel.ops]
            for panel in self._panels
            if panel.kind == "table"
        }

    # ------------------------------------------------------------------
    # General appearance
    # ------------------------------------------------------------------

    def style_table(
        self,
        font_family: str | None = None,
        font_size: str | int | float | None = None,
        text_color: str | None = None,
        background_color: str | None = None,
        text_align: str | None = None,
        header_styles: CSSProperties | None = None,
        index_styles: CSSProperties | None = None,
        data_styles: CSSProperties | None = None,
        column_header_styles: Sequence[HeaderStyleConfig] | None = None,
        row_index_styles: Sequence[IndexStyleConfig] | None = None,
        show_index_names: bool = True,
        corner_styles: CSSProperties | None = None,
    ) -> Self:
        """
        Configure the general appearance of the active tables.

        See ``helpers_ps.DfStyling.style_table`` for the meaning of every
        parameter. Sparse MultiIndex rendering is preserved.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Examples
        --------
        >>> sheet.style_table(
        ...     font_family="Inter, Arial",
        ...     font_size=11,
        ...     text_align="center",
        ...     header_styles={"color": "white", "background-color": "#12275A"},
        ...     row_index_styles=[
        ...         {
        ...             "values": "Δ Yield",
        ...             "level": 0,
        ...             "styles": {"background-color": "#B7331F", "color": "white"},
        ...         },
        ...     ],
        ...     show_index_names=False,
        ... )
        """
        self._record(
            "style_table",
            style_table,
            font_family=font_family,
            font_size=font_size,
            text_color=text_color,
            background_color=background_color,
            text_align=text_align,
            header_styles=header_styles,
            index_styles=index_styles,
            data_styles=data_styles,
            column_header_styles=column_header_styles,
            row_index_styles=row_index_styles,
            show_index_names=show_index_names,
            corner_styles=corner_styles,
        )
        self._warn_unmatched_style_table(
            row_index_styles, column_header_styles
        )
        return self

    def format(
        self,
        formatter: Any = None,
        subset: Any = None,
        **kwargs: Any,
    ) -> Self:
        """
        Format the displayed values (``Styler.format``).

        Parameters
        ----------
        formatter : str | callable | dict | None, default None
            For example ``"{:.1f}"``, ``"{:,.0f}"`` or ``{"col": "{:.1%}"}``.
        subset : label | slice | None, default None
            Cells to format. Use ``pandas.IndexSlice`` for MultiIndex.
        **kwargs
            Any other ``Styler.format`` option (``na_rep``, ``precision``,
            ``decimal``, ``thousands``, ``escape``...).

        Returns
        -------
        TableSheet
            The sheet, for chaining.
        """
        return self._record(
            "format",
            _styler_method,
            "format",
            formatter,
            subset=subset,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Cells
    # ------------------------------------------------------------------

    def style_cell(
        self,
        row: Label,
        column: Label,
        styles: CSSProperties,
    ) -> Self:
        """Apply CSS to one cell. See ``helpers_ps.DfStyling.style_cell``."""
        return self._record(
            "style_cell", style_cell, row=row, column=column, styles=styles
        )

    def style_cells(
        self,
        rows: LabelCollection,
        columns: LabelCollection,
        styles: CSSProperties,
    ) -> Self:
        """Apply CSS to rows x columns. See ``helpers_ps.DfStyling.style_cells``."""
        return self._record(
            "style_cells",
            style_cells,
            rows=rows,
            columns=columns,
            styles=styles,
        )

    def border_cell(
        self,
        row: Label,
        column: Label,
        position: BorderPosition = "top",
        width: str = "1px",
        color: str = "black",
        line_style: BorderLineStyle = "solid",
    ) -> Self:
        """Border one side of a cell. See ``helpers_ps.DfStyling.border_cell``."""
        return self._record(
            "border_cell",
            border_cell,
            row=row,
            column=column,
            position=position,
            width=width,
            color=color,
            line_style=line_style,
        )

    def border_cells(
        self,
        rows: LabelCollection,
        columns: LabelCollection,
        position: BorderPosition = "top",
        width: str = "1px",
        color: str = "black",
        line_style: BorderLineStyle = "solid",
    ) -> Self:
        """Border one side of many cells. See ``helpers_ps.DfStyling.border_cells``."""
        return self._record(
            "border_cells",
            border_cells,
            _expects_styles=True,
            rows=rows,
            columns=columns,
            position=position,
            width=width,
            color=color,
            line_style=line_style,
        )

    # ------------------------------------------------------------------
    # Rows and columns
    # ------------------------------------------------------------------

    def highlight_rows(
        self,
        rows: Labels,
        styles: OptionalCSSProperties = None,
        include_index: bool = True,
        index_level: int | None = None,
    ) -> Self:
        """Highlight rows. See ``helpers_ps.DfStyling.highlight_rows``."""
        return self._record(
            "highlight_rows",
            highlight_rows,
            _expects_styles=True,
            rows=rows,
            styles=styles,
            include_index=include_index,
            index_level=index_level,
        )

    def highlight_columns(
        self,
        columns: Labels,
        styles: OptionalCSSProperties = None,
        include_header: bool = True,
        header_level: int | None = None,
    ) -> Self:
        """Highlight columns. See ``helpers_ps.DfStyling.highlight_columns``."""
        return self._record(
            "highlight_columns",
            highlight_columns,
            _expects_styles=True,
            columns=columns,
            styles=styles,
            include_header=include_header,
            header_level=header_level,
        )

    def border_rows(
        self,
        rows: Labels,
        position: RowBorderPosition = "bottom",
        styles: OptionalCSSProperties = None,
    ) -> Self:
        """
        Add a horizontal border across rows.

        See ``helpers_ps.DfStyling.border_rows``.

        Examples
        --------
        >>> sheet.border_rows(
        ...     [("Δ Yield", "MTD", "A")],
        ...     styles={"width": "2px", "color": "#12275A"},
        ... )
        """
        return self._record(
            "border_rows",
            border_rows,
            _expects_styles=True,
            rows=rows,
            position=position,
            styles=styles,
        )

    def border_columns(
        self,
        columns: Labels,
        position: ColumnBorderPosition = "right",
        include_header: bool = True,
        header_level: int | None = None,
        styles: OptionalCSSProperties = None,
    ) -> Self:
        """Add a vertical border to columns. See ``helpers_ps.DfStyling.border_columns``."""
        return self._record(
            "border_columns",
            border_columns,
            _expects_styles=True,
            columns=columns,
            position=position,
            include_header=include_header,
            header_level=header_level,
            styles=styles,
        )

    # ------------------------------------------------------------------
    # Conditional colors
    # ------------------------------------------------------------------

    def text_color_by_range(
        self,
        ranges: ColorRanges,
        subset: Any = None,
    ) -> Self:
        """
        Color the text of each cell by the numeric range it falls in.

        Parameters
        ----------
        ranges : Mapping[tuple[Real, Real], str]
            ``{(lower, upper): css_color}``, lower-inclusive and
            upper-exclusive. Overlaps use the first match.
        subset : label | slice | None, default None
            Cells to color. ``None`` colors every data cell.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Examples
        --------
        >>> import numpy as np
        >>> sheet.text_color_by_range(
        ...     {(-np.inf, 0): "#C0392B", (0, np.inf): "#1E8449"}
        ... )
        """
        return self._record(
            "text_color_by_range",
            _map_cells,
            text_color_by_range,
            subset,
            ranges=ranges,
        )

    def background_color_by_range(
        self,
        ranges: ColorRanges,
        subset: Any = None,
    ) -> Self:
        """
        Color the background of each cell by the numeric range it falls in.

        Same parameters as ``text_color_by_range``.
        """
        return self._record(
            "background_color_by_range",
            _map_cells,
            background_color_by_range,
            subset,
            ranges=ranges,
        )

    # ------------------------------------------------------------------
    # Escape hatch
    # ------------------------------------------------------------------

    def apply_styler(
        self,
        func: str | StylerFunc,
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        """
        Apply any ``Styler`` operation.

        Parameters
        ----------
        func : str | Callable
            Name of a ``Styler`` method, or a function
            ``func(styler, *args, **kwargs)`` that returns a ``Styler``.
        *args, **kwargs
            Forwarded to the method or function.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Examples
        --------
        >>> sheet.apply_styler("background_gradient", cmap="Blues", axis=None)
        >>> sheet.apply_styler(lambda s: s.set_caption("Daily changes"))
        """
        if isinstance(func, str):
            return self._record(func, _styler_method, func, *args, **kwargs)

        if not callable(func):
            raise TypeError("func must be a Styler method name or a callable.")

        label = getattr(func, "__name__", "custom")
        return self._record(label, func, *args, **kwargs)
