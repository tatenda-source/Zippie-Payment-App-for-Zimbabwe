"""
Stock Market API endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import httpx

from app.api.v1.auth import get_current_user
from app.db import models
from app.db.database import get_db
from app.db.schemas import StockHistoricalData, StockPrediction, StockQuote
from app.services.ml_predictor import ml_predictor_service
from app.services.stock_api import stock_api_service

router = APIRouter()


@router.get("/quote/{symbol}", response_model=StockQuote)
async def get_stock_quote(
    symbol: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current stock quote"""
    quote_data = await stock_api_service.get_quote(symbol.upper())

    if not quote_data:
        raise HTTPException(
            status_code=404, detail=f"Stock quote not found for symbol: {symbol}"
        )

    return StockQuote(**quote_data)


@router.get("/quote", response_model=List[StockQuote])
async def get_multiple_quotes(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get quotes for multiple stocks"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    quotes = await stock_api_service.get_multiple_quotes(symbol_list)

    return [StockQuote(**quote) for quote in quotes]


@router.get("/historical/{symbol}", response_model=List[StockHistoricalData])
async def get_historical_data(
    symbol: str,
    period: str = Query("1mo", description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get historical stock data"""
    historical_data = await stock_api_service.get_historical_data(
        symbol.upper(), period
    )

    if not historical_data:
        raise HTTPException(
            status_code=404, detail=f"Historical data not found for symbol: {symbol}"
        )

    return [StockHistoricalData(**data) for data in historical_data]


@router.get("/predict/{symbol}", response_model=StockPrediction)
async def predict_stock_price(
    symbol: str,
    timeframe: str = Query("1d", description="Prediction timeframe: 1d, 1w, 1m, 3m"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get stock price prediction"""
    # Validate timeframe
    valid_timeframes = ["1d", "1w", "1m", "3m"]
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}",
        )

    # Get historical data for prediction
    period_map = {"1d": "1mo", "1w": "3mo", "1m": "6mo", "3m": "1y"}
    period = period_map.get(timeframe, "1mo")

    historical_data = await stock_api_service.get_historical_data(
        symbol.upper(), period
    )

    if not historical_data or len(historical_data) < 10:
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient historical data for prediction. Need at least 10 data points.",
        )

    # Get prediction
    prediction = ml_predictor_service.predict(
        symbol.upper(), historical_data, timeframe
    )

    if not prediction:
        raise HTTPException(status_code=500, detail="Failed to generate prediction")

    return StockPrediction(**prediction)


@router.get("/search")
async def search_stocks(
    q: str = Query(..., description="Search query"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search for stocks"""
    if len(q) < 2:
        raise HTTPException(
            status_code=400, detail="Search query must be at least 2 characters"
        )

    results = await stock_api_service.search_stocks(q)
    return {"results": results}


@router.get("/popular")
async def get_popular_stocks(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get popular stocks"""
    popular_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX"]
    quotes = await stock_api_service.get_multiple_quotes(popular_symbols)

    return {"stocks": [StockQuote(**quote) for quote in quotes]}


@router.get("/yahoo-proxy")
async def yahoo_proxy(
    symbol: str,
    interval: str = "1d",
    range: str = "1d",
    current_user: models.User = Depends(get_current_user),
):
    """Proxy for Yahoo Finance API to get around CORS issues"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=f"Error from Yahoo Finance API: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500, detail=f"Error connecting to Yahoo Finance API: {e}"
            )