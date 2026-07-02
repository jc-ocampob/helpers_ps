# Quick Reference

Esta página resume los patrones de uso más frecuentes.

---

## Crear instancia

```python
g = Graph_mtplt(df)
```

---

## Línea

```python
g.graph_line(
    tickers="all"
)
```

### Línea con último valor

```python
tag_dot={
    "last": {
        "ticker": "SPX",
        "x_values": "last",
        "show": "dot_tag",
        "template": "{label}\n{y_value:,.1f}"
    }
}
```

---

## Barras

```python
g.graph_bar(
    tickers="all"
)
```

### Barras agrupadas

```python
graph_bar(
    grouped=True
)
```

### Barras stacked

```python
graph_bar(
    stacked=True
)
```

### Etiquetas de valor

```python
show="value_label"
```

### Tags dentro de barra

```python
show="bar_tag"
```

### Total de stack

```python
show="stack_total"
```

---

## Pie / Donut

```python
g.graph_pie(
    tickers="all",
    x_value="last"
)
```

### Donut

```python
g.graph_pie(
    donut_width=0.40
)
```

---

## Box & Whiskers

```python
g.graph_box_whiskers(
    tickers="all"
)
```

---

## Títulos

```python
titles=dict(
    title="Título del gráfico",
    subtitle="Subtítulo descriptivo"
)
```

---

## Fuente

```python
source=dict(
    text="Fuente: Bloomberg."
)
```

---

## Leyenda

```python
legend=dict(
    show=True,
    loc="upper left",
    ncol=3
)
```

---

## Mostrar gráfico

```python
g.show()
```

---

## Guardar gráfico

```python
g.save(
    name="grafico_1"
)
```
