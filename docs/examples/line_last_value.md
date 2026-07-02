# Último valor en gráfico de línea

Este ejemplo muestra cómo destacar el último valor de una serie con punto y etiqueta.

```python
from helpers_ps.Grafico.graf import Graph_mtplt

g = Graph_mtplt(df)

g.graph_line(
    tickers=["SPX"],
    labels=["S&P 500"],
    colors=["#1F77B4"],
    titles=dict(
        title="S&P 500",
        subtitle="Índice en puntos"
    ),
    tag_dot={
        "last": {
            "ticker": "SPX",
            "x_values": "last",
            "show": "dot_tag",
            "template": "{label}\n{y_value:,.1f}",
            "dot": {
                "size": 35,
                "zorder": 8
            },
            "tag": {
                "ubic_etq": (20, 0),
                "fontsize": 7,
                "bg_color": "white",
                "edge_color": "#D9D9D9",
                "show_bbox": True,
                "zorder": 9
            }
        }
    },
    source=dict(
        text="Fuente: Bloomberg."
    )
)

g.show()
```
