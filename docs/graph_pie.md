# graph_pie

`graph_pie` genera gráficos Pie y Donut a partir de una fotografía puntual del dataframe.

---

## Dataframe esperado

```text
Fecha         Equity   Bonds   Cash
2024-12-31    0.40     0.50    0.10
```

---

## Ejemplo básico

```python
g = Graph_mtplt(df)

g.graph_pie(
    tickers="all",
    x_value="last"
)

g.show()
```

---

## Seleccionar una fecha

```python
g.graph_pie(
    tickers="all",
    x_value="2025-12-31"
)
```

---

## Donut chart

```python
g.graph_pie(
    tickers="all",
    x_value="last",
    donut_width=0.40
)
```

---

## Ordenar valores

```python
g.graph_pie(
    tickers="all",
    sort_values=True
)
```

---

## Mostrar porcentajes

```python
g.graph_pie(
    tickers="all",
    autopct="%1.1f%%"
)
```

---

## Leyenda

```python
g.graph_pie(
    tickers="all",
    legend=dict(
        show=True,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5)
    )
)
```

---

## Casos de uso típicos

- Asset allocation.
- Distribución sectorial.
- Distribución geográfica.
- Distribución por emisor.
- Distribución por rating.
- Exposición por moneda.
