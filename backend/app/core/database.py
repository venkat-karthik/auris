"""
Auris - Async Database Setup (SQLAlchemy + asyncpg)
Optimized for multi-tenant scale with improved connection pooling
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool
from loguru import logger

from app.core.config import ASYNC_DATABASE_URL, ENVIRONMENT

import uuid

# ── Engine Configuration ──────────────────────────────────────────────────────
# Optimized pool settings for production:
# - pool_size: 20 (handle concurrent requests)
# - max_overflow: 40 (burst capacity)
# - pool_recycle: 3600s (recycle stale connections)
# - pool_pre_ping: True (test connection before use)

engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
    "future": True,
}

if "sqlite" in ASYNC_DATABASE_URL:
    # SQLite uses NullPool (no connection reuse)
    engine_kwargs["poolclass"] = NullPool
else:
    # PostgreSQL with asyncpg - optimized pooling
    engine_kwargs.update({
        "pool_size": 20,  # Base connections
        "max_overflow": 40,  # Overflow connections for bursts
        "pool_recycle": 3600,  # Recycle connections every hour
        "connect_args": {
            "statement_cache_size": 0,  # Disable statement caching for security
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4().hex}__",
            "timeout": 30,  # Connection timeout
            "command_timeout": 30,  # Query timeout
        }
    })

try:
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        **engine_kwargs
    )
    logger.info(
        f"Database engine created: {ASYNC_DATABASE_URL.split('@')[1] if '@' in ASYNC_DATABASE_URL else 'sqlite'}"
    )
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent additional queries after commit
    autocommit=False,  # Manual transaction control
    autoflush=False,  # Manual flush control
)

# ── Base class for all ORM models ─────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models"""
    pass

# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    """
    FastAPI dependency for database sessions.
    
    Yields a new AsyncSession for each request.
    Automatically commits on success, rolls back on exception.
    
    Usage:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            # Use db session
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Only commit if no exception occurred
            if session.is_active:
                await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# ── Connection pooling utilities ──────────────────────────────────────────────

async def get_db_pool_status():
    """
    Get current database connection pool status.
    Useful for monitoring and debugging.
    
    Returns:
        Dictionary with pool stats
    """
    pool = engine.pool
    if hasattr(pool, '_conn_record_cache'):
        return {
            "pool_type": type(pool).__name__,
            "size": getattr(pool, 'size', None),
            "checked_in": getattr(pool, '_checked_in', None),
            "checked_out": getattr(pool, '_checked_out', None),
        }
    return {"pool_type": "NullPool (SQLite)", "connections": "unlimited"}


async def dispose_pool():
    """
    Dispose of all connections in the pool.
    Call this during graceful shutdown.
    """
    await engine.dispose()
    logger.info("Database connection pool disposed")
