"""
Auris - Configuration Validation
Validates critical configuration on startup to fail fast.
Prevents runtime errors from missing/invalid configuration.
"""
from loguru import logger
import sys


def validate_config(environment: str, debug: bool) -> dict[str, str]:
    """
    Validate all critical configuration parameters.
    
    Args:
        environment: Current environment (local, staging, production)
        debug: Whether debug mode is enabled
        
    Returns:
        Dictionary of validation results
        
    Raises:
        ValueError: If critical configuration is missing or invalid
    """
    errors = []
    warnings = []
    
    # ── Critical Parameters (Must exist in production) ────────────────────────
    
    from app.core.config import (
        JWT_SECRET,
        DATABASE_URL,
        ASYNC_DATABASE_URL,
        OPENAI_API_KEY,
        DEEPGRAM_API_KEY,
        ELEVENLABS_API_KEY,
        TELNYX_API_KEY,
        REDIS_URL,
    )
    
    # 1. JWT_SECRET Validation
    if not JWT_SECRET or JWT_SECRET == "change-me-in-production-local-only-key-12345":
        if environment == "production":
            errors.append("JWT_SECRET is not configured for production")
        else:
            warnings.append("JWT_SECRET is using default local value")
    
    if JWT_SECRET and len(JWT_SECRET) < 32:
        errors.append(f"JWT_SECRET must be at least 32 characters (current: {len(JWT_SECRET)})")
    
    # 2. Database URL Validation
    if not DATABASE_URL or DATABASE_URL == "":
        errors.append("DATABASE_URL is not configured")
    elif not DATABASE_URL.startswith(("postgresql://", "sqlite://")):
        errors.append("DATABASE_URL must start with 'postgresql://' or 'sqlite://'")
    
    if not ASYNC_DATABASE_URL or ASYNC_DATABASE_URL == "":
        errors.append("ASYNC_DATABASE_URL is not configured")
    elif not ASYNC_DATABASE_URL.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
        errors.append("ASYNC_DATABASE_URL must start with 'postgresql+asyncpg://' or 'sqlite+aiosqlite://'")
    
    # 3. Redis URL Validation
    if not REDIS_URL or REDIS_URL == "":
        errors.append("REDIS_URL is not configured")
    elif not REDIS_URL.startswith("redis://"):
        errors.append("REDIS_URL must start with 'redis://'")
    
    # 4. AI Provider Keys Validation
    ai_providers = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "DEEPGRAM_API_KEY": DEEPGRAM_API_KEY,
        "ELEVENLABS_API_KEY": ELEVENLABS_API_KEY,
    }
    
    configured_providers = sum(1 for v in ai_providers.values() if v)
    if configured_providers == 0:
        errors.append("At least one AI provider (OpenAI, Deepgram, ElevenLabs) must be configured")
    elif configured_providers < 3:
        missing = [k for k, v in ai_providers.items() if not v]
        warnings.append(f"Not all AI providers configured. Missing: {', '.join(missing)}")
    
    # 5. Telephony Provider Validation (at least one required for outbound)
    if not TELNYX_API_KEY:
        warnings.append("TELNYX_API_KEY not configured - outbound calls will fail")
    
    # ── Production-Specific Checks ──────────────────────────────────────────
    
    if environment == "production":
        from app.core.config import (
            SENTRY_DSN,
            CORS_ORIGINS,
            BACKEND_URL,
            MINIO_ACCESS_KEY,
            MINIO_SECRET_KEY,
        )
        
        # Production should have Sentry configured
        if not SENTRY_DSN or SENTRY_DSN.startswith("mock"):
            warnings.append("SENTRY_DSN not configured - error tracking disabled")
        
        # Production CORS should not include localhost
        if CORS_ORIGINS and "localhost" in str(CORS_ORIGINS):
            warnings.append("CORS_ORIGINS includes localhost - review for production")
        
        # Production should have secure backend URL
        if BACKEND_URL and "localhost" in BACKEND_URL:
            errors.append("BACKEND_URL contains localhost - must use production domain")
        
        # Storage credentials should not be defaults
        if MINIO_ACCESS_KEY == "minioadmin" and MINIO_SECRET_KEY == "minioadmin":
            errors.append("MinIO credentials are using default values - change for production")
    
    # ── Warnings Summary ────────────────────────────────────────────────────
    
    if warnings:
        logger.warning(f"Configuration warnings ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            logger.warning(f"  {i}. {warning}")
    
    # ── Error Summary & Fail Fast ───────────────────────────────────────────
    
    if errors:
        logger.error(f"Configuration errors ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            logger.error(f"  {i}. {error}")
        
        error_message = (
            f"Configuration validation failed with {len(errors)} error(s):\n" +
            "\n".join(f"  - {e}" for e in errors)
        )
        raise ValueError(error_message)
    
    logger.info(f"✅ Configuration validation passed ({len(warnings)} warnings)")
    
    return {
        "status": "valid",
        "errors": 0,
        "warnings": len(warnings),
        "environment": environment,
    }


def validate_database_connection(database_url: str) -> bool:
    """
    Basic validation that database URL is connectable format.
    Full connection test happens at runtime.
    
    Args:
        database_url: Database connection string
        
    Returns:
        True if URL format is valid
        
    Raises:
        ValueError: If URL format is invalid
    """
    required_parts = {
        "postgresql://": ["://", "localhost" or "@"],
        "sqlite://": ["://"],
    }
    
    for db_type, parts in required_parts.items():
        if database_url.startswith(db_type):
            if all(part in database_url for part in parts):
                logger.debug(f"Database URL format valid: {db_type}")
                return True
    
    raise ValueError(f"Database URL format invalid: {database_url}")


def validate_jwt_secret(secret: str, environment: str = "local") -> bool:
    """
    Validate JWT secret meets security requirements.
    
    Args:
        secret: JWT secret value
        environment: Current environment
        
    Returns:
        True if secret is valid
        
    Raises:
        ValueError: If secret fails validation
    """
    if not secret:
        if environment == "production":
            raise ValueError("JWT_SECRET cannot be empty in production")
        logger.warning("JWT_SECRET is empty - using default (local development only)")
        return False
    
    if len(secret) < 32:
        raise ValueError(f"JWT_SECRET must be at least 32 characters (current: {len(secret)})")
    
    # Check for common weak patterns
    if secret == "change-me-in-production":
        if environment == "production":
            raise ValueError("JWT_SECRET is using default value - must be changed for production")
        logger.warning("JWT_SECRET is using default value - fine for local development")
        return True
    
    # Check for sufficient entropy (at least mixed case and numbers)
    has_upper = any(c.isupper() for c in secret)
    has_lower = any(c.islower() for c in secret)
    has_digit = any(c.isdigit() for c in secret)
    has_special = any(not c.isalnum() for c in secret)
    
    entropy_score = sum([has_upper, has_lower, has_digit, has_special])
    if entropy_score < 3:
        logger.warning(f"JWT_SECRET has low entropy (score: {entropy_score}/4) - consider using stronger key")
    
    return True


def log_config_summary(environment: str, debug: bool, cors_origins: list):
    """
    Log configuration summary for debugging.
    
    Args:
        environment: Current environment
        debug: Debug mode enabled
        cors_origins: CORS allowed origins
    """
    logger.info(f"Configuration Summary:")
    logger.info(f"  Environment: {environment}")
    logger.info(f"  Debug Mode: {debug}")
    logger.info(f"  CORS Origins: {', '.join(cors_origins[:3])}{'...' if len(cors_origins) > 3 else ''}")
    logger.info(f"  ✅ All critical configuration validated")
