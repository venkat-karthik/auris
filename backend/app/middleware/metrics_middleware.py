"""
Auris - Metrics Middleware
Tracks HTTP request metrics and records them to Prometheus.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from app.services.metrics import REQUEST_COUNT, REQUEST_LATENCY, ERROR_COUNT


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request metrics."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Extract endpoint path (remove IDs for better grouping)
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method
        
        # Track request start
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate latency
            latency = time.time() - start_time
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(latency)
            
            # Track errors
            if response.status_code >= 500:
                ERROR_COUNT.labels(
                    error_type="server_error",
                    endpoint=endpoint
                ).inc()
            elif response.status_code >= 400:
                ERROR_COUNT.labels(
                    error_type="client_error",
                    endpoint=endpoint
                ).inc()
            
            return response
            
        except Exception as e:
            # Track exception
            latency = time.time() - start_time
            ERROR_COUNT.labels(
                error_type=type(e).__name__,
                endpoint=endpoint
            ).inc()
            raise
    
    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """
        Normalize endpoint path by removing IDs.
        Example: /api/v1/agents/123 -> /api/v1/agents/{id}
        """
        parts = path.split('/')
        normalized = []
        
        for part in parts:
            # Replace numeric IDs with {id}
            if part.isdigit():
                normalized.append("{id}")
            else:
                normalized.append(part)
        
        return "/".join(normalized)
