from __future__ import annotations

import threading
import time


class TokenBucket:
    """Thread-safe token bucket for per-second rate limiting."""

    def __init__(self, rate_per_second: int, capacity: int | None = None) -> None:
        if rate_per_second <= 0:
            raise ValueError("rate_per_second must be positive")
        self._rate = float(rate_per_second)
        self._capacity = float(capacity if capacity is not None else rate_per_second)
        self._tokens = self._capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
                self._last_refill = now
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                deficit = tokens - self._tokens
                sleep_for = deficit / self._rate
            time.sleep(sleep_for)
