# graph_line

`graph_line` genera gráficos de línea para series temporales o cualquier dataframe indexado.

---

## Dataframe esperado

```text
Fecha         SPX      NASDAQ
2024-01-31    100      150
2024-02-29    105      152
2024-03-31    108      160
```

- El índice representa el eje X.
- Las columnas representan las series.

---

## Ejemplo básico

```python
g = Graph_mtplt(df)

g.graph_line(
    tickers=["SPX"]
)

g.show()
```

---

## Múltiples series

```python
g.graph_line(
    tickers=[
        "SPX",
        "NASDAQ",
        "IBEX"
    ],
    labels=[
        "S&P 500",
        "Nasdaq",
        "IBEX"
    ],
    legend=dict(
        show=True
    )
)
```

---

## Personalizar colores

```python
g.graph_line(
    tickers=["SPX"],
    labels=["S&P 500"],
    colors=["#004A9F"]
)
```

---

## Título, subtítulo y fuente

```python
g.graph_line(
    tickers=["SPX"],
    titles=dict(
        title="Mercado Accionario",
        subtitle="Evolución del S&P 500"
    ),
    source=dict(
        text="Fuente: Bloomberg."
    )
)
```

---

## Formato Bloomberg en eje X

```python
g.graph_line(
    tickers=["SPX"],
    x_axis=dict(
        bbg_format=True,
        tick_step=3,
        fontsize=7
    )
)
```

---

## Mostrar último valor

```python
g.graph_line(
    tickers=["SPX"],
    labels=["S&P 500"],
    tag_dot={
        "last": {
            "ticker": "SPX",
            "x_values": "last",
            "show": "dot_tag",
            "template": "{label}\n{x_value:%b-%y}: {y_value:,.1f}",
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
    }
)
```

---

## Agregar líneas horizontales

```python
g.graph_line(
    tickers=["SPX"],
    hlines=dict(
        y_values=[0, 50, 100],
        linestyle="--",
        linewidth=0.7,
        color="gray"
    )
)
```

---

## Agregar guías horizontales

```python
g.graph_line(
    tickers=["SPX"],
    show_hguide=True
)
```

---

## Agregar recesiones

Después de crear el gráfico:

```python
g.add_recesiones(
    country="United States"
)
```

---

## Casos de uso típicos

- Índices bursátiles.
- Tipo de cambio.
- Inflación.
- Tasas y yields.
- Indicadores macroeconómicos.
- Performance acumulada de portafolios.
