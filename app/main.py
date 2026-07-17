from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.response import api_response
from app.middleware.request_id import RequestIDMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.database import engine
from app.models import Base
import os

# Setup logging immediately
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://localhost:3000",
        "https://web-production-2c654.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Run Alembic migrations on startup."""
    import subprocess
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
    except Exception as e:
        print(f"Migration warning: {e}")


@app.get("/health", tags=["Health Check"])
async def health_check():
    return api_response(
        data={
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        },
        message="Saleszy v2 is running."
    )


# --- Import and include Routers ---
from app.api.v1.router import router as v1_router
app.include_router(v1_router)