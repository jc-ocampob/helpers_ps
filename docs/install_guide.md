# Installation

## Install the package

```bash
pip install helpers_ps@git+https://github.com/jc-ocampob/helpers_ps.git@v0.3.3
```

Replace `v0.3.3` with the **tag** (or branch) you want. Without a tag the default branch is installed:

```bash
pip install helpers_ps@git+https://github.com/jc-ocampob/helpers_ps.git
```

To upgrade an existing installation:

```bash
pip install --upgrade --force-reinstall --no-deps helpers_ps@git+https://github.com/jc-ocampob/helpers_ps.git@v0.3.3
```

Check the version:

```python
import helpers_ps as hp

hp.__version__
```

!!! info "Requirements"
    Python **3.10 or newer** (3.11 is used to build this documentation). The main dependencies (`pandas`, `numpy`, `matplotlib`, `adjustText`, `scipy`, `seaborn`, `plotly`, `python-pptx`, `xlsxwriter`, `xlwings`, `xbbg`, and `pywin32` on Windows) are installed automatically.

---

## Extra requirements by component

| Component | Extra requirement |
|---|---|
| **DfStyling** (`TableSheet`) | A headless browser through Playwright: `pip install playwright`, then either have **Chrome / Edge** installed (used automatically) or run `python -m playwright install chromium`. |
| **Excel** (`to_excel_open`) | Microsoft Excel installed (Windows / macOS) and `xlwings`. |
| **Bbg** | A Bloomberg Terminal session on the machine (not documented yet). |
| **Fonts** | The default font is **Inter**. Install it in the operating system (and restart Python). If it is missing, Matplotlib falls back to another font and prints warnings; `hp.set_graph_theme(rebuild_font_cache=True)` refreshes the font cache after installing it. |

---

## Import

```python
import helpers_ps as hp
```

The components are then available as attributes:

```python
hp.GraphMtplt        # charts
hp.set_graph_theme   # global chart theme
hp.Calcs             # financial calculations
hp.DfStyling         # table images
hp.Ppt               # PowerPoint
hp.Excel             # Excel
hp.PALETA_COLORES    # institutional color palette
```

!!! warning "Importing the package imports `xlwings`"
    `import helpers_ps` loads all components, including `Excel`, which imports `xlwings`. If you see `ModuleNotFoundError: No module named 'xlwings'`, install it with `pip install xlwings`.

---

## Set the chart theme (once per session)

```python
hp.set_graph_theme()
```

It sets the font, the base sizes and the locale used for number formatting in every chart. See [GraphMtplt: Theme](GraphMtplt/getting_started.md#theme) for the options.

---

## Working with the documentation locally

The documentation is built with MkDocs (Material theme). From the root of the repository:

```bash
pip install -r requirements-docs.txt
mkdocs serve          # http://127.0.0.1:8000, reloads on every change
mkdocs build --clean  # generates the static site in ./site
```

The site is published automatically by the *Deploy Docs* GitHub Action when the `main` branch is updated.

---

## Next step

The next step is to view the `GraphMtplt` class: [GraphMtplt](GraphMtplt/getting_started.md)
