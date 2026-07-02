# Barras stacked con totales

Este ejemplo muestra cómo construir un gráfico de barras stacked y agregar el total del stack.

```python
from helpers_ps.Grafico.graf import Graph_mtplt

g = Graph_mtplt(df)

g.graph_bar(
    tickers=[
        "Equity",
        "Bonds",
        "Cash"
    ],
    labels=[
        "Renta Variable",
        "Renta Fija",
        "Caja"
    ],
    stacked=True,
    bar_mode="last",
    legend=dict(
        show=True,
        loc="upper left",
        ncol=3
    ),
    bar_labels={
        "total": {
            "ticker": "Equity",
            "x_values": "all",
            "show": "stack_total",
            "template": "{total_value:.1%}",
            "tag": {
                "fontsize": 7,
                "font_color": "black",
                "bg_color": "white",
                "edge_color": "#D9D9D9",
                "show_bbox": True,
                "ubic_etq": (0, 5),
                "zorder": 9
            }
        }
    },
    source=dict(
        text="Fuente: elaboración propia."
    )
)

g.show()
```
