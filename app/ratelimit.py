"""Protects the public link from running up a bill.

Two limits, both kept in memory:
- each visitor (by IP address) gets a number of requests per minute;
- the whole app gets a number of paid requests per day.
"""

import threading
import time


class RateLimiter:
    def __init__(self, per_minute: int = 30, daily_cap: int = 2000):
        self.per_minute = per_minute
        self.daily_cap = daily_cap
        self._recent: dict[str, list[float]] = {}
        self._day = ""
        self._day_count = 0
        self._lock = threading.Lock()

    def check(self, visitor: str) -> str | None:
        """None if the request may go ahead, else "rate_limited" or "daily_cap"."""
        now = time.time()
        today = time.strftime("%Y-%m-%d", time.gmtime(now))
        with self._lock:
            if today != self._day:
                self._day, self._day_count = today, 0
                self._recent.clear()
            if self._day_count >= self.daily_cap:
                return "daily_cap"
            times = [t for t in self._recent.get(visitor, []) if t > now - 60]
            if len(times) >= self.per_minute:
                self._recent[visitor] = times
                return "rate_limited"
            times.append(now)
            self._recent[visitor] = times
            self._day_count += 1
            return None
