"""
Auris - Prometheus Observability & Metrics Service
Exposes HTTP request latencies, active voice call gauges, and system health metrics.
"""
from prometheus_client import Gauge, Counter
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
from app.services.monitor_tracker import MonitorTracker

# Custom Prometheus Gauges and Counters
AURIS_ACTIVE_CALLS = Gauge("auris_active_calls", "Number of currently active voice calls across all transports")
AURIS_ACTIVE_LISTENERS = Gauge("auris_active_listeners", "Number of connected monitoring dashboard WebSocket listeners")
AURIS_TOTAL_CALLS_INITIATED = Counter("auris_total_calls_initiated", "Total number of voice calls initiated since server start")
AURIS_TOTAL_CALLS_ENDED = Counter("auris_total_calls_ended", "Total number of voice calls completed since server start")


def setup_prometheus_metrics(app: FastAPI) -> None:
    """Initialize Prometheus instrumentation and expose /metrics endpoints."""
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/api/v1/health", "/metrics", "/api/v1/metrics"],
        inprogress_name="auris_http_requests_inprogress",
        inprogress_labels=True,
    )

    # Instrument app and expose endpoints
    instrumentator.instrument(app)
    instrumentator.expose(app, endpoint="/metrics", tags=["Observability"])
    instrumentator.expose(app, endpoint="/api/v1/metrics", tags=["Observability"])
