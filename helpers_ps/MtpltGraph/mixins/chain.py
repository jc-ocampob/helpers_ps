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