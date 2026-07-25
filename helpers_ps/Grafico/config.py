from __future__ import annotations

import warnings
import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import locale

try:
    from helpers_ps.Config.var_globs import PALETA_COLORES
except Exception:
    PALETA_COLORES = [
        "#2F71E5", "#00A6A6", "#F28E2B", "#E15759", "#76B7B2",
        "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F"
    ]

buffers: dict[str, object] = {}

def set_graph_theme(
    font_family: str = "Inter",
    font_size: int = 9,
    title_size: int = 12,
    title_weight: str = "bold",
    use_locale: bool = True,
    locale_name: str | None = "es_ES.UTF-8",
    rebuild_font_cache: bool = False,
    ignore_matplotlib_warnings: bool = False,
) -> None:
    """
    Configure the default Matplotlib theme used by institutional charts.

    Parameters
    ----------
    font_family:
        Font family applied globally to Matplotlib figures.

    font_size:
        Default font size for chart text.

    title_size:
        Default title size for axes titles.

    title_weight:
        Default title weight for axes titles.

    use_locale:
        Whether Matplotlib should use locale-aware number formatting.

    locale_name:
        Locale used for number/date formatting. For Spanish, common values are:
        - "es_ES.UTF-8" on Linux/macOS
        - "Spanish_Spain.1252" on Windows
        - "es_PE.UTF-8" if available in the operating system

        If None, the system default locale is used.

    rebuild_font_cache:
        Whether to rebuild Matplotlib's font cache. Use this only when a new font
        was installed and Matplotlib cannot find it.

    ignore_matplotlib_warnings:
        Whether to suppress Matplotlib UserWarnings. This is disabled by default
        to avoid hiding useful debugging information.
    """
    if ignore_matplotlib_warnings:
        warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

    if rebuild_font_cache:
        fm._load_fontmanager(try_read_cache=False)

    if use_locale:
        locale_candidates = []

        if locale_name is not None:
            locale_candidates.append(locale_name)

        # Spanish fallback options across operating systems
        locale_candidates.extend(
            [
                "es_ES.UTF-8",          # Linux/macOS
                "es_ES.utf8",           # Linux alternative
                "es_PE.UTF-8",          # Peru if installed
                "es_PE.utf8",           # Peru alternative
                "Spanish_Spain.1252",   # Windows
                "Spanish_Peru.1252",    # Windows, if available
                "Spanish",              # Generic Windows fallback
                "",                     # System default
            ]
        )

        locale_set = False

        for loc in locale_candidates:
            try:
                locale.setlocale(locale.LC_ALL, loc)
                locale_set = True
                break
            except locale.Error:
                continue

        if not locale_set:
            warnings.warn(
                "Could not set Spanish locale. Matplotlib will continue using the current system locale.",
                UserWarning,
            )

    mpl.rcParams["axes.formatter.use_locale"] = use_locale
    plt.rcParams["font.family"] = font_family
    plt.rcParams["font.size"] = font_size
    plt.rcParams["axes.titlesize"] = title_size
    plt.rcParams["axes.titleweight"] = title_weight