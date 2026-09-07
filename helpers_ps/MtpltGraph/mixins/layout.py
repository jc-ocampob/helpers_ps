from __future__ import annotations
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from typing import Self
import numpy as np
from typing import Literal
from ..models import FigureTitle, FigureSubtitle, FigureSource

class LayoutMixin:
    """
    Figure layout and presentation utilities.

    This mixin provides high-level helpers for managing figure
    structure, titles, subtitles, source notes, subplot layouts,
    and overall visual presentation.

    Features
    --------
    - Figure-level titles and subtitles.
    - Source notes and footers.
    - Standard and GridSpec subplot layouts.
    - Plot-level titles.
    - Global subplot adjustments.

    Notes
    -----
    Methods in this mixin operate primarily at the figure level
    rather than on individual chart series.
    """

    def add_title(
        self,
        text: str,
        *,
        x: float = 0.02,
        y: float = 0.93,
        fontsize: int = 12,
        color: str = "#000000",
        fontweight: str = "bold",
        ha: str = "left",
        va: str = "top",
        **kwargs,
    ) -> Self:
        """
        Add a figure-level title.

        This method places a title on the figure canvas rather than
        inside the active axis. Figure-level titles remain consistent
        across multi-panel layouts and are positioned independently
        from subplot content.

        Parameters
        ----------
        text : str
            Title text.

        x : float, default 0.02
            Horizontal figure coordinate.

        y : float, default 0.93
            Vertical figure coordinate.

        fontsize : int, default 12
            Title font size.

        color : str, default "#000000"
            Title color.

        fontweight : str, default "bold"
            Font weight.

        ha : str, default "left"
            Horizontal alignment.

        va : str, default "top"
            Vertical alignment.

        **kwargs
            Additional keyword arguments passed to
            `Figure.text()`.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Examples
        --------
        >>> (
        ...     graph
        ...     .add_title("Global Equity Performance")
        ... )
        """

        self._ax.set_title("")

        self._fig.text(
            x,
            y,
            text,
            fontsize=fontsize,
            color=color,
            fontweight=fontweight,
            ha=ha,
            va=va,
            **kwargs,
        )

        self._title = FigureTitle(
            text=text,
            x=x,
            y=y,
            fontsize=fontsize,
            color=color,
            fontweight=fontweight,
            ha=ha,
            va=va,
        )

        return self


    def add_subtitle(
        self,
        text: str,
        *,
        x: float = 0.02,
        y: float = 0.88,
        fontsize: int = 9,
        color: str = "#333333",
        fontweight: str = "normal",
        ha: str = "left",
        va: str = "top",
        **kwargs,
    ) -> Self:
        """
        Add a figure-level subtitle.

        This method places descriptive text below the figure title.
        Subtitles are useful for additional context such as date
        ranges, portfolio names, scenario descriptions, or report
        notes.

        Parameters
        ----------
        text : str
            Subtitle text.

        x : float, default 0.02
            Horizontal figure coordinate.

        y : float, default 0.88
            Vertical figure coordinate.

        fontsize : int, default 9
            Subtitle font size.

        color : str, default "#333333"
            Subtitle color.

        fontweight : str, default "normal"
            Font weight.

        ha : str, default "left"
            Horizontal alignment.

        va : str, default "top"
            Vertical alignment.

        **kwargs
            Additional keyword arguments passed to
            `Figure.text()`.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Examples
        --------
        >>> (
        ...     graph
        ...     .add_subtitle(
        ...         "Performance since inception"
        ...     )
        ... )
        """

        self._fig.text(
            x,
            y,
            text,
            fontsize=fontsize,
            color=color,
            fontweight=fontweight,
            ha=ha,
            va=va,
            **kwargs,
        )

        self._subtitle = FigureSubtitle(
            text=text,
            x=x,
            y=y,
            fontsize=fontsize,
            color=color,
            fontweight=fontweight,
            ha=ha,
            va=va,
        )

        return self


    def add_source(
        self,
        text: str | list | None = None,
        x: float = 0.02,
        y: float = 0.022,
        fontsize: float = 6,
        color: str = "#606060",
        line_spacing: float = 0.022,
    ) -> Self:
        """
        Add source notes or footer text to the figure.

        This method displays one or more text lines in the footer area
        of the figure. Source notes are typically used for data sources,
        disclosures, assumptions, methodology descriptions, or report
        footnotes.

        Parameters
        ----------
        text : str, list, or None, optional
            Source text to display.

        x : float, default 0.02
            Horizontal figure coordinate.

        y : float, default 0.022
            Vertical position of the first source line.

        fontsize : float, default 6
            Text font size.

        color : str, default "#606060"
            Text color.

        line_spacing : float, default 0.022
            Vertical spacing between lines.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Raises
        ------
        ValueError
            If more than four source lines are provided.

        Examples
        --------
        Single source:

        >>> (
        ...     graph
        ...     .add_source(
        ...         "Source: Bloomberg"
        ...     )
        ... )

        Multiple sources:

        >>> (
        ...     graph
        ...     .add_source([
        ...         "Source: Bloomberg",
        ...         "Prepared by Portfolio Solutions"
        ...     ])
        ... )
        """
        
        if text is None:
            return self
        
        if isinstance(text, str):
            lines = [text]
        else:
            lines = list(text)

        if len(lines) > 4:
            raise ValueError("Too many lines for source. Max 4.")
        elif len(lines) < 4:
            lines += [""] * (4 - len(lines))

        for i, line in enumerate(lines[::-1]):
            self._fig.text(
                x,
                y + i * line_spacing,
                line,
                ha="left",
                va="bottom",
                fontsize=fontsize,
                color=color
            )

        self._source = FigureSource(
            text=text,
            x=x,
            y=y,
            fontsize=fontsize,
            color=color,
            line_spacing=line_spacing,
        )

        return self


    def plot(
        self,
        figsize: tuple[float, float] = (6.00, 4.80),
        color: str = "#D5D5D5",
        researchtype: bool = True,
        lw: float = 0.8,
        nrows: int = 1,
        ncols: int = 1,
        sharex: bool = False,
        sharey: bool = False,
        dpi: int | None = None,
        height_ratios: list[float] | None = None,
        width_ratios: list[float] | None = None,
        hspace: float | None = None,
        wspace: float | None = None
    ) -> Self:
        """
        Create the base figure and subplot layout.

        This method initializes the Matplotlib figure, subplot grid,
        and internal chart metadata. It is the starting point for
        all chart construction workflows.

        The layout can be created using either a standard subplot
        configuration or a custom GridSpec configuration with
        user-defined spacing and size ratios.

        Parameters
        ----------
        figsize : tuple[float, float], default (6.00, 4.80)
            Figure size in inches.

        color : str, default "#D5D5D5"
            Color of the decorative figure divider lines.

        researchtype : bool, default True
            Whether to add institutional-style divider lines.

        lw : float, default 0.8
            Width of the decorative divider lines.

        nrows : int, default 1
            Number of subplot rows.

        ncols : int, default 1
            Number of subplot columns.

        sharex : bool, default False
            Whether subplots share the x-axis.

        sharey : bool, default False
            Whether subplots share the y-axis.

        dpi : int or None, optional
            Figure DPI.

        height_ratios : list[float] or None, optional
            Relative row heights for GridSpec layouts.

        width_ratios : list[float] or None, optional
            Relative column widths for GridSpec layouts.

        hspace : float or None, optional
            Vertical spacing between subplots.

        wspace : float or None, optional
            Horizontal spacing between subplots.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Examples
        --------
        Standard figure:

        >>> (
        ...     graph
        ...     .plot()
        ... )

        Create a 2x2 layout:

        >>> (
        ...     graph
        ...     .plot(
        ...         nrows=2,
        ...         ncols=2
        ...     )
        ... )

        Custom GridSpec layout:

        >>> (
        ...     graph
        ...     .plot(
        ...         nrows=2,
        ...         ncols=1,
        ...         height_ratios=[3, 1]
        ...     )
        ... )
        """
        
        # -------------------------------------------------
        # 1. Crear figura + axes
        # -------------------------------------------------
        use_gridspec = any([
            height_ratios is not None,
            width_ratios is not None,
            hspace is not None,
            wspace is not None,
            dpi is not None
        ])

        if not use_gridspec:
            fig, axes = plt.subplots(
                nrows=nrows,
                ncols=ncols,
                figsize=figsize,
                sharex=sharex,
                sharey=sharey
            )
        else:
            fig = plt.figure(figsize=figsize, dpi=dpi)

            gs_kwargs = {
                "nrows": nrows,
                "ncols": ncols
            }

            if height_ratios is not None:
                gs_kwargs["height_ratios"] = height_ratios

            if width_ratios is not None:
                gs_kwargs["width_ratios"] = width_ratios

            if hspace is not None:
                gs_kwargs["hspace"] = hspace

            if wspace is not None:
                gs_kwargs["wspace"] = wspace

            gs = fig.add_gridspec(**gs_kwargs)

            axes = []
            first_ax = None

            for r in range(nrows):
                row_axes = []
                for c in range(ncols):
                    subplot_kwargs = {}

                    if first_ax is not None:
                        if sharex:
                            subplot_kwargs["sharex"] = first_ax
                        if sharey:
                            subplot_kwargs["sharey"] = first_ax

                    ax = fig.add_subplot(gs[r, c], **subplot_kwargs)

                    if first_ax is None:
                        first_ax = ax

                    row_axes.append(ax)

                axes.append(row_axes)

            if nrows == 1 and ncols == 1:
                axes = axes[0][0]
            else:
                axes = np.array(axes, dtype=object)

        # -------------------------------------------------
        # 2. Guardar figura
        # -------------------------------------------------
        self._generate_metadata(
            fig,
            axes,
            nrows,
            ncols
        )

        # -------------------------------------------------
        # 5. Líneas decorativas de figura
        # -------------------------------------------------
        if researchtype:
            self._fig.add_artist(
                Line2D(
                    [0.0, 1.0], [0.95, 0.95],
                    transform=self._fig.transFigure,
                    color=color, lw=lw
                )
            )

            self._fig.add_artist(
                Line2D(
                    [0.0, 1.0], [0.12, 0.12],
                    transform=self._fig.transFigure,
                    color=color, lw=lw
                )
            )

        # -------------------------------------------------
        # 6. Ajustes globales
        # -------------------------------------------------
        # Si no usas gridspec custom, mantén el comportamiento original
        if not use_gridspec:
            self._fig.subplots_adjust(
                left=0.15,
                right=0.93,
                top=0.80,
                bottom=0.30
            )

        return self


    def subplot_adjust(
            self,
            **kwargs
    ) -> Self:
        """
        Adjust subplot spacing and margins.

        This is a thin wrapper around Matplotlib's
        `Figure.subplots_adjust()` method and can be used to
        fine-tune figure spacing after creation.

        Parameters
        ----------
        **kwargs
            Keyword arguments accepted by
            `Figure.subplots_adjust()`.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Examples
        --------
        >>> (
        ...     graph
        ...     .subplot_adjust(
        ...         left=0.10,
        ...         right=0.95
        ...     )
        ... )
        """
        
        self._fig.subplots_adjust(**kwargs)

        return self

    # -----
    # Plot level layout
    # -----
    def add_plot_title(
            self,
            text: str,
            loc: Literal["left", "right", "center"] = "center",
            fontsize: int =7, 
            fontweight: Literal["bold", "semibold", "normal"] = "bold", 
            fontstyle: Literal["normal", "italic"] = "normal", 
            color:str = "black", 
            pad: int = 3,
            y: int = 1.0
    ) -> Self:
        """
        Add a title to the active subplot.

        Unlike `add_title()`, which operates at the figure level,
        this method places the title directly on the current axis.
        It is useful for multi-panel charts where each subplot
        requires its own title.

        Parameters
        ----------
        text : str
            Plot title text.

        loc : {"left", "right", "center"}, default "center"
            Title alignment.

        fontsize : int, default 7
            Title font size.

        fontweight : {"bold", "semibold", "normal"}, default "bold"
            Font weight.

        fontstyle : {"normal", "italic"}, default "normal"
            Font style.

        color : str, default "black"
            Title color.

        pad : int, default 3
            Padding between title and plotting area.

        y : float, default 1.0
            Vertical title position.

        Returns
        -------
        Self
            Returns the chart instance for method chaining.

        Examples
        --------
        Add a subplot title:

        >>> (
        ...     graph
        ...     .add_plot_title(
        ...         "Performance"
        ...     )
        ... )

        Align title to the left:

        >>> (
        ...     graph
        ...     .add_plot_title(
        ...         "Portfolio A",
        ...         loc="left"
        ...     )
        ... )
        """

        self._ax.set_title(
            text,
            loc=loc,
            fontsize=fontsize,
            fontweight=fontweight,
            fontstyle=fontstyle,
            color=color,
            pad=pad,
            y=y
        )

        return self
