# Getting Started

## Importar la clase principal

```python
from helpers_ps.Grafico.graf import Graph_mtplt
```

> Ajustar el path de importación si la clase se mueve a otro módulo.

---

## Crear una instancia

```python
g = Graph_mtplt(
    dataframe=df
)
```

El parámetro `dataframe` puede ser:

```python
pd.DataFrame
```

o una lista de dataframes:

```python
[ df_1, df_2, df_3,]
```

---

## Estructura recomendada de dataframe

El índice representa el eje X y las columnas representan las series.

```text
Fecha         SPX      NASDAQ
2024-01-31    100      150
2024-02-29    105      152
2024-03-31    108      160
```

---

## Crear un gráfico de línea

```python
g.graph_line(
    tickers="all"
)

g.show()
```

---

## Crear un gráfico de barras

```python
g.graph_bar(
    tickers="all"
)

g.show()
```

---

## Guardar un gráfico

```python
g.save(
    name="mi_grafico"
)
```

Esto guarda el gráfico en memoria dentro del diccionario global de buffers.

---

## Flujo habitual

```python
g = Graph_mtplt(df)

g.graph_line(
    tickers="all",
    titles=dict(
        title="Mi gráfico",
        subtitle="Subtítulo descriptivo"
    ),
    source=dict(
        text="Fuente: Bloomberg."
    )
)

g.show()
```
