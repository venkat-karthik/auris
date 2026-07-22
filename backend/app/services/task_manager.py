"""
Auris - Background Task Manager
Safe background task execution with error handling and cleanup.
"""
import asyncio
from typing import Callable, Any, Optional
from loguru import logger
from contextlib import asynccontextmanager


class TaskManager:
    """Manages background tasks with proper error handling and cleanup."""
    
    def __init__(self):
        self.tasks = set()
    
    async def create_task(
        self,
        coro,
        name: str = "background_task",
        on_error: Optional[Callable] = None
    ) -> asyncio.Task:
        """
        Create a background task with error handling.
        
        Args:
            coro: Coroutine to run
            name: Task name for logging
            on_error: Callback on error (receives exception)
        
        Returns:
            asyncio.Task
        """
        async def wrapped_task():
            try:
                result = await coro
                logger.info(f"✅ Task completed: {name}")
                return result
            except asyncio.CancelledError:
                logger.warning(f"⚠️  Task cancelled: {name}")
                raise
            except Exception as e:
                logger.error(f"❌ Task failed: {name} - {type(e).__name__}: {e}")
                if on_error:
                    try:
                        await on_error(e) if asyncio.iscoroutinefunction(on_error) else on_error(e)
                    except Exception as callback_error:
                        logger.error(f"Error in error callback: {callback_error}")
                raise
        
        task = asyncio.create_task(wrapped_task())
        task.set_name(name)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        
        logger.debug(f"📌 Task created: {name} (ID: {task.get_name()})")
        return task
    
    async def cancel_all(self):
        """Cancel all pending tasks."""
        if not self.tasks:
            logger.debug("No pending tasks to cancel")
            return
        
        logger.info(f"Cancelling {len(self.tasks)} pending tasks...")
        
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for cancellation to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info(f"Cancelled all tasks")
    
    async def wait_all(self, timeout: Optional[float] = None):
        """Wait for all tasks to complete."""
        if not self.tasks:
            return
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for tasks (timeout={timeout}s)")
            await self.cancel_all()
    
    def get_pending_count(self) -> int:
        """Get number of pending tasks."""
        return len([t for t in self.tasks if not t.done()])


# Global task manager instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get or create global task manager."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


@asynccontextmanager
async def managed_task(name: str = "task", on_error: Optional[Callable] = None):
    """
    Context manager for managed task execution.
    
    Usage:
        async with managed_task("my_task") as task:
            await do_work()
    """
    manager = get_task_manager()
    task_ref = None
    
    try:
        yield manager
    except Exception as e:
        logger.error(f"Error in managed task {name}: {e}")
        if on_error:
            try:
                await on_error(e) if asyncio.iscoroutinefunction(on_error) else on_error(e)
            except Exception as callback_error:
                logger.error(f"Error in error callback: {callback_error}")
        raise


async def safe_background_task(
    coro,
    task_name: str = "background_operation",
    on_error: Optional[Callable] = None,
    log_errors: bool = True
) -> None:
    """
    Execute a coroutine as a fire-and-forget background task.
    
    Args:
        coro: Coroutine to execute
        task_name: Name for logging
        on_error: Error callback
        log_errors: Whether to log errors
    """
    manager = get_task_manager()
    await manager.create_task(coro, name=task_name, on_error=on_error)
