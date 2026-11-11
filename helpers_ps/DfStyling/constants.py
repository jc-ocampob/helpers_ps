DEFAULT_HIGHLIGHT_STYLE = {
    "font-weight": "bold",
    "border-top": "1px solid black",
    "border-bottom": "1px solid black",
    "border-left": "1px solid black",
    "border-right": "1px solid black",
}

DEFAULT_LINE_STYLE = {
    "width": "1px",
    "style": "solid",
    "color": "black",
}


# ---------------------------------------------------------------------
# TableSheet defaults
# ---------------------------------------------------------------------

#: Font used for titles, notes and sources (CSS-like comma lists accepted).
DEFAULT_FONT_FAMILY = "Inter"

#: Font used when none of the requested fonts is installed.
FALLBACK_FONT = "DejaVu Sans"

#: Resolution (dots per inch) of rendered tables and exported images.
DEFAULT_DPI = 200

#: Stable ``Styler`` uuid. Makes the generated HTML deterministic, which
#: is what allows rendered tables to be cached by content.
STYLER_UUID = "dfs"

#: Browser channels tried in order when launching Chromium. ``None`` is
#: the Chromium bundled with Playwright.
DEFAULT_BROWSER_CHANNELS = ("chrome", "msedge", "chromium", None)

#: Cache budget (MB) of the process-wide render cache.
DEFAULT_CACHE_MB = 256
