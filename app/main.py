"""
NETA AI — FastAPI application entry point.
Mounts all module routers.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.geojson_mapping.router import router as geo_router
from app.ground_operations.router import router as ground_router
from app.security_auth.router import router as auth_router
from app.news_intelligence.router import router as news_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection
    from app.database_design.database import engine
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    yield
    # Shutdown: dispose connection pool
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Real-time political campaign intelligence platform for Serilingampally AC-52",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS — strict whitelist
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(geo_router)
app.include_router(ground_router)
app.include_router(news_router)


@app.get("/api/health", tags=["System"])
async def health_check():
    return JSONResponse({"status": "ok", "service": "neta-api", "version": "1.0.0"})
