"""Simple in-memory sliding-window rate limiter. No external deps."""

import functools
import time
from collections import deque

from quart import request

# {key: deque of timestamps}
_hits: dict[str, deque] = {}


def get_real_ip() -> str:
    return (
        request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        .split(",")[0]
        .strip()
    )


def rate_limit(max_calls: int = 5, period: int = 60, key_func=get_real_ip):
    """Decorator for route-level rate limiting.

    Returns 429 with Retry-After header when limit exceeded.
    """

    def decorator(f):
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            key = f"{f.__name__}:{key_func()}"
            now = time.monotonic()
            window = _hits.setdefault(key, deque())

            # Evict expired entries
            while window and window[0] <= now - period:
                window.popleft()

            if len(window) >= max_calls:
                retry_after = int(period - (now - window[0])) + 1
                return (
                    {"message": "Too many requests"},
                    429,
                    {"Retry-After": str(retry_after)},
                )

            window.append(now)
            return await f(*args, **kwargs)

        return wrapper

    return decorator


async def check_security_rate_limit():
    """before_request hook for the security blueprint — limits auth endpoints."""
    key = f"security:{get_real_ip()}"
    now = time.monotonic()
    period = 60
    max_calls = 10
    window = _hits.setdefault(key, deque())

    while window and window[0] <= now - period:
        window.popleft()

    if len(window) >= max_calls:
        retry_after = int(period - (now - window[0])) + 1
        return {"message": "Too many requests"}, 429, {"Retry-After": str(retry_after)}

    window.append(now)
