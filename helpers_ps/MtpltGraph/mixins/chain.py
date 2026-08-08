from __future__ import annotations
from typing import Any, Callable, Self

class ChainMixin:
    """
    Provide chainable helpers for graph workflows
    """

    def pipe(
        self: Self,
        func: Callable[..., Self | None],
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        """
        Apply a custom function to the graph object and keep the chain alive.

        This method follows the same idea as pandas .pipe(), allowing reusable
        graph transformations to be inserted into the chart-building workflow.

        Parameters
        ----------
        func:
            Function that receives the current graph object as its first argument.
            The function can either return the graph object or return None.
        *args:
            Positional arguments passed to the function.
        **kwargs:
            Keyword arguments passed to the function.

        Returns
        -------
        Graph_base
            The current graph object, or the object returned by the function.
        """
        result = func(self, *args, **kwargs)
        return self if result is None else result


    def tap(
        self: Self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        """
        Execute a side-effect function and keep the chain alive.

        This is useful for debugging, logging, previewing, or applying matplotlib
        actions that do not need to return the graph object.

        Parameters
        ----------
        func:
            Function that receives the current graph object as its first argument.
        *args:
            Positional arguments passed to the function.
        **kwargs:
            Keyword arguments passed to the function.

        Returns
        -------
        Graph_base
            The current graph object.
        """
        func(self, *args, **kwargs)
        return self


    def axis(self: Self, ax_index: int = 0) -> Self:
        """
        Select the active subplot axis and keep the chain alive.

        This is a public chainable wrapper around _set_axis().

        Parameters
        ----------
        ax_index:
            Zero-based index of the subplot axis to activate.

        Returns
        -------
        Graph_base
            The current graph object.
        """
        self._set_axis(ax_index=ax_index)
        return self


    def get_axis(self, side: str = "left"):
        """
        Return the active left or right Matplotlib axis.

        Parameters
        ----------
        side:
            Axis side to retrieve. Must be either "left" or "right".

        Returns
        -------
        matplotlib.axes.Axes
            The requested Matplotlib axis.
        """
        if side not in {"left", "right"}:
            raise ValueError("side must be 'left' or 'right'.")

        if side == "left":
            return self._ax

        if self._right_ax is None:
            raise RuntimeError("No right axis exists for the active chart.")

        return self._right_ax
