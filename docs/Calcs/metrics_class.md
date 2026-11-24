# The `Metrics` class

`Metrics` is an **object-oriented wrapper** over a price DataFrame. You create it once and call methods that mirror many of the functions of the module, without passing the DataFrame every time. It adds one feature the functions do not have: **naming** columns through a description table.

!!! tip "Which one should I use?"
    For new code prefer the **functions** (`hp.Calcs.volatility(df)`): they cover more metrics (`wtd`, rolling versions, `sharpe_ratio`, `macd`...), validate the input and have complete docstrings. Use `Metrics` if you already have code built on it or if you need `assign_names`.

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

---

## Creating the object

`hp.Calcs.Metrics(data_frame, descripcion=None, fallback=True)`

| Argument | Description |
|---|---|
| `data_frame` | Prices: `DatetimeIndex` and one column per asset. Not empty (`ValueError`), with a date index (`TypeError`). |
| `descripcion` | *Optional.* DataFrame **indexed by ticker** with a column `Nombre` (display name). |
| `fallback` | Same meaning as in the functions: for `ytd` / `mtd` / `qtd`, if there is no previous period-end, use the first price of the period. |

```python
m = hp.Calcs.Metrics(data_frame=prices)
m.ytd().tail(1).round(4)
```
**Output**

```text
               SPX     NDX     AGG
2024-12-27  0.1735 -0.0266  0.0181
```

---

## Methods

| Method | Equivalent function | Notes |
|---|---|---|
| `ytd()`, `mtd()`, `qtd()` | `ytd`, `mtd`, `qtd` | |
| `drawdown(method="simple", min_price=1e-6)` | `drawdown` | |
| `std_downside(method, target_return, annualize, periods_per_year)` | `downside_std` | |
| `beta(benchmark, window=None, method="simple")` | `beta` | |
| `upside_capture(benchmark)`, `downside_capture(benchmark)`, `capture_ratio(benchmark)` | same names | |
| `tracking_error(benchmark, ...)`, `information_ratio(benchmark, ...)` | same names | |
| `var(confidence, method, returns_method, horizon)` | `value_at_risk` | |
| `excess_return(benchmark, period="qtd")`, `consistency(benchmark, period="qtd")` | same names | |
| `rsi(window, prefix)`, `sma(windows, ...)`, `ema(windows, ...)` | same names | |
| `ranges(desviaciones, prefix)` | `mean_std_bands` | Default column prefix `Media({w}sigma)_`. |
| `relative(...)`, `momentum(...)`, `momentum_sma(...)`, `rank_percentile()` | | |
| `assign_names(data_frame=None)` | not available as a function | Renames columns using `descripcion`. |

```python
pd.DataFrame({
    "Beta": m.beta("SPX"),
    "Tracking error": m.tracking_error("SPX"),
    "VaR 95%": m.var(),
}).round(4)
```
**Output**

```text
       Beta  Tracking error  VaR 95%
SPX  1.0000          0.0000   0.0147
NDX  0.1075          0.2435   0.0220
AGG -0.0025          0.1626   0.0064
```

---

## Using descriptions to rename columns

When `descripcion` is given, the class builds a `relation` table that maps each column to a readable name. Columns of the form `"PREFIX-TICKER"` are matched using the part **after the dash**. `assign_names()` then renames the columns of any result that contains the tickers in their names.

```python
description = pd.DataFrame(
    {"Nombre": ["S&P 500", "Nasdaq 100", "Global Aggregate"]},
    index=["SPX", "NDX", "AGG"],
)

m = hp.Calcs.Metrics(data_frame=prices, descripcion=description)
m.assign_names(m.rsi().tail(1))
```
**Output**

```text
            RSI14_S&P 500  RSI14_Nasdaq 100  RSI14_Global Aggregate
2024-12-27      40.475202         35.055255               44.683135
```

!!! warning "In-place renaming"
    `assign_names()` modifies the `columns` of the DataFrame you pass and returns it. When called without arguments it renames `m.data_frame` itself, so make a copy first if you still need the original tickers.

---

[API reference of the calculations](../api/Calcs/functions.md)
