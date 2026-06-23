"""
Auris - Async Database Setup (SQLAlchemy + asyncpg)
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import ASYNC_DATABASE_URL

# ── Engine ────────────────────────────────────────────────────────────────────
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}
if "sqlite" not in ASYNC_DATABASE_URL:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    **engine_kwargs
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ── Base class for all ORM models ─────────────────────────────────────────────
class Base(DeclarativeBase):
    pass

# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
