from __future__ import annotations

from typing import Any, Self

from pandas import DataFrame, Series
from pandas.io.formats.style import Styler

from ..models import (
    ALIGNS,
    SCALE_MODES,
    VALIGNS,
    Align,
    GridLayout,
    Key,
    Notes,
    Panel,
    ScaleMode,
    VAlign,
)
from ..rendering.images import figure_of, load_static_image
from .base import SheetBase


def _as_list(notes: Notes) -> list[str]:
    """Normalize one note, several notes or ``None`` to a list."""
    if notes is None:
        return []
    if isinstance(notes, str):
        return [notes]
    return [str(note) for note in notes]


class PanelMixin(SheetBase):
    """Create, select, remove and describe panels."""

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def _new_name(self, name: str | None) -> str:
        if name is None:
            name = f"panel_{self._counter}"
        elif not isinstance(name, str) or not name:
            raise TypeError("A panel name must be a non-empty str.")
        elif name == ".":
            raise ValueError("'.' is reserved for empty layout cells.")

        if any(panel.name == name for panel in self._panels):
            raise ValueError(f"A panel named {name!r} already exists.")

        self._counter += 1
        return name

    def add_table(
        self,
        dataframe: DataFrame | Styler | Series,
        name: str | None = None,
        *,
        activate: bool = True,
    ) -> Self:
        """
        Add a table panel.

        Parameters
        ----------
        dataframe : pandas.DataFrame | pandas.io.formats.style.Styler | pandas.Series
            Table source. A ``Styler`` is used as the starting point of
            the recipe (it is copied, never modified).
        name : str | None, default None
            Panel name. Defaults to ``"panel_<n>"``.
        activate : bool, default True
            Make the new panel the only active one, so the next styling
            calls apply to it.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Examples
        --------
        >>> sheet = (
        ...     TableSheet(df_yield, names=["yield"])
        ...     .add_table(df_spreads, name="spreads")
        ...     .style_table(font_size=11)     # applies to "spreads"
        ... )
        """
        if isinstance(dataframe, Series):
            dataframe = dataframe.to_frame()

        if not isinstance(dataframe, (DataFrame, Styler)):
            raise TypeError(
                "dataframe must be a pandas DataFrame, Styler or Series, "
                f"got {type(dataframe).__name__}."
            )

        panel = Panel(
            name=self._new_name(name),
            kind="table",
            source=dataframe,
        )
        self._panels.append(panel)

        if activate:
            self._active = [panel.name]
        return self

    def add_image(
        self,
        image: Any,
        name: str | None = None,
        *,
        activate: bool = True,
    ) -> Self:
        """
        Add an image panel, typically a chart.

        Parameters
        ----------
        image : numpy.ndarray | PIL.Image.Image | bytes | str | pathlib.Path | matplotlib.figure.Figure | object
            Image source. Figures, and objects exposing one as ``_fig``
            (such as ``GraphMtplt``), are rasterized at render time with
            the sheet ``dpi``, so they always reflect their current state.
            Arrays, PIL images, encoded bytes and file paths are loaded
            immediately.
        name : str | None, default None
            Panel name. Defaults to ``"panel_<n>"``.
        activate : bool, default True
            Make the new panel the only active one.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Examples
        --------
        >>> sheet.add_image(graph, name="curve").panel(title="Yield curve")
        """
        array = load_static_image(image)

        if array is not None:
            source: Any = array
        else:
            source = figure_of(image)
            if source is None:
                raise TypeError(
                    "image must be an array, PIL image, bytes, path, "
                    "matplotlib Figure or an object with a Figure in "
                    f"'_fig', got {type(image).__name__}."
                )

        panel = Panel(
            name=self._new_name(name),
            kind="image",
            source=source,
        )
        self._panels.append(panel)

        if activate:
            self._active = [panel.name]
        return self

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def on(self, *keys: Key) -> Self:
        """
        Select the panels that the next calls apply to.

        Parameters
        ----------
        *keys : int | str
            Panel positions (negative values allowed) or names. With no
            arguments, every panel is selected.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Examples
        --------
        >>> sheet.on("yield").style_table(font_size=11)
        >>> sheet.on("yield", "spreads").style_table(font_family="Arial")
        >>> sheet.on().style_table(text_align="center")       # all panels
        """
        if not self._panels:
            raise ValueError("The sheet has no panels yet.")

        if not keys:
            self._active = [panel.name for panel in self._panels]
        else:
            names: list[str] = []
            for key in keys:
                name = self._find(key).name
                if name not in names:
                    names.append(name)
            self._active = names
        return self

    def remove(self, *keys: Key) -> Self:
        """
        Remove panels (and their cells in an explicit layout).

        Rows and columns of an explicit layout that become empty are
        dropped, together with their ``width_ratios``.

        Parameters
        ----------
        *keys : int | str
            Panel positions or names.

        Returns
        -------
        TableSheet
            The sheet, for chaining.
        """
        doomed = {self._find(key).name for key in keys}

        self._panels = [p for p in self._panels if p.name not in doomed]

        if self._mosaic is not None:
            self._mosaic, self._width_ratios = GridLayout.without(
                self._mosaic, self._width_ratios, doomed
            )

        self._active = [name for name in self._active if name not in doomed]
        if not self._active and self._panels:
            self._active = [self._panels[0].name]
        return self

    @property
    def panel_names(self) -> list[str]:
        """Names of the panels, in creation order."""
        return [panel.name for panel in self._panels]

    # ------------------------------------------------------------------
    # Panel texts and geometry
    # ------------------------------------------------------------------

    def panel(
        self,
        *,
        title: str | None = None,
        subtitle: str | None = None,
        notes: Notes = None,
        align: Align | None = None,
        valign: VAlign | None = None,
        scale: ScaleMode | None = None,
        title_size: float | None = None,
        title_color: str | None = None,
        title_weight: str | None = None,
    ) -> Self:
        """
        Set texts and geometry of the active panels.

        ``None`` leaves a setting unchanged. Use an empty string (or an
        empty list for ``notes``) to clear it. Column widths are set with
        ``layout(width_ratios=...)``.

        Parameters
        ----------
        title : str | None, default None
            Text above the table.
        subtitle : str | None, default None
            Smaller text under the title.
        notes : str | Sequence[str] | None, default None
            Notes below the table. Replaces the previous ones.
        align : {"left", "center", "right"} | None, default None
            Horizontal alignment when the panel is narrower than its cell.
        valign : {"top", "center", "bottom"} | None, default None
            Vertical alignment when its cell is taller than the panel,
            for example a panel that spans several rows.
        scale : {"uniform", "fit", "natural"} | None, default None
            Overrides the sheet ``scale`` for these panels, e.g.
            ``scale="fit"`` to make a chart fill its cell width.
        title_size, title_color, title_weight : optional
            Overrides of the sheet title style for these panels.

        Returns
        -------
        TableSheet
            The sheet, for chaining.

        Examples
        --------
        >>> sheet.on("yield").panel(
        ...     title="Δ Yield",
        ...     subtitle="Basis points",
        ...     notes="MTD: month to date.",
        ... )
        >>> sheet.on("curve").panel(scale="fit", valign="center")
        """
        if align is not None and align not in ALIGNS:
            raise ValueError(f"align must be one of {ALIGNS}, got {align!r}.")
        if valign is not None and valign not in VALIGNS:
            raise ValueError(f"valign must be one of {VALIGNS}, got {valign!r}.")
        if scale is not None and scale not in SCALE_MODES:
            raise ValueError(
                f"scale must be one of {SCALE_MODES}, got {scale!r}."
            )

        for panel in self._targets():
            if title is not None:
                panel.title = title
            if subtitle is not None:
                panel.subtitle = subtitle
            if notes is not None:
                panel.notes = _as_list(notes)
            if align is not None:
                panel.align = align
            if valign is not None:
                panel.valign = valign
            if scale is not None:
                panel.scale = scale
            if title_size is not None:
                panel.title_size = title_size
            if title_color is not None:
                panel.title_color = title_color
            if title_weight is not None:
                panel.title_weight = title_weight
        return self
