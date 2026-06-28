import time
from fastapi import Request, HTTPException, status, Depends
import redis.asyncio as aioredis
from loguru import logger

from app.core.config import REDIS_URL

# Connect to Redis
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


async def check_rate_limit(request: Request, limit: int = 100, window_secs: int = 60):
    """
    FastAPI dependency for sliding-window rate limiting.
    Defaults to 100 requests per minute per IP / Organization.
    """
    # 1. Identify client key
    client_ip = request.client.host if request.client else "unknown"
    client_identifier = client_ip

    # If organization id is present in state, rate limit per organization
    if hasattr(request.state, "org_id") and request.state.org_id:
        client_identifier = f"org_{request.state.org_id}"

    # Unique rate limit key based on request path and client
    key = f"rate_limit:{client_identifier}:{request.url.path}"
    now = time.time()

    try:
        async with redis_client.pipeline() as pipe:
            # Clean up old timestamps outside the sliding window
            pipe.zremrangebyscore(key, 0, now - window_secs)
            # Count remaining timestamps in window
            pipe.zcard(key)
            # Add current timestamp
            pipe.zadd(key, {str(now): now})
            # Set key expiration
            pipe.expire(key, window_secs)
            
            # Execute atomic transaction
            res = await pipe.execute()
            
            count = res[1]  # Output of ZCARD command
            
            if count > limit:
                logger.warning(f"Rate limit exceeded: {client_identifier} on {request.url.path} (Count: {count}/{limit})")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please throttle your traffic and try again."
                )

    except HTTPException:
        raise
    except Exception as e:
        # Fail-safe: if Redis connection drops, let the request proceed to avoid downtime
        logger.error(f"Redis rate limiting connection error: {e}")
        return
