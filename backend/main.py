import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.database.init_db import init_db
from backend.rate_limiter import limiter
from backend.routes.auth_routes import router as auth_router
from backend.routes.evaluation_routes import router as evaluation_router
from backend.routes.prompt_routes import router as prompt_router
from backend.routes.response_routes import router as response_router

from backend.routes.analytics_routes import (
    router as analytics_router
)

# Configure root logger so all module-level loggers (e.g. auth_service)
# emit to stdout with timestamps.  Set level to INFO so successful sends
# are visible; errors will also appear regardless of this threshold.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

# CORS allowed origins — configurable via env var so production and local
# dev don't require a code change.
# Set CORS_ALLOWED_ORIGINS in Railway to a comma-separated list, e.g.:
#   https://humble-reflection-production-22fc.up.railway.app,http://localhost:3000
_cors_env = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8501"
)
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_env.split(",") if o.strip()]
print("CORS_ORIGINS:", CORS_ORIGINS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI Governance Dashboard",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router)

app.include_router(
    analytics_router
)

app.include_router(prompt_router)

app.include_router(response_router)

app.include_router(evaluation_router)


@app.get("/")
def root():
    return {
        "message": "AI Governance Dashboard API Running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
