from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Unpack

from pandas import DataFrame, Series
from pandas.io.formats.style import Styler

from .mixins import LayoutMixin, OutputMixin, PanelMixin, StylingMixin
from .models import Header, Renderer, SheetStyle, SheetStyleOptions
from .rendering.browser import PlaywrightRenderer
from .rendering.cache import DEFAULT_CACHE, RenderCache

TableLike = DataFrame | Styler | Series


class TableSheet(PanelMixin, StylingMixin, LayoutMixin, OutputMixin):
    """
    Build an institutional image from one or several styled tables.

    The sheet holds the DataFrames, records the styling you apply to each
    one, and composes everything (titles, notes, sources) into a single
    image. Like ``GraphMtplt``, every method returns the sheet, so calls
    can be chained.

    How it works
    ------------
    * Each table is a *recipe*: its source plus the ordered list of
      operations applied through the styling methods. The ``Styler`` is
      rebuilt from the recipe whenever needed, so re-running a notebook
      cell never accumulates CSS.
    * Tables are rendered by a headless browser, **all in one batch**, and
      cached by content: changing a title, the layout or the spacing never
      renders again; changing one table renders only that table.
    * Panels (tables and charts) are arranged on a grid (``layout``) that
      can span rows and columns, and positioned with ``subplots_adjust``.
    * ``preview()`` shows the result in the notebook, ``save()`` writes it.

    Parameters
    ----------
    dataframe : DataFrame | Styler | Series | Mapping | Sequence | None, default None
        One table, a list of tables, or a ``{name: table}`` mapping. More
        can be added later with ``add_table``. The first panel is active.
    names : Sequence[str] | None, default None
        Panel names for a list input. Defaults to ``"panel_<n>"``.
    style : SheetStyle | None, default None
        Base visual parameters.
    renderer : Callable | None, default None
        ``renderer(documents, dpi) -> images``. Defaults to
        ``PlaywrightRenderer()``.
    cache : RenderCache | None, default None
        Cache of rendered tables. ``None`` uses the process-wide cache
        shared by every sheet; ``RenderCache(max_mb=0)`` disables caching.
    nrows, ncols : int | None, default None
        Shape of the grid the panels are placed on, in creation order.
        ``nrows=1`` puts the panels side by side, ``ncols=1`` (the
        default) stacks them. See ``layout`` for explicit arrangements.
    width_ratios : Sequence[float] | None, default None
        Relative width of every grid column.
    **style_options
        Any ``SheetStyle`` field, e.g. ``width_in=11`` or ``height_in=7.5``.

    Examples
    --------
    One table.

    >>> sheet = (
    ...     TableSheet(df, width_in=7)
    ...     .style_table(font_size=11, text_align="center")
    ...     .format("{:.0f}")
    ...     .panel(title="Δ Yield", subtitle="Basis points")
    ...     .add_source("Fuente: Example Data")
    ... )
    >>> sheet.preview()
    >>> sheet.save("yield.png")

    Two tables side by side and a chart that spans both rows on the right.

    >>> sheet = (
    ...     TableSheet({"yield": df_yield, "spreads": df_spreads}, width_in=13)
    ...     .on().style_table(font_size=11, text_align="center")      # both
    ...     .on("yield").panel(title="Δ Yield")
    ...     .on("spreads").panel(title="Δ Spreads")
    ...     .add_image(graph, name="curve").panel(title="Yield curve")
    ...     .layout([["yield", "curve"], ["spreads", "curve"]], width_ratios=[3, 2])
    ...     .subplots_adjust(wspace=0.1, hspace=0.2)
    ...     .add_title("Renta fija local")
    ...     .add_source("Fuente: Example Data")
    ...     .save(dir="out", name="lamina")
    ... )
    """

    def __init__(
        self,
        dataframe: TableLike | Mapping[str, TableLike] | Sequence[TableLike] | None = None,
        *,
        names: Sequence[str] | None = None,
        style: SheetStyle | None = None,
        renderer: Renderer | None = None,
        cache: RenderCache | None = None,
        nrows: int | None = None,
        ncols: int | None = None,
        width_ratios: Sequence[float] | None = None,
        **style_options: Unpack[SheetStyleOptions],
    ) -> None:
        self._panels = []
        self._active = []
        self._style = style or SheetStyle()
        self._header: Header | None = None
        self._notes = []
        self._sources = []
        self._mosaic = None
        self._shape = None
        self._width_ratios = None
        self._renderer = renderer or PlaywrightRenderer()
        self._cache = DEFAULT_CACHE if cache is None else cache
        self._counter = 0
        self._last_path: Path | None = None

        if style_options:
            self.config_layout(**style_options)

        for name, table in self._normalize_input(dataframe, names):
            self.add_table(table, name=name, activate=False)

        if self._panels:
            self._active = [self._panels[0].name]

        if nrows is not None or ncols is not None or width_ratios is not None:
            self.layout(nrows=nrows, ncols=ncols, width_ratios=width_ratios)

    @staticmethod
    def _normalize_input(
        dataframe: object,
        names: Sequence[str] | None,
    ) -> list[tuple[str | None, TableLike]]:
        """Return ``(name, table)`` pairs for every accepted input shape."""
        if dataframe is None:
            if names:
                raise ValueError("names given without any dataframe.")
            return []

        if isinstance(dataframe, (DataFrame, Styler, Series)):
            items = [dataframe]
        elif isinstance(dataframe, Mapping):
            if names is not None:
                raise TypeError(
                    "names cannot be used with a mapping; its keys are "
                    "the panel names."
                )
            return [(str(key), value) for key, value in dataframe.items()]
        else:
            items = list(dataframe)  # type: ignore[call-overload]

        if names is None:
            return [(None, item) for item in items]

        if len(names) != len(items):
            raise ValueError(
                f"names has {len(names)} entries for {len(items)} tables."
            )
        return list(zip(names, items))
