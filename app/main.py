"""
NETA AI — FastAPI application entry point.
Mounts all module routers.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.geojson_mapping.router import router as geo_router
from app.ground_operations.router import router as ground_router
from app.security_auth.router import router as auth_router
from app.news_intelligence.router import router as news_router
from app.booth_management.router import router as booth_router
from app.prediction_sentiment.router import router as prediction_router
from app.opposition_intelligence.router import router as opposition_router
from app.whatsapp_integration.router import router as whatsapp_router
from app.intelligence.router import router as intelligence_router
from app.intelligence.sse import sse_router
from app.admin.router import router as admin_router
from app.demographics.router import router as demographics_router
from app.telegram_integration.router import router as telegram_router


_redis_client = None


async def _get_redis():
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    """IP-based rate limit: 10 login attempts per IP per 60 seconds."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/auth/login" and request.method == "POST":
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                ip = forwarded.split(",")[0].strip()
            elif request.client:
                ip = request.client.host
            else:
                ip = "unknown"
            key = f"rl:login:{ip}"
            try:
                rc = await _get_redis()
                count = await rc.incr(key)
                if count == 1:
                    await rc.expire(key, 60)
                if count > 10:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many login attempts. Try again in 60 seconds."},
                        headers={"Retry-After": "60"},
                    )
            except Exception:
                pass  # Redis unavailable — fail open, don't block legitimate logins
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection
    from app.database_design.database import engine
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    yield
    # Shutdown: dispose connection pool
    await engine.dispose()
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Real-time political campaign intelligence platform for Serilingampally AC-52",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(LoginRateLimitMiddleware)

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
app.include_router(booth_router)
app.include_router(prediction_router)
app.include_router(opposition_router)
app.include_router(whatsapp_router)
app.include_router(intelligence_router)
app.include_router(sse_router)
app.include_router(admin_router)
app.include_router(demographics_router)
app.include_router(telegram_router)


@app.get("/api/health", tags=["System"])
async def health_check():
    return JSONResponse({"status": "ok", "service": "neta-api", "version": "1.0.0"})
