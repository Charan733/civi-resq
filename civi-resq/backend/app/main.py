"""
CIVI-RESQ Backend -- Main Application Entrypoint
----------------------------------------------------
AI-Powered Urban Infrastructure Risk & Intervention Planning System.
Run with: uvicorn app.main:app --reload
API docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth_router, zones_router, simulate_router, analytics_router, assistant_router, reports_router

settings = get_settings()

app = FastAPI(
    title="CIVI-RESQ API",
    description="AI-Powered Urban Infrastructure Risk & Intervention Planning System — "
                 "a decision-support tool for civil engineers and urban planners. "
                 "Predictions are AI-assisted preliminary risk assessments, not certified "
                 "structural or engineering safety determinations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(zones_router.router)
app.include_router(simulate_router.router)
app.include_router(analytics_router.router)
app.include_router(assistant_router.router)
app.include_router(reports_router.router)


@app.get("/")
def root():
    return {
        "service": "CIVI-RESQ API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
