from fastapi import FastAPI

from backend.routes.prompt_routes import router as prompt_router

from backend.routes.analytics_routes import (
    router as analytics_router
)

app = FastAPI(
    title="AI Governance Dashboard",
    version="1.0.0"
)

app.include_router(
    analytics_router
)

app.include_router(prompt_router)


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