import re
import threading
import time
from collections import deque

MAX_WAIT = 90.0


def retry_wait(error_text: str, attempt: int) -> float:
    """Seconds to wait before a retry: the delay Google asks for ("retry in 59.3s"), else exponential."""
    match = re.search(r"retry in ([\d.]+)s", error_text) or re.search(r"'retryDelay': '([\d.]+)s'", error_text)
    if match:
        return min(float(match.group(1)) + 1.0, MAX_WAIT)
    return float(min(2**attempt, MAX_WAIT))


class RateLimiter:
    """Sliding one-minute window: blocks until `units` more units fit under `per_minute`."""

    def __init__(self, per_minute: int) -> None:
        self._per_minute = per_minute
        self._events: deque[tuple[float, int]] = deque()
        self._lock = threading.Lock()

    @property
    def per_minute(self) -> int:
        return self._per_minute

    def acquire(self, units: int = 1) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                while self._events and now - self._events[0][0] >= 60.0:
                    self._events.popleft()
                if sum(n for _, n in self._events) + units <= self._per_minute:
                    self._events.append((now, units))
                    return
                wait = 60.0 - (now - self._events[0][0]) + 0.1
            time.sleep(wait)
