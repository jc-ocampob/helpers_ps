# Tag Handling

Tag handling within `graph_line` relies on the helper functions `etiqueta_valor` and `punto_valor`; therefore, it inherits the available configuration options from those functions.

## How `tag_dot` Works in `graph_line`

`tag_dot` requires a dictionary where the `key` represents a unique identifier and the `value` is itself a dictionary containing the information required to plot the tags.

## Example Dictionary for `tag_dot`

```python
tag_dot = {
    # A distinctive key is generated to group the tags
    "distinctive_group_key": {

        # ticker: str references the ticker on which the tags will be applied
        "ticker": "SPX",

        # X values where the tags should be placed. It can be the last value,
        # all values, or a list of specific positions
        "x_values": "all" | "last" | ["2025-12-31", "last", "2026-04-05"],

        # template manages the tag as a template with the available
        # x and y variables
        "template": "{x_value:,%b-%Y}: {y_value:,.0f}",

        # show is a string that controls what should be displayed:
        # the tag and point, or only one of them
        "show": "dot_tag" | "tag" | "dot",

        # If different from None, a legend reference is generated
        # for these points using the assigned series name
        "legend_label": "Key Moments",

        # Control dictionary for the subgroup points,
        # inheriting all functionality from
        # .punto_valor()
        "dot": {
            "color": "green",
            "size": 22,
        },

        # Control dictionary for the subgroup tags,
        # inheriting all functionality from
        # .etiqueta_valor()
        "tag": {
            "bg_color": "none",
            "font_color": "red"
        },
    }
}
```

---

## Basic Tag Example

In this first example, SPX and RTY data are used to generate two groups of tags, one for each series.

```python
graph = GraphMtplt(dataframe=_data)
graph.graph_line(
    figsize=(6, 5),                                                                                                  # Figure size configuration on which the chart is built
    tickers="all",                                                                                                  # Tickers (column names) to be displayed: "all" = all | "ticker" | ["ticker1", "ticker2", ..., "tickerN"]
    labels=["S&P 500", "Russell 2000"],                                                                            # Labels for each series (overwrites column names): None = default, use tickers | ["label_of_ticker1", "label_of_ticker2", ..., "label_of_tickerN"]
    colors=["black"],                                                                                               # Colors for each series (overwrites default colors): None = default, use CC palette | ["color_of_ticker1", "color_of_ticker2", ..., "color_of_tickerN"]
    titles=dict(                                                                                                     # Inherits all functionality from self.set_titles()
        title="SPX Price",
        subtitle="SPX Price Evolution Since 1990"
    ),                                                                                                              
    source=dict(                                                                                                     # Inherits all functionality from self.add_source()
        text=[f"Source: Bloomberg, with information as of market close", "Note 1: Maje was here"]
    ),
    x_axis=dict(                                                                                                     # Inherits functionality from _prep_x_axis
        tick_step=25,
        bbg_format=True,
        fmt="%b-%Y",
        lim=("2015-01-01", None),
        fontsize=6
    ),
    tag_dot={  # Adds tag | dot | dot_tag to a line series
        "1": dict(                                                                                                  # Random key used only to differentiate grouping (allows adding configurable tag groups for the same series)
            ticker="PX_LAST-SPX INDEX",                                                                             # ticker (column name) of the series to work with
            x_values=["last", pd.Timestamp("2025-12-31")],                                                         # X-axis points where tags should be placed: x_values = "last" | x_values = "all" | x_values = ["last", "2025-04-05", ...]
            template="{y_value:,.0f}",                                                                              # Template for the label to be placed in the tag
            show="dot_tag",                                                                                         # What should be displayed: show = "dot" (only point) | "tag" (only tag) | "dot_tag" (both tag and point)
            dot=dict(                                                                                                # Inherits all functionality from self.punto_valor()
                color="green",
                size=22,
            ),
            tag=dict(                                                                                                # Inherits all functionality from self.etiqueta_valor()
                bg_color="none"
            ),
            legend_label="Key Moments"
        ),
        "2": dict(
            ticker="PX_LAST-RUO INDEX",
            x_values=[pd.Timestamp("2020-12-31")],
            template="{y_value:,.0f}",
            show="dot_tag",
            dot=dict(
                size=22,
                zorder=50,
                color="red"
            ),
            tag=dict(
                bg_color="none",
                font_color="red"
            )
        ),
    },
    legend=dict(
        show=True,
        ncol=1
    ),
)

g.show()
```

![Example](../images/line_graph.png)

---

