"""
Hippie Fintech Platform - Main Application
Integrated P2P Payments + Stock Market Insights
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.db.database import Base, engine

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {str(e)}")
    raise

app = FastAPI(
    title="Hippie Fintech Platform",
    description="Integrated P2P Payments + Stock Market Insights",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
        "message": "Hippie Fintech Platform API",
        "version": "1.0.0",
        "status": "healthy",
        "modules": ["P2P Payments", "Stock Market Insights", "InvestIQ"],
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
            "stocks": "operational",
            "ml_predictor": "operational",
        },
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
