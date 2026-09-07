from __future__ import annotations
from importlib.resources import files
import pandas as pd
from typing import Self


class RecessionMixin:
    """
    Recession overlay utilities.

    This mixin provides helpers for retrieving recession periods and
    overlaying them on time-series charts. Recession periods are loaded
    from an internal dataset and displayed as shaded regions using
    `shade_x()`.

    Notes
    -----
    Recession overlays are only supported on charts whose x-axis is based
    on dates, including standard datetime and Bloomberg-style date axes.
    """

    def add_recessions(
        self,
        country: str = "United States",
        data_frame: bool = False,
        controles: dict | None = None,
    ) -> Self:
        """
        Add recession periods to the active chart or return the recession dataset.

        This method loads historical recession periods from the internal
        recession database. Recessions can either be returned as a DataFrame
        or displayed as shaded vertical regions on the active chart.

        Parameters
        ----------
        country : str, default "United States"
            Country whose recession periods should be retrieved.

        data_frame : bool, default False
            If True, return the recession dataset instead of shading the
            chart.

        controles : dict or None, optional
            Styling parameters passed directly to `shade_x()`. Typical
            options include:

            - color
            - alpha
            - hatch
            - label
            - zorder

        Returns
        -------
        pandas.DataFrame or None
            Returns a DataFrame when `data_frame=True`. Otherwise recession
            overlays are added directly to the chart.

        Raises
        ------
        RuntimeError
            If no chart has been initialized.

        TypeError
            If the active chart does not use a date-based x-axis.

        NotImplementedError
            If recession data is not available for the requested country.

        Examples
        --------
        Display U.S. recessions:

        >>> (
        ...     graph
        ...     .graph_line(series)
        ...     .add_recessions()
        ... )

        Customize recession styling:

        >>> (
        ...     graph
        ...     .graph_line(series)
        ...     .add_recessions(
        ...         controles={
        ...             "color": "grey",
        ...             "alpha": 0.2,
        ...             "hatch": "//",
        ...         }
        ...     )
        ... )

        Retrieve the recession database:

        >>> recession_df = graph.add_recessions(
        ...     data_frame=True
        ... )

        Retrieve recession periods for another country:

        >>> (
        ...     graph
        ...     .graph_line(series)
        ...     .add_recessions(
        ...         country="United Kingdom"
        ...     )
        ... )
        """

        csv_path = files("helpers_ps").joinpath("Data/recessions.csv")

        recesiones = pd.read_csv(
            csv_path,
            parse_dates=["start_date", "end_date"],
        )

        recesiones = recesiones.set_index("recesion_id")

        if data_frame:
            return recesiones

        if self._ax is None:
            raise RuntimeError("No existe grafico para agregar las recesiones")

        if self._x_axis_mode not in ["bbg", "datetime"]:
            raise TypeError(
                "No se pueden aplicar recesiones a un grafico que no tiene como eje fechas"
            )

        if country not in recesiones["country"].unique():
            raise NotImplementedError("No hay registro de recesiones para ese pais")

        recesiones = recesiones[recesiones["country"] == country].copy()

        date_list = [
            (
                recesiones.loc[x, "start_date"].strftime("%Y-%m-%d"),
                recesiones.loc[x, "end_date"].strftime("%Y-%m-%d"),
            )
            for x in recesiones.index.tolist()
        ]

        controles = controles if controles is not None else dict(
            color="grey",
            alpha=0.3,
        )

        self.shade_x(periods=date_list, **controles)

        return None