# Calcs: Getting Started

`Calcs` is a collection of **financial calculations over a DataFrame of prices**: period-to-date returns, performance and risk statistics, drawdowns, benchmark-relative metrics (beta, tracking error, information ratio, capture), Value at Risk, technical indicators and a few helpers to build ranges and relative series.

```python
import helpers_ps as hp

hp.Calcs.total_return(prices)
hp.Calcs.max_drawdown(prices)
hp.Calcs.beta(prices, benchmark="SPX")
```

Every function is a plain function: **DataFrame in, Series / DataFrame out**. Results are designed to be plotted straight away with [`GraphMtplt`](../GraphMtplt/getting_started.md) or shown in a [`TableSheet`](../DfStyling/getting_started.md).

---

## The input: a DataFrame of prices

All functions expect the same layout:

| Requirement | Detail |
|---|---|
| **Index** | `pandas.DatetimeIndex`, with no duplicated dates. Unsorted indexes are sorted internally. |
| **Columns** | One column per asset / series, **numeric**. The column names become the labels of the results. |
| **Values** | **Prices or index levels** (not returns). Returns are computed internally. |
| **Benchmark** | For benchmark-relative functions, the benchmark is **one more column** of the same DataFrame, referenced by `benchmark="NAME"`. |

```python
import numpy as np
import pandas as pd
import helpers_ps as hp

rng = np.random.default_rng(42)
dates = pd.bdate_range("2023-01-02", periods=520)
rets = rng.normal([0.0004, 0.0006, 0.0002], [0.009, 0.013, 0.004], size=(len(dates), 3))
prices = pd.DataFrame(
    100 * np.exp(rets.cumsum(axis=0)),
    index=dates,
    columns=["SPX", "NDX", "AGG"],
)
```

```python
prices.tail(3).round(2)
```
**Output**

```text
               SPX     NDX     AGG
2024-12-25  120.57  102.20  104.37
2024-12-26  119.14  101.43  104.09
2024-12-27  120.02  102.57  104.05
```

If the validation fails you get an explicit error:

| Error | Cause |
|---|---|
| `TypeError: The DataFrame index must be a pandas DatetimeIndex.` | The index is not dates. Use `df.set_index("date")` after `pd.to_datetime`. |
| `TypeError: The DataFrame contains non-numeric columns: [...]` | Drop or convert text columns first. |
| `ValueError: The DataFrame index contains duplicated values.` | Remove duplicated dates. |
| `ValueError: The DataFrame cannot be empty.` | Empty DataFrame. |
| `ValueError: Benchmark 'X' was not found in the DataFrame.` | `benchmark` is not a column. |

---

## Common conventions

| Argument | Where | Meaning |
|---|---|---|
| `method` | most functions | `"simple"` (default, percentage returns) or `"log"` (logarithmic returns). |
| `periods_per_year` | annualized metrics | Number of observations per year: `252` daily (default), `52` weekly, `12` monthly. **Change it if your data is not daily.** |
| `annualize` | volatility, Sharpe, tracking error, IR... | `True` by default. `False` gives the per-period value. |
| `ddof` | volatility, tracking error... | Degrees of freedom of the standard deviation (`1` = sample). |
| `window` | rolling versions | Number of observations of the rolling window (`252` ~ 1 year of daily data). |
| `min_periods` | rolling versions | Minimum observations to produce a value (default: the window). |
| `prefix` | technical indicators | Template for the output column names (`"RSI{w}_"` -> `RSI14_SPX`). |

**Output type.** Functions that summarize the whole history return a `pandas.Series` indexed by asset (named after the metric, e.g. `"Volatility"`). Functions that produce a time series return a `DataFrame` with the same dates.

---

## Function index

| Group | Functions | Page |
|---|---|---|
| **Period-to-date** | `wtd`, `mtd`, `qtd`, `ytd` | [Returns and performance](returns_performance.md#period-to-date-returns) |
| **Performance** | `total_return`, `annualized_return`, `volatility`, `sharpe_ratio`, `downside_std`, `sortino_ratio` | [Returns and performance](returns_performance.md#performance-statistics) |
| **Drawdown** | `drawdown`, `max_drawdown`, `calmar_ratio` | [Returns and performance](returns_performance.md#drawdowns) |
| **Benchmark-relative** | `active_return`, `beta`, `tracking_error`, `rolling_tracking_error`, `information_ratio`, `rolling_information_ratio`, `upside_capture`, `downside_capture`, `capture_ratio`, `hit_ratio`, `excess_return`, `consistency` | [Benchmark-relative](benchmark_relative.md) |
| **Risk** | `value_at_risk`, `expected_shortfall` | [Risk](risk.md) |
| **Technical indicators** | `rsi`, `sma`, `ema`, `zscore`, `bollinger_bands`, `macd`, `momentum`, `momentum_sma` | [Technical indicators](technical.md) |
| **Ranges and transformations** | `mean_std_bands`, `relative`, `rank_percentile` | [Transformations](transformations.md) |
| **Object-oriented wrapper** | `Metrics` | [Metrics class](metrics_class.md) |

The full signatures are in the [API reference](../api/Calcs/functions.md).

---

## A first analysis

```python
summary = pd.DataFrame({
    "Total return": hp.Calcs.total_return(prices),
    "Ann. return": hp.Calcs.annualized_return(prices),
    "Volatility": hp.Calcs.volatility(prices),
    "Sharpe (rf 3%)": hp.Calcs.sharpe_ratio(prices, risk_free_rate=0.03),
    "Max drawdown": hp.Calcs.max_drawdown(prices),
})
summary.round(3)
```
**Output**

```text
     Total return  Ann. return  Volatility  Sharpe (rf 3%)  Max drawdown
SPX         0.196        0.091       0.150           0.455        -0.122
NDX         0.039        0.019       0.204           0.046        -0.178
AGG         0.037        0.018       0.062          -0.168        -0.087
```

Because every metric is a Series indexed by asset, they combine naturally into one table with `pd.DataFrame({...})`, which you can then format and export with [`DfStyling`](../DfStyling/getting_started.md).

---

## Next step

[Returns and performance ->](returns_performance.md)
