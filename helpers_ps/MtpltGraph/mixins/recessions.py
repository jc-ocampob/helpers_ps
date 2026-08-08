from __future__ import annotations

from importlib.resources import files

import pandas as pd


class RecessionMixin:
    """Provide recession overlay utilities."""

    def add_recessions(
        self,
        country: str = "United States",
        data_frame: bool = False,
        controles: dict | None = None,
    ):
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