"""
Auris - Main FastAPI Application
100% written from scratch.
"""
from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import APP_NAME, APP_VERSION, CORS_ORIGINS, DEBUG
from app.routes.agents import router as agents_router
from app.routes.auth import router as auth_router
from app.routes.billing import router as billing_router
from app.routes.calls import router as calls_router
from app.routes.telephony import router as telephony_router
from app.routes.knowledge_base import router as knowledge_base_router
from app.routes.campaigns import router as campaigns_router
from app.routes.api_keys import router as api_keys_router
from app.routes.phone_numbers import router as phone_numbers_router
from app.routes.analytics import router as analytics_router
from app.routes.monitor import router as monitor_router
from app.routes.whatsapp import router as whatsapp_router
from app.routes.integrations import router as integrations_router
from app.routes.cloned_voices import router as cloned_voices_router
from app.routes.reseller import router as reseller_router
from app.routes.mcp import router as mcp_router
from app.routes.retell_compat import router as retell_compat_router
from app.routes.links import router as links_router
from app.routes.supervisor import router as supervisor_router
from app.dependencies.rate_limit import check_rate_limit


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.config import SENTRY_DSN, ENVIRONMENT
    if SENTRY_DSN and not SENTRY_DSN.startswith("mock"):
        import sentry_sdk
        try:
            sentry_sdk.init(dsn=SENTRY_DSN, environment=ENVIRONMENT)
            logger.info(f"Initialized Sentry error tracking for environment: {ENVIRONMENT}")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")

    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    yield
    logger.info(f"Shutting down {APP_NAME}")


app = FastAPI(
    title=f"{APP_NAME} API",
    description="Auris Voice AI Platform — built from scratch",
    version=APP_VERSION,
    debug=DEBUG,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(agents_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(calls_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(telephony_router, prefix=API_PREFIX)
app.include_router(billing_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(knowledge_base_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(campaigns_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(api_keys_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(phone_numbers_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(analytics_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(whatsapp_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(integrations_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(cloned_voices_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(reseller_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(mcp_router, prefix=API_PREFIX, dependencies=[Depends(check_rate_limit)])
app.include_router(retell_compat_router, prefix=f"{API_PREFIX}/retell", dependencies=[Depends(check_rate_limit)])
app.include_router(retell_compat_router, prefix=f"{API_PREFIX}/retell-compat", dependencies=[Depends(check_rate_limit)])
app.include_router(monitor_router, prefix=API_PREFIX)
app.include_router(links_router, prefix=API_PREFIX)
app.include_router(supervisor_router, prefix=API_PREFIX)



@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }
