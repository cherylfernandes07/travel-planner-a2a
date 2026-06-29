# ─────────────────────────────────────────────────────────────
# rate_limiter.py
# Per-IP rate limiting using Redis.
# Survives server restarts and works across multiple instances.
# ─────────────────────────────────────────────────────────────

import os
import time
import redis.asyncio as aioredis
from fastapi import Request, HTTPException

# ── Config ────────────────────────────────────────────────────

MAX_REQUESTS_PER_DAY = 5
WINDOW_SECONDS = 86400  # 24 hours

# ── Redis client ──────────────────────────────────────────────

redis_client = aioredis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True,
)

# ── Helpers ───────────────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    """Extract real IP — handles proxies and load balancers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def _rate_limit_key(ip: str) -> str:
    """Redis key for this IP's request log."""
    return f"rate_limit:{ip}"

# ── Core limiter ──────────────────────────────────────────────

async def check_rate_limit(ip: str) -> dict:
    """
    Checks and records a request for the given IP.
    Raises HTTP 429 if the daily limit is exceeded.
    Uses a Redis sorted set — timestamps are scores,
    so expiry is a simple range delete.
    """
    key = _rate_limit_key(ip)
    now = time.time()
    window_start = now - WINDOW_SECONDS

    pipe = redis_client.pipeline()

    # Remove timestamps older than the window
    pipe.zremrangebyscore(key, "-inf", window_start)
    # Count remaining requests in window
    pipe.zcard(key)
    # Add current request timestamp
    pipe.zadd(key, {str(now): now})
    # Set key expiry to window size so Redis auto-cleans
    pipe.expire(key, WINDOW_SECONDS)

    results = await pipe.execute()
    count_before = results[1]  # count before adding current request

    if count_before >= MAX_REQUESTS_PER_DAY:
        # Find oldest request to calculate retry time
        oldest = await redis_client.zrange(key, 0, 0, withscores=True)
        retry_after = int(oldest[0][1] + WINDOW_SECONDS - now) if oldest else WINDOW_SECONDS

        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": MAX_REQUESTS_PER_DAY,
                "window": "24 hours",
                "retry_after_seconds": retry_after,
                "message": (
                    f"You have used all {MAX_REQUESTS_PER_DAY} plan requests for today. "
                    f"Try again in {retry_after // 3600}h {(retry_after % 3600) // 60}m."
                ),
            },
        )

    return {
        "ip": ip,
        "requests_used": count_before + 1,
        "requests_remaining": MAX_REQUESTS_PER_DAY - count_before - 1,
        "limit": MAX_REQUESTS_PER_DAY,
        "window": "24 hours",
    }


async def get_rate_limit_status(ip: str) -> dict:
    """Check current usage without consuming a request."""
    key = _rate_limit_key(ip)
    now = time.time()
    window_start = now - WINDOW_SECONDS

    await redis_client.zremrangebyscore(key, "-inf", window_start)
    count = await redis_client.zcard(key)

    return {
        "ip": ip,
        "requests_used": count,
        "requests_remaining": max(0, MAX_REQUESTS_PER_DAY - count),
        "limit": MAX_REQUESTS_PER_DAY,
        "window": "24 hours",
    }