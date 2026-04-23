"""
Zippie - P2P Payment Platform for Zimbabwe
"""

import logging
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.database import Base, engine

# Load environment variables
load_dotenv()

# Configure logging — structured JSON in prod, plain text for dev/tests.
_log_level = logging.INFO if settings.DEBUG else logging.WARNING
_root = logging.getLogger()
for _h in list(_root.handlers):
    _root.removeHandler(_h)
_handler = logging.StreamHandler(sys.stdout)
if settings.LOG_FORMAT == "json":
    from pythonjsonlogger import jsonlogger

    _handler.setFormatter(
        jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    )
else:
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
_root.addHandler(_handler)
_root.setLevel(_log_level)
logger = logging.getLogger(__name__)

# Sentry — optional. Empty DSN = disabled. Missing package = no-op.
if settings.SENTRY_DSN:
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            release=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
        )
    except ImportError:
        logger.warning("sentry-sdk not installed; skipping Sentry init")

# Create database tables.
# TODO: once Alembic is the source of truth in all envs (prod + CI),
# drop this call and rely on `alembic upgrade head` at deploy time.
# Tests still lean on create_all against in-memory SQLite.
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {str(e)}")
    raise

app = FastAPI(
    title="Zippie Payment Platform",
    description="P2P Payment System for Zimbabwe",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Zippie Payment Platform API",
        "version": "2.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from sqlalchemy import text

    from app.db.database import get_db

    # Check database connection
    db_status = "disconnected"
    try:
        db_gen = get_db()
        db = next(db_gen)
        db.execute(text("SELECT 1"))
        db_status = "connected"
        # Close the database session
        try:
            next(db_gen, None)
        except StopIteration:
            pass
    except Exception as e:
        db_status = "disconnected"
        logger.error(f"Database health check failed: {str(e)}")

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "services": {
            "p2p": "operational",
        },
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    import logging

    logger = logging.getLogger(__name__)

    # Log the full error for debugging
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    # Return safe error message
    error_message = str(exc) if settings.DEBUG else "An error occurred"

    # Don't leak sensitive information
    if not settings.DEBUG:
        # In production, sanitize error messages
        if "password" in error_message.lower() or "secret" in error_message.lower():
            error_message = "An error occurred"

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": error_message},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
