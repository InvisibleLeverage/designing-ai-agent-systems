"""
Tool Cache — Chapter 8: Deployment and Scaling

Decorator-based TTL cache for agent tool outputs.
Cache hit = no external call = near-zero cost.
Track hit rate as a production metric — below 20% suggests queries are too varied.

TTL guidelines:
  Stock prices / live data : 60 seconds
  News articles            : 3600 seconds (1 hour)
  Documentation pages      : 86400 seconds (24 hours)
  Immutable records        : None (never expires)
"""
import functools
import hashlib
import json
import time
from typing import Any, Optional


class ToolCache:
    """
    In-memory TTL cache for tool outputs.
    Production swap: replace _store with Redis (use SETEX for TTL-based expiry).
    """

    def __init__(self):
        self._store:     dict[str, tuple[Any, float]] = {}  # key → (value, expires_at)
        self._hits:      int = 0
        self._misses:    int = 0

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            self._misses += 1
            return None
        value, expires_at = self._store[key]
        if expires_at is not None and time.time() > expires_at:
            del self._store[key]
            self._misses += 1
            return None
        self._hits += 1
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float]) -> None:
        expires_at = (time.time() + ttl_seconds) if ttl_seconds is not None else None
        self._store[key] = (value, expires_at)

    def invalidate(self, key: str) -> bool:
        return bool(self._store.pop(key, None))

    def clear(self) -> None:
        self._store.clear()
        self._hits = self._misses = 0

    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total else 0.0

    def stats(self) -> dict:
        return {
            "entries":   len(self._store),
            "hits":      self._hits,
            "misses":    self._misses,
            "hit_rate":  f"{self.hit_rate():.1%}",
        }


# Module-level default cache instance
_default_cache = ToolCache()


def cache_key(fn_name: str, args: tuple, kwargs: dict) -> str:
    """Deterministic cache key: MD5(fn_name + args + sorted kwargs)."""
    payload = json.dumps(
        {"fn": fn_name, "args": list(args), "kwargs": dict(sorted(kwargs.items()))},
        sort_keys=True, default=str,
    )
    return hashlib.md5(payload.encode()).hexdigest()  # noqa: S324


def cache_tool(ttl_seconds: float = 300, cache: Optional[ToolCache] = None):
    """
    Decorator: cache a tool function's output with TTL.

    Usage:
        @cache_tool(ttl_seconds=3600)
        def fetch_news(query: str) -> dict: ...

        @cache_tool(ttl_seconds=60)
        def get_stock_price(ticker: str) -> dict: ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            c   = cache or _default_cache
            key = cache_key(fn.__name__, args, kwargs)
            hit = c.get(key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            c.set(key, result, ttl_seconds)
            return result
        wrapper.cache       = cache or _default_cache
        wrapper.invalidate  = lambda *a, **kw: (cache or _default_cache).invalidate(cache_key(fn.__name__, a, kw))
        return wrapper
    return decorator


def get_default_cache() -> ToolCache:
    return _default_cache


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    call_count = 0

    @cache_tool(ttl_seconds=5)
    def fetch_page(url: str) -> dict:
        global call_count
        call_count += 1
        return {"url": url, "content": f"Page content for {url}", "fetched_at": time.time()}

    @cache_tool(ttl_seconds=1)     # short TTL — will expire
    def get_price(ticker: str) -> dict:
        global call_count
        call_count += 1
        return {"ticker": ticker, "price": 42.0}

    # First calls — cache misses
    r1 = fetch_page("https://docs.example.com/api")
    r2 = fetch_page("https://docs.example.com/api")  # cache hit
    r3 = fetch_page("https://docs.example.com/sdk")  # different URL — miss

    print(f"Calls made: {call_count} (expected 2)")
    print(f"Cache stats: {fetch_page.cache.stats()}")

    # TTL expiry test
    p1 = get_price("AAPL")
    time.sleep(1.1)
    p2 = get_price("AAPL")   # expired — cache miss
    print(f"\nPrice calls made: 2 (hit rate after expiry: {get_price.cache.hit_rate():.0%})")
    print(f"Default cache stats: {_default_cache.stats()}")
