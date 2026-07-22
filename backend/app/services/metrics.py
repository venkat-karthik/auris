"""
Auris - Prometheus Metrics & Observability
Tracks request latency, database queries, errors, and business metrics.
"""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from fastapi import FastAPI
import time


# Create registry
registry = CollectorRegistry()

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=registry
)

# Database metrics
DB_QUERY_COUNT = Counter(
    'db_queries_total',
    'Total database queries',
    ['query_type', 'table'],
    registry=registry
)

DB_QUERY_LATENCY = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=registry
)

# Error metrics
ERROR_COUNT = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint'],
    registry=registry
)

# Call metrics
CALLS_CREATED = Counter(
    'calls_created_total',
    'Total calls created',
    ['call_type', 'transport'],
    registry=registry
)

CALLS_COMPLETED = Counter(
    'calls_completed_total',
    'Total calls completed',
    ['status', 'disposition'],
    registry=registry
)

CALL_DURATION = Histogram(
    'call_duration_seconds',
    'Call duration',
    buckets=(1, 5, 10, 30, 60, 300, 600, 3600),
    registry=registry
)

# Agent metrics
AGENTS_TOTAL = Gauge(
    'agents_total',
    'Total active agents',
    ['org_id'],
    registry=registry
)

# Campaign metrics
CAMPAIGNS_RUNNING = Gauge(
    'campaigns_running',
    'Running campaigns',
    ['org_id'],
    registry=registry
)

# Connection pool metrics
DB_POOL_SIZE = Gauge(
    'db_pool_size',
    'Database connection pool size',
    registry=registry
)

DB_POOL_CHECKED_OUT = Gauge(
    'db_pool_checked_out',
    'Database connections checked out',
    registry=registry
)


def setup_prometheus_metrics(app: FastAPI) -> None:
    """
    Setup Prometheus metrics endpoint in FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    @app.get("/metrics")
    async def metrics():
        """Return Prometheus metrics."""
        return Response(
            content=generate_latest(registry),
            media_type=CONTENT_TYPE_LATEST
        )


def track_request(method: str, endpoint: str, status_code: int, latency: float) -> None:
    """Track HTTP request metrics."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)


def track_error(error_type: str, endpoint: str) -> None:
    """Track error metrics."""
    ERROR_COUNT.labels(error_type=error_type, endpoint=endpoint).inc()


def track_db_query(query_type: str, table: str = "", latency: float = 0.0) -> None:
    """Track database query metrics."""
    DB_QUERY_COUNT.labels(query_type=query_type, table=table).inc()
    if latency > 0:
        DB_QUERY_LATENCY.labels(query_type=query_type).observe(latency)


def track_call_created(call_type: str, transport: str) -> None:
    """Track call creation."""
    CALLS_CREATED.labels(call_type=call_type, transport=transport).inc()


def track_call_completed(status: str, disposition: str = "") -> None:
    """Track call completion."""
    CALLS_COMPLETED.labels(status=status, disposition=disposition).inc()


def track_call_duration(duration_seconds: float) -> None:
    """Track call duration."""
    CALL_DURATION.observe(duration_seconds)


def update_agent_count(org_id: int, count: int) -> None:
    """Update agent count gauge."""
    AGENTS_TOTAL.labels(org_id=org_id).set(count)


def update_campaign_count(org_id: int, count: int) -> None:
    """Update running campaign count gauge."""
    CAMPAIGNS_RUNNING.labels(org_id=org_id).set(count)


def update_pool_metrics(checked_in: int, checked_out: int) -> None:
    """Update connection pool metrics."""
    DB_POOL_SIZE.set(checked_in + checked_out)
    DB_POOL_CHECKED_OUT.set(checked_out)
