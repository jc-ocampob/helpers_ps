from __future__ import annotations

import asyncio
import io
import math
import sys
from collections.abc import Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..constants import DEFAULT_BROWSER_CHANNELS

TABLE_ELEMENT_ID = "dfs_table"


# ---------------------------------------------------------------------
# HTML document
# ---------------------------------------------------------------------

def build_base_css(font_px: int = 14, zebra: bool = True) -> str:
    """
    Return the base CSS of a rendered table.

    It reproduces the look of ``dataframe_image`` (bold headers, a rule
    under the header, optional zebra rows, collapsed borders). Anything set
    through ``Styler`` is applied afterwards and therefore overrides it.

    Parameters
    ----------
    font_px : int, default 14
        Base font size in CSS pixels.
    zebra : bool, default True
        Shade odd body rows.

    Returns
    -------
    str
        CSS rules (without ``<style>`` tags).
    """
    rules = f"""
    html, body {{ margin: 0; padding: 0; background: #ffffff; }}
    #{TABLE_ELEMENT_ID} {{ display: inline-block; }}
    table {{
        background-color: transparent;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        border: 1px solid #f5f5f5;
        border-collapse: collapse;
        border-spacing: 0;
        color: black;
        font-size: {font_px}px;
        table-layout: fixed;
    }}
    thead {{ border-bottom: 1px solid black; vertical-align: bottom; }}
    tr, th, td {{
        text-align: right;
        vertical-align: middle;
        padding: 0.5em 0.5em;
        line-height: normal;
        white-space: normal;
        max-width: none;
        border: none;
    }}
    th {{ font-weight: bold; }}
    """
    if zebra:
        rules += "tbody tr:nth-child(odd) { background: #f5f5f5; }\n"
    return rules


def build_document(
    table_html: str,
    font_px: int = 14,
    zebra: bool = True,
) -> str:
    """
    Wrap the HTML of a ``Styler`` in a complete document.

    Parameters
    ----------
    table_html : str
        Output of ``Styler.to_html()``.
    font_px : int, default 14
        Base font size in CSS pixels.
    zebra : bool, default True
        Shade odd body rows.

    Returns
    -------
    str
        Complete HTML document. The table is inside the element
        ``#dfs_table``, which is what gets screenshotted.
    """
    css = build_base_css(font_px=font_px, zebra=zebra)
    return (
        "<!DOCTYPE html><html><head>"
        '<meta charset="UTF-8"/>'
        f"<style>{css}</style>"
        "</head><body>"
        f'<div id="{TABLE_ELEMENT_ID}">{table_html}</div>'
        "</body></html>"
    )


# ---------------------------------------------------------------------
# Event-loop isolation
# ---------------------------------------------------------------------

@contextmanager
def _proactor_policy() -> Iterator[None]:
    """
    Use the Proactor event-loop policy while the browser is driven (Windows).

    Jupyter/ipykernel installs ``WindowsSelectorEventLoopPolicy``. Loops
    created under that policy cannot spawn subprocesses, so Playwright
    fails to launch the browser with an empty ``NotImplementedError``. The
    previous policy is restored on exit. No-op on other platforms.
    """
    if sys.platform != "win32":
        yield
        return

    previous = asyncio.get_event_loop_policy()
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        yield
    finally:
        asyncio.set_event_loop_policy(previous)


def _run_isolated(func: Any) -> Any:
    """
    Run ``func`` in a dedicated worker thread.

    Playwright's sync API cannot run inside the event loop of a Jupyter
    kernel. A fresh thread has no running loop.
    """
    with _proactor_policy(), ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(func).result()


# ---------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------

