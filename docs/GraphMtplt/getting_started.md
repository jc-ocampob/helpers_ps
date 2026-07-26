# Getting Started with `GraphMtplt`

`GraphMtplt` is the main class that handles the creation of institutional type graphs with standarized formating and ample flexibility

-----
## Importing and creating an instance

Creating an instance of the class takes 1 positional argument `dataframe` that is later used in graph creation. Te positional argument can take in a single `pd.Dataframe` or a list of `pd.Dataframe`.

```python
import helpers_ps as hp

g = hp.GraphMtplt(dataframe = df | [df_1, df_2,...])
```

---
## Available graph types

| Method | Description |
|---|---|
| `graph_line()` | Time series and indicator evolution |
| `graph_bar()` | Bars (simple, stacked, grouped) |
| `graph_pie()` | Pie y Donut charts |
| `graph_box_whiskers()` | Historical distribution by series |

---
## Next Step

The next step is to understand the creation of the line chart in [graph_line](Line/graph.md)