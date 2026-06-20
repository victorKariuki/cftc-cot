"""
Caching backends for the CFTC COT SDK.

COT data updates weekly, so caching API responses dramatically reduces redundant
network traffic. Two backends are provided:

- :class:`MemoryCache`: in-process dict with per-entry expiry (no dependencies).
- :class:`DiskCache`: persistent cache backed by the optional ``diskcache`` package.

Both honor a TTL (time-to-live) in seconds; a TTL of 24 hours is recommended.
"""
from __future__ import annotations
import time
from typing import Any, Optional, Protocol, runtime_checkable

from .exceptions import COTError

DEFAULT_TTL: int = 86400  # 24 hours


@runtime_checkable
class COTCache(Protocol):
    """Protocol implemented by all cache backends."""

    def get(self, key: str) -> Optional[Any]:
        """Return the cached value for ``key``, or ``None`` if missing/expired."""
        ...

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """Store ``value`` under ``key``, expiring after ``ttl`` seconds."""
        ...


class MemoryCache:
    """In-process cache using a dict with per-entry expiry timestamps."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.time() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        self._store[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        """Remove all cached entries."""
        self._store.clear()


class DiskCache:
    """
    Persistent cache backed by the optional ``diskcache`` package.

    Args:
        cache_dir: Directory in which to store cache files.

    Raises:
        COTError: If the ``diskcache`` package is not installed.
    """

    def __init__(self, cache_dir: str = "./cot_cache") -> None:
        try:
            import diskcache  # noqa: PLC0415  (lazy, optional dependency)
        except ImportError as exc:  # pragma: no cover - exercised via skip
            raise COTError(
                "Disk caching requires the 'diskcache' package. "
                "Install it with: pip install cftc-cot-soda[cache]"
            ) from exc
        self._cache = diskcache.Cache(cache_dir)

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        self._cache.set(key, value, expire=ttl)

    def clear(self) -> None:
        """Remove all cached entries."""
        self._cache.clear()


def build_cache(
    cache: Optional[str], cache_dir: Optional[str] = None
) -> Optional[COTCache]:
    """
    Construct a cache backend from a string selector.

    Args:
        cache: ``"memory"``, ``"disk"``, ``None``, or an already-built cache object.
        cache_dir: Directory for the disk backend (defaults to ``./cot_cache``).

    Returns:
        A cache instance, or ``None`` if caching is disabled.

    Raises:
        COTError: If an unknown cache type is requested.
    """
    if cache is None:
        return None
    if isinstance(cache, str):
        if cache == "memory":
            return MemoryCache()
        if cache == "disk":
            return DiskCache(cache_dir or "./cot_cache")
        raise COTError(f"Unknown cache type: {cache!r} (expected 'memory' or 'disk')")
    # Assume a pre-built cache object implementing the COTCache protocol.
    return cache
