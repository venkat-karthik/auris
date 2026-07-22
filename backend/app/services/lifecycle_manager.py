"""
Auris - Service Lifecycle Manager
Manages startup/shutdown of external services (Redis, database, WebSockets).
"""
import asyncio
from typing import Callable, Optional, Dict, Any
from loguru import logger


class LifecycleManager:
    """
    Centralized service lifecycle management.
    
    Tracks all external service connections and ensures proper cleanup on shutdown.
    """
    
    def __init__(self):
        self.startup_hooks: list[Callable] = []
        self.shutdown_hooks: list[Callable] = []
        self.services: Dict[str, Any] = {}
    
    def register_startup(self, hook: Callable) -> None:
        """Register a startup hook to run during app startup."""
        self.startup_hooks.append(hook)
        logger.debug(f"Registered startup hook: {hook.__name__}")
    
    def register_shutdown(self, hook: Callable) -> None:
        """Register a shutdown hook to run during app shutdown."""
        self.shutdown_hooks.append(hook)
        logger.debug(f"Registered shutdown hook: {hook.__name__}")
    
    def register_service(self, name: str, service: Any) -> None:
        """Register a service for lifecycle tracking."""
        self.services[name] = service
        logger.debug(f"Registered service: {name}")
    
    async def startup(self) -> None:
        """Execute all startup hooks."""
        logger.info(f"Running {len(self.startup_hooks)} startup hooks...")
        for hook in self.startup_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
                logger.info(f"✅ Startup hook completed: {hook.__name__}")
            except Exception as e:
                logger.error(f"❌ Startup hook failed: {hook.__name__} - {e}")
                raise
    
    async def shutdown(self) -> None:
        """Execute all shutdown hooks in reverse order."""
        if not self.shutdown_hooks:
            logger.debug("No shutdown hooks registered")
            return
        
        logger.info(f"Running {len(self.shutdown_hooks)} shutdown hooks...")
        
        # Run hooks in reverse order (LIFO) - shutdown opposite of startup
        for hook in reversed(self.shutdown_hooks):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
                logger.info(f"✅ Shutdown hook completed: {hook.__name__}")
            except Exception as e:
                logger.error(f"⚠️  Shutdown hook error: {hook.__name__} - {e}")
                # Don't raise - continue with other hooks


# Global lifecycle manager instance
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get or create global lifecycle manager."""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager()
    return _lifecycle_manager


async def redis_startup() -> None:
    """Initialize Redis connection on startup."""
    try:
        from app.dependencies.rate_limit import redis_client
        from app.core.config import REDIS_URL
        
        # Test Redis connection
        result = await redis_client.ping()
        if result:
            logger.info("✅ Redis connection established")
        else:
            logger.warning("⚠️  Redis connection test returned false")
    except ImportError:
        logger.debug("Redis client not configured")
    except Exception as e:
        logger.error(f"Redis startup failed: {e}")
        raise


async def redis_shutdown() -> None:
    """Cleanup Redis connection on shutdown."""
    try:
        from app.dependencies.rate_limit import redis_client
        
        if redis_client and hasattr(redis_client, 'close'):
            await redis_client.close()
            logger.info("✅ Redis connection closed")
    except ImportError:
        logger.debug("Redis client not configured")
    except Exception as e:
        logger.error(f"Redis shutdown error: {e}")


async def database_startup() -> None:
    """Verify database connectivity on startup."""
    try:
        from app.core.database import get_db_connection
        
        async with get_db_connection() as conn:
            result = await conn.execute("SELECT 1")
            if result:
                logger.info("✅ Database connection verified")
    except Exception as e:
        logger.error(f"Database startup failed: {e}")
        raise


async def database_shutdown() -> None:
    """Cleanup database connections on shutdown."""
    try:
        from app.core.database import dispose_pool
        await dispose_pool()
        logger.info("✅ Database connection pool disposed")
    except Exception as e:
        logger.error(f"Database shutdown error: {e}")


async def setup_lifecycle_manager() -> LifecycleManager:
    """
    Setup the lifecycle manager with all service hooks.
    Call this during app startup.
    """
    manager = get_lifecycle_manager()
    
    # Register startup/shutdown pairs (startup first, then shutdown will run them in reverse)
    manager.register_startup(redis_startup)
    manager.register_startup(database_startup)
    
    manager.register_shutdown(redis_shutdown)
    manager.register_shutdown(database_shutdown)
    
    return manager
