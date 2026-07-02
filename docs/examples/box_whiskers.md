# Box & Whiskers con último valor

Este ejemplo muestra cómo agregar el último valor observado sobre un gráfico Box & Whiskers.

```python
from helpers_ps.Grafico.graf import Graph_mtplt

g = Graph_mtplt(df)

g.graph_box_whiskers(
    tickers="all",
    mean_tag=dict(
        show=True,
        fmt=",.1f"
    ),
    tag_dot={
        "ultimo": {
            "ticker": "SPX_PE",
            "x_values": "last",
            "show": "dot_tag",
            "template": "{y_value:,.1f}",
            "dot": {
                "size": 35,
                "color": "red",
                "zorder": 8
            },
            "tag": {
                "ubic_etq": (15, 0),
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
