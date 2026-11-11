from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import numpy as np


def figure_of(obj: Any) -> Any | None:
    """
    Return the matplotlib ``Figure`` behind ``obj``, if any.

    Parameters
    ----------
    obj : Any
        A ``Figure`` or an object exposing one as ``_fig`` (for example a
        ``GraphMtplt`` instance).

    Returns
    -------
    matplotlib.figure.Figure | None
        The figure, or ``None`` if ``obj`` is not figure-like.
    """
    from matplotlib.figure import Figure

    if isinstance(obj, Figure):
        return obj

    fig = getattr(obj, "_fig", None)
    return fig if isinstance(fig, Figure) else None


def array_to_rgb(array: np.ndarray) -> np.ndarray:
    """
    Convert an image array to RGB ``uint8`` composed over white.

    Parameters
    ----------
    array : numpy.ndarray
        ``(H, W)``, ``(H, W, 3)`` or ``(H, W, 4)``. Floating-point arrays
        are interpreted in the range ``[0, 1]``.

    Returns
    -------
    numpy.ndarray
        ``(H, W, 3)`` ``uint8`` array.
    """
    arr = np.asarray(array)

    if arr.ndim not in (2, 3):
        raise ValueError(
            f"Image array must be 2-D or 3-D, got shape {arr.shape}."
        )

    if arr.dtype != np.uint8:
        arr = (np.clip(arr.astype(float), 0.0, 1.0) * 255).round().astype(
            np.uint8
        )

    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)

    if arr.shape[2] == 4:
        alpha = arr[..., 3:4].astype(np.float32) / 255
        rgb = arr[..., :3].astype(np.float32) * alpha + 255 * (1 - alpha)
        arr = rgb.round().astype(np.uint8)
    elif arr.shape[2] != 3:
        raise ValueError(
            f"Image array must have 3 or 4 channels, got {arr.shape[2]}."
        )

    return np.ascontiguousarray(arr)


def pil_to_rgb(image: Any) -> np.ndarray:
    """Convert a PIL image to RGB ``uint8`` composed over white."""
    from PIL import Image

    if image.mode in ("RGBA", "LA", "P"):
        rgba = image.convert("RGBA")
        canvas = Image.new("RGBA", rgba.size, "white")
        canvas.alpha_composite(rgba)
        image = canvas

    return np.asarray(image.convert("RGB")).copy()


def figure_to_rgb(fig: Any, dpi: int) -> np.ndarray:
    """
    Rasterize a matplotlib figure at ``dpi``.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to rasterize.
    dpi : int
        Resolution.

    Returns
    -------
    numpy.ndarray
        ``(H, W, 3)`` ``uint8`` array.
    """
    import matplotlib
    from PIL import Image

    buffer = io.BytesIO()
    # 'standard' bbox: a global ``savefig.bbox = "tight"`` must not change
    # the size of the chart.
    with matplotlib.rc_context({"savefig.bbox": "standard"}):
        fig.savefig(
            buffer,
            format="png",
            dpi=dpi,
            facecolor=fig.get_facecolor(),
        )
    buffer.seek(0)

    with Image.open(buffer) as image:
        return pil_to_rgb(image)


def load_static_image(obj: Any) -> np.ndarray | None:
    """
    Load a static image source as RGB ``uint8``.

    Supports ``numpy.ndarray``, PIL images, ``bytes`` and file paths.

    Parameters
    ----------
    obj : Any
        Image source.

    Returns
    -------
    numpy.ndarray | None
        The image, or ``None`` if ``obj`` is not a static image source.
    """
    from PIL import Image

    if isinstance(obj, np.ndarray):
        return array_to_rgb(obj)

    if isinstance(obj, Image.Image):
        return pil_to_rgb(obj)

    if isinstance(obj, (bytes, bytearray)):
        with Image.open(io.BytesIO(obj)) as image:
            return pil_to_rgb(image)

    if isinstance(obj, (str, Path)):
        with Image.open(obj) as image:
            return pil_to_rgb(image)

    return None


def rasterize_image(source: Any, dpi: int) -> np.ndarray:
    """
    Return the RGB array of an image panel source.

    Static sources are returned as they are; figures are rasterized at
    ``dpi`` every time, so they always reflect their current state.
    """
    if isinstance(source, np.ndarray):
        return source

    fig = figure_of(source)
    if fig is None:
        raise TypeError(
            f"Unsupported image source: {type(source).__name__}."
        )

    return figure_to_rgb(fig, dpi)
