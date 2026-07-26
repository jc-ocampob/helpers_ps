# graph_box_whiskers

`graph_box_whiskers` generates Box & Whiskers charts to visualize historical distributions by series.

---

## Expected DataFrame

```text
Date          SPX_PE   NDX_PE   EUROSTOXX_PE
2024-01-31    18.2     24.1     13.5
2024-02-29    18.7     25.0     13.8
2024-03-31    19.1     25.4     14.0
```

---

## Basic Example

```python
g = hp.GraphMtplt(df)

g.graph_box_whiskers(
    tickers="all"
)

g.show()
```

---

## Show Mean

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

## Label Maximum Values

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

## Label Minimum Values

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

## Label Mean

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

## Show Last Value

```python
g.graph_box_whiskers(
    tickers="all",
    tag_dot={
        "last": {
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

## Typical Use Cases

- Historical P/E ratios.
- Historical EV/EBITDA ratios.
- Historical yields.
- Historical spreads.
- Historical margins.
- Relative valuation comparison.
