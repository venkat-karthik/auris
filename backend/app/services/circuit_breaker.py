"""
Auris - Circuit Breaker Pattern
Prevents cascading failures when external services are degraded or down.
Implements: Closed → Open → Half-Open → Closed state machine.
"""
import time
import asyncio
from enum import Enum
from typing import Callable, Optional, Any, TypeVar, ParamSpec
from loguru import logger
from functools import wraps

T = TypeVar("T")
P = ParamSpec("P")


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing - reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker for external API calls.
    
    Prevents cascading failures:
    - CLOSED: Requests pass through normally
    - OPEN: Fails fast (threshold exceeded)
    - HALF_OPEN: Allows test requests to check recovery
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exceptions: tuple = (Exception,)
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Service name for logging
            failure_threshold: Consecutive failures before opening
            recovery_timeout: Seconds before attempting recovery (half-open)
            expected_exceptions: Exception types to count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count_in_half_open = 0
    
    async def call(
        self,
        coro: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> T:
        """
        Execute coroutine through circuit breaker.
        
        Args:
            coro: Async function to call
            *args, **kwargs: Arguments to pass
        
        Returns:
            Result from coro
        
        Raises:
            Exception: Original exception or CircuitBreakerOpen
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable (retrying in {self._time_until_retry():.1f}s)"
                )
        
        try:
            result = await coro(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count_in_half_open += 1
            logger.info(
                f"✅ Circuit breaker '{self.name}' half-open: "
                f"success {self.success_count_in_half_open}/{self.failure_threshold}"
            )
            
            if self.success_count_in_half_open >= self.failure_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(
            f"❌ Circuit breaker '{self.name}': "
            f"failure {self.failure_count}/{self.failure_threshold}"
        )
        
        if self.failure_count >= self.failure_threshold:
            self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if not self.last_failure_time:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _time_until_retry(self) -> float:
        """Get seconds until next retry attempt."""
        if not self.last_failure_time:
            return 0
        elapsed = time.time() - self.last_failure_time
        return max(0, self.recovery_timeout - elapsed)
    
    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        if self.state != CircuitState.OPEN:
            logger.error(
                f"🔴 Circuit breaker '{self.name}' OPENED. "
                f"Threshold exceeded ({self.failure_count}/{self.failure_threshold})"
            )
            self.state = CircuitState.OPEN
    
    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        logger.warning(
            f"🟡 Circuit breaker '{self.name}' entering HALF_OPEN. "
            f"Attempting recovery..."
        )
        self.state = CircuitState.HALF_OPEN
        self.failure_count = 0
        self.success_count_in_half_open = 0
    
    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        logger.info(
            f"🟢 Circuit breaker '{self.name}' CLOSED. "
            f"Service recovered successfully"
        )
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count_in_half_open = 0
    
    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time,
            "time_until_retry": self._time_until_retry() if self.state == CircuitState.OPEN else 0,
        }


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open (service unavailable)."""
    pass


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_or_create_circuit_breaker(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exceptions: tuple = (Exception,)
) -> CircuitBreaker:
    """Get or create a circuit breaker for a service."""
    if service_name not in _circuit_breakers:
        cb = CircuitBreaker(
            name=service_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=expected_exceptions
        )
        _circuit_breakers[service_name] = cb
        logger.debug(f"Created circuit breaker for service: {service_name}")
    
    return _circuit_breakers[service_name]


def circuit_breaker(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exceptions: tuple = (Exception,)
):
    """
    Decorator for async functions with circuit breaker protection.
    
    Usage:
        @circuit_breaker("openai", failure_threshold=3)
        async def call_openai_api(prompt: str):
            return await openai_client.chat.completions.create(...)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        cb = get_or_create_circuit_breaker(
            service_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=expected_exceptions
        )
        
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            async def call_coro():
                return await func(*args, **kwargs)
            
            return await cb.call(call_coro)
        
        return wrapper
    
    return decorator


def get_all_circuit_breakers() -> dict[str, dict]:
    """Get status of all circuit breakers."""
    return {name: cb.get_status() for name, cb in _circuit_breakers.items()}