@dataclass
class PlaywrightRenderer:
    """
    Render HTML documents to images with a headless Chromium browser.

    All documents of a call share **one** browser instance, which makes a
    grid of tables almost as fast as a single table (launching the browser
    is the expensive part).

    Parameters
    ----------
    chrome_path : str | None, default None
        Path to a Chromium-based executable. If given, ``channels`` is
        ignored.
    channels : Sequence[str | None], default ``("chrome", "msedge", "chromium", None)``
        Browser channels tried in order. ``None`` is the Chromium bundled
        with Playwright. The first one that launches is remembered.
    timeout_ms : int, default 30000
        Timeout of page operations.
    launch_args : Sequence[str], default ()
        Extra command-line arguments for the browser.

    Attributes
    ----------
    launch_count : int
        Number of browsers launched by this instance.

    Notes
    -----
    Requires ``playwright``. If no browser is found, install one with
    ``python -m playwright install chromium`` or use Chrome/Edge.

    Examples
    --------
    >>> renderer = PlaywrightRenderer(chrome_path=r"C:\\Program Files\\...\\chrome.exe")
    >>> sheet = TableSheet(df, renderer=renderer)
    """

    chrome_path: str | None = None
    channels: Sequence[str | None] = DEFAULT_BROWSER_CHANNELS
    timeout_ms: int = 30_000
    launch_args: Sequence[str] = ()
    launch_count: int = field(default=0, init=False)
    cache_token: str = field(default="playwright", init=False)
    _working_channel: Any = field(default=None, init=False, repr=False)
    _has_working_channel: bool = field(default=False, init=False, repr=False)

    def __call__(
        self,
        documents: Sequence[str],
        dpi: int,
    ) -> list[np.ndarray]:
        """
        Render documents to RGB ``uint8`` arrays.

        Parameters
        ----------
        documents : Sequence[str]
            Complete HTML documents (see ``build_document``).
        dpi : int
            Output resolution. One CSS pixel becomes ``dpi / 96`` pixels.

        Returns
        -------
        list[numpy.ndarray]
            One image per document, in the same order.
        """
        if not documents:
            return []
        return _run_isolated(lambda: self._render(documents, dpi))

    # -- internals ----------------------------------------------------

    def _render(
        self,
        documents: Sequence[str],
        dpi: int,
    ) -> list[np.ndarray]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise ImportError(
                "Playwright is required to render tables. "
                "Install it with 'pip install playwright'."
            ) from error

        images: list[np.ndarray] = []

        with sync_playwright() as playwright:
            browser = self._launch(playwright)
            try:
                context = browser.new_context(
                    device_scale_factor=dpi / 96,
                    bypass_csp=True,
                )
                page = context.new_page()
                page.set_default_timeout(self.timeout_ms)

                for index, document in enumerate(documents):
                    try:
                        images.append(self._screenshot(page, document))
                    except Exception as error:
                        raise RuntimeError(
                            f"Could not render document {index}: "
                            f"{type(error).__name__}: {error}"
                        ) from error
            finally:
                browser.close()

        return images

    def _launch(self, playwright: Any) -> Any:
        """Launch the first available browser, remembering which one."""
        if self.chrome_path:
            attempts: list[tuple[str | None, str | None]] = [
                (None, self.chrome_path)
            ]
        else:
            channels = list(self.channels)
            if self._has_working_channel and self._working_channel in channels:
                channels.remove(self._working_channel)
                channels.insert(0, self._working_channel)
            attempts = [(channel, None) for channel in channels]

        errors: list[str] = []
        for channel, executable in attempts:
            options: dict[str, Any] = {
                "headless": True,
                "args": list(self.launch_args),
            }
            if executable:
                options["executable_path"] = executable
            elif channel:
                options["channel"] = channel

            try:
                browser = playwright.chromium.launch(**options)
            except Exception as error:
                first_line = (str(error).strip().splitlines() or [""])[0]
                label = executable or channel or "bundled chromium"
                errors.append(
                    f"  - {label}: {type(error).__name__}: {first_line}"
                )
                continue

            self.launch_count += 1
            self._working_channel = channel
            self._has_working_channel = True
            return browser

        raise RuntimeError(
            "No Chromium-based browser could be launched.\n"
            + "\n".join(errors)
            + "\nInstall one with 'python -m playwright install chromium', "
            "install Chrome/Edge, or pass PlaywrightRenderer(chrome_path=...)."
        )

    def _screenshot(self, page: Any, document: str) -> np.ndarray:
        from PIL import Image

        page.set_content(document, wait_until="load")
        page.evaluate(
            "async () => { await document.fonts.ready; return true; }"
        )

        table = page.locator(f"#{TABLE_ELEMENT_ID}")
        box = table.bounding_box()
        if not box or box["width"] <= 0 or box["height"] <= 0:
            raise RuntimeError("the table is empty (zero size).")

        page.set_viewport_size(
            {
                "width": math.ceil(box["width"]) + 20,
                "height": math.ceil(box["height"]) + 20,
            }
        )
        png = table.screenshot(type="png")

        with Image.open(io.BytesIO(png)) as image:
            return np.asarray(image.convert("RGB")).copy()
