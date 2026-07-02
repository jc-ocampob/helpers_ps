# graph_bar

`graph_bar` genera gráficos de barras simples, agrupadas o stacked.

Soporta:

- barras simples;
- barras agrupadas;
- barras stacked;
- series temporales;
- datos categóricos;
- etiquetas de valor;
- tags internos;
- totales de stacks.

---

## Dataframe esperado

```text
Fecha         Equity   Bonds   Cash
2024-01-31    0.40     0.50    0.10
2024-02-29    0.42     0.48    0.10
2024-03-31    0.45     0.45    0.10
```

---

## Barra simple

```python
g = Graph_mtplt(df)

g.graph_bar(
    tickers=["RETORNO"],
    bar_mode="time"
)

g.show()
```

---

## Barras agrupadas

```python
g.graph_bar(
    tickers=[
        "SPX",
        "NASDAQ"
    ],
    labels=[
        "S&P 500",
        "Nasdaq"
    ],
    grouped=True,
    bar_mode="last",
    legend=dict(
        show=True
    )
)
```

---

## Barras stacked

```python
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
        show=True
    )
)
```

---

## Modos disponibles

### Auto

```python
bar_mode="auto"
```

El modo se define automáticamente.

### Time

```python
bar_mode="time"
```

El índice se interpreta como eje temporal.

### Last

```python
bar_mode="last"
```

El índice se interpreta como categorías.

---

## Etiquetas de valor

Usar:

```python
show="value_label"
```

Ejemplo:

```python
g.graph_bar(
    tickers=["RETORNO"],
    bar_mode="time",
    bar_labels={
        "label_1": {
            "ticker": "RETORNO",
            "x_values": "last",
            "show": "value_label",
            "template": "{y_value:.1%}",
            "tag": {
                "fontsize": 7,
                "font_color": "black",
                "bg_color": "white",
                "edge_color": "#D9D9D9",
                "show_bbox": True,
                "ubic_etq": (0, 5),
                "zorder": 8
            }
        }
    }
)
```

---

## Tag central

Usar:

```python
show="bar_tag"
```

Ejemplo:

```python
g.graph_bar(
    tickers=["Peso"],
    bar_mode="last",
    bar_labels={
        "tag_1": {
            "ticker": "Peso",
            "x_values": "last",
            "show": "bar_tag",
            "template": "{label}\n{y_value:.1%}",
            "tag": {
                "fontsize": 7,
                "font_color": "white",
                "bg_color": "#404040",
                "edge_color": "none",
                "show_bbox": True,
                "ubic_etq": (0, 0),
                "zorder": 8
            }
        }
    }
)
```

---

## Total de stack

Usar:

```python
show="stack_total"
```

Ejemplo:

```python
g.graph_bar(
    tickers=[
        "Equity",
        "Bonds",
        "Cash"
    ],
    stacked=True,
    bar_mode="last",
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
    legend=dict(
        show=True
    )
)
```

---

## Casos de uso típicos

- Asset allocation.
- Contribución a retorno.
- Distribución por sector.
- Distribución por país.
- Resultados mensuales.
- Atribución por clase de activo.
