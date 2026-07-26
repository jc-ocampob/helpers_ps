# graph_pie

`graph_pie` generates Pie and Donut charts from a point-in-time snapshot of the dataframe.

---

## Expected DataFrame

```text
Date          Equity   Bonds   Cash
2024-12-31    0.40     0.50    0.10
```

---

## Basic Example

```python
g = hp.GraphMtplt(df)

g.graph_pie(
    tickers="all",
    x_value="last"
)

g.show()
```

---

## Select a Date

```python
g.graph_pie(
    tickers="all",
    x_value="2025-12-31"
)
```

---

## Donut Chart

```python
g.graph_pie(
    tickers="all",
    x_value="last",
    donut_width=0.40
)
```

---

## Sort Values

```python
g.graph_pie(
    tickers="all",
    sort_values=True
)
```

---

## Show Percentages

```python
g.graph_pie(
    tickers="all",
    autopct="%1.1f%%"
)
```

---

## Legend

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

## Typical Use Cases

- Asset allocation.
- Sector distribution.
- Geographic distribution.
- Issuer distribution.
- Rating distribution.
- Currency exposure.
