# Helpers PS

Internal library developed for financial analisis, institutional graph generation and report construction. For full documentation visit https://jc-ocampob.github.io/helpers_ps/

------
## Install

```bash
pip install helpers_ps@git+https://github.com/jc-ocampob/helpers_ps.git@v0.3.0
```

------
## Import

```python
import helpers_ps as hp
```

------
## Main Components

### Matplotlib Standarized Graphs

Framework based on `matplotlib` for generating institutional graphs.

Main class:

```python
hp.GraphMtplt
```

### Finacial Metrics calculations

Functions used for general financial metricas to be calculated over a dataframe wich include `ytd`, `mtd`, `beta`, etc.

Main reference:
```python
hp.FinCalculations
```

### Power Point presentations

Framework based on `python-pptx` for generating graphs in powerpoint.

Main reference:
```python
hp.Powerpoint
```

### Bloomberg data

Framework based on `xbbg` for pulling data from bloomberg.

Main reference:
```python
hp.BBGHelper
```