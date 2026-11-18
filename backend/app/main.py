from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router
import app.models  # Ensures all models are registered in Base metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-initialize database tables if not already existing
    if settings.ENVIRONMENT != "testing":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    if settings.ENVIRONMENT != "testing":
        await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ClinicFlow Production Medical EHR, Triage, and Scheduling API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck for AWS Application Load Balancer & ECS Fargate
@app.get("/healthz", tags=["System Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "clinicflow-api",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Mount API V1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Fallback handler to prevent unhandled 500s from leaking system trace details."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal clinical platform error occurred. Please contact IT support.", "error": str(exc)},
    )
