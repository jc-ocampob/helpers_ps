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

        Every argument is optional: only the ones you pass are applied.
        Dictionaries hold plain CSS properties, for example
        ``{"background-color": "#12275A", "font-weight": "bold"}``. Calling
        ``style_table`` several times is fine: the rules are replayed in
        call order, so the latest call wins.

        Inside one call the rules are applied in this order. When two of
        them set the same CSS property, the later one wins (a color in
        ``column_header_styles`` beats one in ``header_styles``):

        1. ``font_family``, ``font_size``, ``text_color``,
           ``background_color``, ``text_align``: header, index and data
           cells.
        2. ``header_styles``, ``index_styles``, ``data_styles``: every cell
           of that kind.
        3. ``column_header_styles``: selected column headers.
        4. ``row_index_styles``: selected row-index labels.
        5. ``corner_styles``: the corner and the index-names row.

        Sparse MultiIndex rendering is preserved. See
        ``helpers_ps.DfStyling.style_table`` for the functional version.

        Parts of a table
        ----------------
        ::

            +----------+----------+----------+-------+-------+
            | corner   | corner   | corner   |  1M   |  3M   |  <- column headers
            +----------+----------+----------+-------+-------+
            | Metric   | Period   | Rating   |       |       |  <- index-names row
            +----------+----------+----------+-------+-------+
            | Δ Yield  | MTD      | AAA      |   5   |   8   |
            |          |          | AA+      |  -9   |  39   |
            +----------+----------+----------+-------+-------+
              ^ index cells                    ^ data cells

        * Column headers: ``header_styles``, ``column_header_styles``.
        * Index cells (all levels): ``index_styles``, ``row_index_styles``.
        * Data cells: ``data_styles``.
        * Corner cells and index-names row: ``corner_styles``. The
          index-names row is hidden by ``show_index_names=False``.

        Parameters
        ----------
        font_family : str | None, default None
            CSS font family of the header, index and data cells. A list is
            a fallback chain, e.g. ``"Inter, Arial, sans-serif"``. The
            titles, notes and sources drawn around the table use the sheet
            font instead (``config_layout(font_family=...)``).

        font_size : str | int | float | None, default None
            Font size of the header, index and data cells. A number means
            pixels (``11`` is ``"11px"``); a string may use any CSS unit
            (``"9pt"``, ``"0.8rem"``). With ``scale="natural"`` the size on
            the page is real (1 px = 0.75 pt, so 11 px = 8.25 pt). With the
            default ``scale="uniform"`` the table is resized to fill its
            cell, so ``font_size`` barely changes the final text size; it
            changes how heavy fixed-pixel borders look next to the text.

        text_color : str | None, default None
            Text color of the header, index and data cells.

        background_color : str | None, default None
            Background color of the header, index and data cells. It also
            covers the alternating row shading (``zebra``).

        text_align : str | None, default None
            ``"left"``, ``"center"`` or ``"right"`` for the header, index
            and data cells. Without it the table is right-aligned.

        header_styles : Mapping[str, str] | None, default None
            CSS for every column-header cell (the labels above the data).
            Header labels are bold by default; use
            ``{"font-weight": "normal"}`` to undo it. It does not reach the
            corner cells; use ``corner_styles``.

        index_styles : Mapping[str, str] | None, default None
            CSS for every row-index cell, at all index levels. Index labels
            are bold by default, like the headers.

        data_styles : Mapping[str, str] | None, default None
            CSS for every data cell.

        column_header_styles : Sequence[dict] | None, default None
            Rules for selected column headers. Each dictionary has:

            * ``"columns"``: one column label or a list of labels. With
              MultiIndex columns use complete labels as tuples. To style a
              group label of an upper level, the list must include the
              first column of that group (the one that carries the label).
            * ``"styles"``: the CSS to apply.
            * ``"level"`` (optional): header row to style. Default is the
              last one, the row of the labels closest to the data.

        row_index_styles : Sequence[dict] | None, default None
            Rules for selected row-index labels. Each dictionary has:

            * ``"values"``: one index value or a list of values.
            * ``"level"``: index level, as a position (``0`` is the outer
              level) or as its name (``"Period"``).
            * ``"styles"``: the CSS to apply.
            * ``"parent"`` (optional): tuple with the values of the outer
              levels, to style a repeated label only inside one section.

        show_index_names : bool, default True
            Show the row with the index level names (``Metric``,
            ``Period``, ``Rating``). ``False`` hides it without changing
            the DataFrame.

        corner_styles : Mapping[str, str] | None, default None
            CSS for the corner cells above the index and for the
            index-names row, including its empty cells under the column
            headers.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Notes
        -----
        * A value that does not exist in the table matches nothing and is
          ignored.
        * The header row is as tall as its tallest cell, corner included.
          If you lower the padding or font size of the header, give
          ``corner_styles`` the same values or the row stays tall. In the
          same way, a data row is as tall as its tallest cell, index
          included.
        * ``row_index_styles`` paints the index label only. To style the
          data cells of a row use ``highlight_rows`` or ``style_cells``.

        Examples
        --------
        The examples use a table with the index levels ``Metric``
        (``Δ Yield``, ``Δ Spreads``), ``Period`` (``MTD``, ``YTD``) and
        ``Rating`` (``AAA``, ``AA+``, ``AA``, ``A``), and the columns
        ``1M``, ``3M``, ``6M``, ``1Y``, ``3Y``, ``5Y``, ``10Y``.

        ``font_family``.

        >>> sheet.style_table(font_family="Inter, Arial, sans-serif")

        ``font_size``: a number is pixels, a string can use any CSS unit.

        >>> sheet.style_table(font_size=11)
        >>> sheet.style_table(font_size="9pt")

        ``text_color`` and ``background_color``.

        >>> sheet.style_table(text_color="#222222", background_color="white")

        ``text_align``: centered labels, right-aligned numbers (the data
        rule is applied after the general one).

        >>> sheet.style_table(
        ...     text_align="center",
        ...     data_styles={"text-align": "right"},
        ... )

        ``header_styles``: dark header with white text.

        >>> sheet.style_table(
        ...     header_styles={
        ...         "color": "white",
        ...         "background-color": "#12275A",
        ...     },
        ... )

        ``index_styles``: normal-weight index labels (bold is the default)
        on a grey background.

        >>> sheet.style_table(
        ...     index_styles={
        ...         "font-weight": "normal",
        ...         "background-color": "#F2F2F2",
        ...     },
        ... )

        ``data_styles``: a thin line under every row.

        >>> sheet.style_table(
        ...     data_styles={"border-bottom": "1px solid #E5E5E5"},
        ... )

        Shorter rows: lower the padding in the data cells and in the index
        cells, because the tallest cell sets the row height.

        >>> sheet.style_table(
        ...     data_styles={"padding": "0.25em 0.6em"},
        ...     index_styles={"padding": "0.25em 0.6em"},
        ... )

        ``column_header_styles``: color some headers differently. The
        general ``header_styles`` applies to all of them and the rules of
        the list are applied after it.

        >>> sheet.style_table(
        ...     header_styles={"color": "white", "background-color": "#12275A"},
        ...     column_header_styles=[
        ...         {
        ...             "columns": ["1M", "3M", "6M"],
        ...             "styles": {"background-color": "#3075DB"},
        ...         },
        ...         {
        ...             "columns": "10Y",
        ...             "styles": {"background-color": "#B7331F"},
        ...         },
        ...     ],
        ... )

        ``column_header_styles`` with MultiIndex columns, for example
        ``("Yield", "1M")``, ``("Yield", "3M")``, ``("Spread", "1M")`` and
        ``("Spread", "3M")``. ``"level": 0`` styles the group label
        (``Yield``), so list the group's columns starting with its first
        one; without ``"level"`` the rule styles the last level (``1M``,
        ``3M``).

        >>> sheet.style_table(
        ...     column_header_styles=[
        ...         {
        ...             "columns": [("Yield", "1M"), ("Yield", "3M")],
        ...             "level": 0,
        ...             "styles": {"background-color": "#B7331F", "color": "white"},
        ...         },
        ...         {
        ...             "columns": [("Spread", "1M"), ("Spread", "3M")],
        ...             "styles": {"background-color": "#3075DB", "color": "white"},
        ...         },
        ...     ],
        ... )

        ``row_index_styles``: the outer label, the labels of one section
        (``parent``) and every ``AAA`` of a level selected by name.

        >>> sheet.style_table(
        ...     row_index_styles=[
        ...         {
        ...             "values": "Δ Yield",
        ...             "level": 0,
        ...             "styles": {"background-color": "#B7331F", "color": "white"},
        ...         },
        ...         {
        ...             "values": ["MTD", "YTD"],
        ...             "level": 1,
        ...             "parent": ("Δ Yield",),
        ...             "styles": {"font-style": "italic"},
        ...         },
        ...         {
        ...             "values": "AAA",
        ...             "level": "Rating",
        ...             "styles": {"color": "#B7331F"},
        ...         },
        ...     ],
        ... )

        ``show_index_names``: hide the ``Metric`` / ``Period`` / ``Rating``
        row.

        >>> sheet.style_table(show_index_names=False)

        ``corner_styles``: paint the corner like the header, and keep the
        header row short by giving the corner the same padding.

        >>> sheet.style_table(
        ...     header_styles={
        ...         "color": "white",
        ...         "background-color": "#12275A",
        ...         "padding": "0.2em 0.5em",
        ...     },
        ...     corner_styles={
        ...         "background-color": "#12275A",
        ...         "padding": "0.2em 0.5em",
        ...     },
        ...     show_index_names=False,
        ... )

        Everything together: an institutional table.

        >>> sheet.style_table(
        ...     font_family="Inter, Arial",
        ...     font_size=11,
        ...     text_align="center",
        ...     header_styles={"color": "white", "background-color": "#12275A"},
        ...     corner_styles={"background-color": "#12275A"},
        ...     index_styles={"background-color": "#F2F2F2"},
        ...     data_styles={"border-bottom": "1px solid #E5E5E5"},
        ...     row_index_styles=[
        ...         {
        ...             "values": "Δ Yield",
        ...             "level": 0,
        ...             "styles": {"background-color": "#B7331F", "color": "white"},
        ...         },
        ...         {
        ...             "values": "Δ Spreads",
        ...             "level": 0,
        ...             "styles": {"background-color": "#163A87", "color": "white"},
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
