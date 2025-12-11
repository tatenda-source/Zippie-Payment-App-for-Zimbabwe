"""
API v1 Router
"""

from fastapi import APIRouter

from app.api.v1 import auth, payments, stocks, watchlists

api_router = APIRouter()

# Include routers
api_router.include_router(
    auth.router, prefix="/auth", tags=["Authentication"]
)
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(
    payments.router, prefix="/payments", tags=["Payments"]
)
api_router.include_router(
    watchlists.router, prefix="/watchlists", tags=["Watchlists"]
)
