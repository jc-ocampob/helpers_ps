from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict

import numpy as np

from ..constants import DEFAULT_CACHE_MB


def make_key(token: str, dpi: int, document: str) -> str:
    """
    Build a cache key from the renderer token, the resolution and the
    complete HTML document of a table.

    Parameters
    ----------
    token : str
        Identifies the renderer that produced the image.
    dpi : int
        Render resolution.
    document : str
        Complete HTML document.

    Returns
    -------
    str
        SHA-1 hex digest.
    """
    digest = hashlib.sha1()
    digest.update(f"{token}|{dpi}|".encode())
    digest.update(document.encode("utf-8"))
    return digest.hexdigest()


class RenderCache:
    """
    Thread-safe LRU cache of rendered table images, limited by memory.

    Tables are cached by *content* (the HTML that is rendered), not by
    object identity. Re-running a notebook cell that rebuilds the same
    table, or changing only a title or a gap, therefore never launches the
    browser again.

    Parameters
    ----------
    max_mb : float, default ``DEFAULT_CACHE_MB``
        Memory budget in megabytes. ``0`` disables caching.

    Attributes
    ----------
    hits, misses : int
        Lookup counters.

    Examples
    --------
    >>> sheet = TableSheet(df, cache=RenderCache(max_mb=0))  # no cache
    """

    def __init__(self, max_mb: float = DEFAULT_CACHE_MB) -> None:
        if max_mb < 0:
            raise ValueError("max_mb must be >= 0.")
        self.max_bytes = int(max_mb * 1024 * 1024)
        self.hits = 0
        self.misses = 0
        self._items: OrderedDict[str, np.ndarray] = OrderedDict()
        self._bytes = 0
        self._lock = threading.Lock()

    def get(self, key: str) -> np.ndarray | None:
        """Return the cached image or ``None``."""
        with self._lock:
            image = self._items.get(key)
            if image is None:
                self.misses += 1
                return None
            self._items.move_to_end(key)
            self.hits += 1
            return image

    def put(self, key: str, image: np.ndarray) -> None:
        """Store ``image`` (made read-only), evicting least-recent entries."""
        if self.max_bytes == 0 or image.nbytes > self.max_bytes:
            return
        image.flags.writeable = False
        with self._lock:
            previous = self._items.pop(key, None)
            if previous is not None:
                self._bytes -= previous.nbytes
            self._items[key] = image
            self._bytes += image.nbytes
            while self._bytes > self.max_bytes and self._items:
                _, evicted = self._items.popitem(last=False)
                self._bytes -= evicted.nbytes

    def clear(self) -> None:
        """Remove every cached image and reset the counters."""
        with self._lock:
            self._items.clear()
            self._bytes = 0
            self.hits = 0
            self.misses = 0

    @property
    def size_mb(self) -> float:
        """Memory currently used, in megabytes."""
        return self._bytes / (1024 * 1024)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, key: object) -> bool:
        return key in self._items

    def __repr__(self) -> str:
        return (
            f"RenderCache(items={len(self)}, "
            f"size_mb={self.size_mb:.1f}/{self.max_bytes / 1048576:.0f}, "
            f"hits={self.hits}, misses={self.misses})"
        )


#: Process-wide cache shared by every ``TableSheet`` by default.
DEFAULT_CACHE = RenderCache()


def clear_render_cache() -> None:
    """Empty the process-wide render cache."""
    DEFAULT_CACHE.clear()
