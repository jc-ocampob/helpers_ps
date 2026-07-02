# graph_box_whiskers

`graph_box_whiskers` genera gráficos Box & Whiskers para visualizar distribuciones históricas por serie.

---

## Dataframe esperado

```text
Fecha         SPX_PE   NDX_PE   EUROSTOXX_PE
2024-01-31    18.2     24.1     13.5
2024-02-29    18.7     25.0     13.8
2024-03-31    19.1     25.4     14.0
```

---

## Ejemplo básico

```python
g = Graph_mtplt(df)

g.graph_box_whiskers(
    tickers="all"
)

g.show()
```

---

## Mostrar media

```python
g.graph_box_whiskers(
    tickers="all",
    box_config=dict(
        showmeans=True,
        meanline=True
    )
)
```

---

## Etiquetar máximos

```python
g.graph_box_whiskers(
    tickers="all",
    range_tag_high=dict(
        show=True,
        fmt=",.2f"
    )
)
```

---

## Etiquetar mínimos

```python
g.graph_box_whiskers(
    tickers="all",
    range_tag_low=dict(
        show=True,
        fmt=",.2f"
    )
)
```

---

## Etiquetar media

```python
g.graph_box_whiskers(
    tickers="all",
    mean_tag=dict(
        show=True,
        fmt=",.2f"
    )
)
```

---

## Mostrar último valor

```python
g.graph_box_whiskers(
    tickers="all",
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
                "show_bbox": True
            }
        }
    }
)
```

---

## Casos de uso típicos

- P/E históricos.
- EV/EBITDA históricos.
- Yields históricos.
- Spreads históricos.
- Márgenes históricos.
- Comparación relativa de valuaciones.
