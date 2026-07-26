# Line Chart

`GraphMtplt.graph_line()` generates line charts for time series or any indexed dataframe.

::: helpers_ps.MtpltGraph.charts.GraphMtplt.graph_line
    options:
      heading_level: 3
      show_root_heading: true
      show_root_full_path: false
      separate_signature: true
      show_signature_annotations: true


---

## Expected DataFrame

```text
Date          SPX      NASDAQ
2024-01-31    100      150
2024-02-29    105      152
2024-03-31    108      160
```

- The index represents the X-axis.
- The columns represent the data series.

---

## Basic Example

```python
g = GraphMtplt(df)

g.graph_line(
    tickers=["SPX"]
)

g.show()
```

---

## Multiple Series

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

## Customize Colors

```python
g.graph_line(
    tickers=["SPX"],
    labels=["S&P 500"],
    colors=["#004A9F"]
)
```

---

## Title, Subtitle, and Source

```python
g.graph_line(
    tickers=["SPX"],
    titles=dict(
        title="Equity Market",
        subtitle="S&P 500 Evolution"
    ),
    source=dict(
        text="Source: Bloomberg."
    )
)
```

---

## Bloomberg Format on X-Axis

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

## Show Last Value

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

## Add Horizontal Lines

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

## Add Horizontal Guides

```python
g.graph_line(
    tickers=["SPX"],
    show_hguide=True
)
```

---

## Add Recession Periods

After creating the chart:

```python
g.add_recesiones(
    country="United States"
)
```

---

## Typical Use Cases

- Equity indices.
- Exchange rates.
- Inflation.
- Rates and yields.
- Macroeconomic indicators.
- Cumulative portfolio performance.
