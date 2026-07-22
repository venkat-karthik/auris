"""
Auris - Rate Limiting Configuration
Configurable rate limits for different endpoint types.
"""

# Rate limit configurations (requests per window)
RATE_LIMITS = {
    # Auth endpoints - stricter limits
    "auth": {
        "limit": 5,
        "window_secs": 300,  # 5 requests per 5 minutes
        "description": "Anti-brute-force protection"
    },
    
    # API endpoints - moderate limits
    "api": {
        "limit": 100,
        "window_secs": 60,  # 100 requests per minute
        "description": "General API rate limit"
    },
    
    # Call creation - lower limits (resource intensive)
    "calls": {
        "limit": 20,
        "window_secs": 60,  # 20 calls per minute
        "description": "Call creation limit"
    },
    
    # Campaign endpoints - lower limits
    "campaigns": {
        "limit": 10,
        "window_secs": 60,  # 10 campaigns per minute
        "description": "Campaign operation limit"
    },
    
    # File uploads - very strict
    "uploads": {
        "limit": 5,
        "window_secs": 300,  # 5 uploads per 5 minutes
        "description": "File upload limit"
    },
    
    # Analytics - higher limits (read-only)
    "analytics": {
        "limit": 200,
        "window_secs": 60,  # 200 requests per minute
        "description": "Analytics query limit"
    },
}


def get_rate_limit(endpoint_type: str) -> tuple[int, int]:
    """
    Get rate limit configuration for endpoint type.
    
    Args:
        endpoint_type: Type of endpoint (auth, api, calls, etc)
    
    Returns:
        (limit, window_secs) tuple
    """
    config = RATE_LIMITS.get(endpoint_type, RATE_LIMITS["api"])
    return config["limit"], config["window_secs"]


# Headers that indicate rate limiting
RATE_LIMIT_HEADERS = {
    "X-RateLimit-Limit": "Total requests allowed in window",
    "X-RateLimit-Remaining": "Requests remaining in window",
    "X-RateLimit-Reset": "Unix timestamp when window resets",
}


def create_rate_limit_headers(
    limit: int,
    remaining: int,
    reset_timestamp: int
) -> dict[str, str]:
    """
    Create rate limit response headers.
    
    Args:
        limit: Total requests allowed
        remaining: Requests remaining
        reset_timestamp: Unix timestamp of window reset
    
    Returns:
        Dictionary of rate limit headers
    """
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(reset_timestamp),
    }
