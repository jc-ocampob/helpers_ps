from __future__ import annotations
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from typing import Self
import numpy as np

class LayoutMixin:
    """
    Provide figure creation, layout, titles and source notes
    """

    def add_titles(
        self,
        title: str | None = None,
        title_font_size: int = 12,
        subtitle: str | None = None,
        subtitle_font_size: int = 9
    ) -> Self:
        """
        Add a main title and subtitle to the active figure.

        This method places figure-level text elements instead of using the default
        axis title, allowing for a consistent institutional layout across different
        chart types.

        Parameters
        ----------
        title : str or None, optional
            Main chart title.
        title_font_size : int, default 12
            Font size of the main title.
        subtitle : str or None, optional
            Subtitle displayed below the main title.
        subtitle_font_size : int, default 9
            Font size of the subtitle.

        Returns
        -------
        None
            Title and subtitle are added directly to the active figure.
        """
        
        # eliminar title del axis
        self._ax.set_title("")

        # título principal (arriba del todo)
        if title:
            self._fig.text(
                0.02, 0.93,
                title,
                ha="left",
                va="top",
                fontsize=title_font_size,
                fontweight="bold"
            )

        # subtítulo
        if subtitle:
            self._fig.text(
                0.02, 0.88,
                subtitle,
                ha="left",
                va="top",
                fontsize=subtitle_font_size,
                color="#333333"
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
        Add a source note or footer text to the active figure.

        The source can be provided as a single string or as a list of lines. The
        method supports up to four lines and places them in the lower section of the
        figure.

        Parameters
        ----------
        text : str, list, or None, optional
            Source text to display. If None, no source note is added.
        x : float, default 0.02
            Horizontal figure coordinate for the source text.
        y : float, default 0.022
            Vertical figure coordinate for the first source line.
        fontsize : float, default 6
            Font size of the source note.
        color : str, default "#606060"
            Text color of the source note.
        line_spacing : float, default 0.022
            Vertical spacing between source lines.

        Returns
        -------
        None
            Source text is added directly to the active figure.

        Raises
        ------
        ValueError
            If more than four source lines are provided.
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
        Create the base Matplotlib figure and axes layout.

        This method initializes the figure and axes used by all chart methods. It
        supports standard subplot creation as well as custom GridSpec layouts when
        height ratios, width ratios, spacing, or DPI are provided.

        Parameters
        ----------
        figsize : tuple[float, float], default (6.00, 4.80)
            Figure size in inches.
        color : str, default "#D5D5D5"
            Color of the decorative horizontal divider lines.
        researchtype : bool default True
            Adds decorative figure dividers.
        lw : float, default 0.8
            Line width of the decorative figure dividers.
        nrows : int, default 1
            Number of subplot rows.
        ncols : int, default 1
            Number of subplot columns.
        sharex : bool, default False
            Whether subplots should share the x-axis.
        sharey : bool, default False
            Whether subplots should share the y-axis.
        dpi : int or None, optional
            Figure DPI. If provided, a custom GridSpec layout is used.
        height_ratios : list[float] or None, optional
            Relative height ratios for GridSpec rows.
        width_ratios : list[float] or None, optional
            Relative width ratios for GridSpec columns.
        hspace : float or None, optional
            Vertical spacing between GridSpec rows.
        wspace : float or None, optional
            Horizontal spacing between GridSpec columns.

        Returns
        -------
        None
            The figure and axes are created and stored internally.

        Notes
        -----
        The method also adds institutional-style decorative horizontal lines to the
        figure and applies default subplot spacing when no custom GridSpec settings
        are used.
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
                    [0.01, 0.98], [0.95, 0.95],
                    transform=self._fig.transFigure,
                    color=color, lw=lw
                )
            )

            self._fig.add_artist(
                Line2D(
                    [0.01, 0.98], [0.12, 0.12],
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
