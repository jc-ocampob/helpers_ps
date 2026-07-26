# graph_bar

`graph_bar` generates simple, grouped, or stacked bar charts.

It supports:

- simple bars;
- grouped bars;
- stacked bars;
- time series;
- categorical data;
- value labels;
- internal tags;
- stack totals.

---

## Expected DataFrame

```text
Date          Equity   Bonds   Cash
2024-01-31    0.40     0.50    0.10
2024-02-29    0.42     0.48    0.10
2024-03-31    0.45     0.45    0.10
```

---

## Simple Bar

```python
g = Graph_mtplt(df)

g.graph_bar(
    tickers=["RETURN"],
    bar_mode="time"
)

g.show()
```

---

## Grouped Bars

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

## Stacked Bars

```python
g.graph_bar(
    tickers=[
        "Equity",
        "Bonds",
        "Cash"
    ],
    labels=[
        "Equity",
        "Fixed Income",
        "Cash"
    ],
    stacked=True,
    bar_mode="last",
    legend=dict(
        show=True
    )
)
```

---

## Available Modes

### Auto

```python
bar_mode="auto"
```

The mode is defined automatically.

### Time

```python
bar_mode="time"
```

The index is interpreted as a time axis.

### Last

```python
bar_mode="last"
```

The index is interpreted as categories.

---

## Value Labels

Use:

```python
show="value_label"
```

Example:

```python
g.graph_bar(
    tickers=["RETURN"],
    bar_mode="time",
    bar_labels={
        "label_1": {
            "ticker": "RETURN",
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

## Center Tag

Use:

```python
show="bar_tag"
```

Example:

```python
g.graph_bar(
    tickers=["Weight"],
    bar_mode="last",
    bar_labels={
        "tag_1": {
            "ticker": "Weight",
            "x_values": "last",
            "show": "bar_tag",
            "template": "{label}
{y_value:.1%}",
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

## Stack Total

Use:

```python
show="stack_total"
```

Example:

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

## Typical Use Cases

- Asset allocation.
- Return contribution.
- Sector distribution.
- Country distribution.
- Monthly results.
- Attribution by asset class.
