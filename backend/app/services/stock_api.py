"""
Stock API Service - Integrates with Alpha Vantage and Yahoo Finance
"""

from datetime import datetime
from typing import Dict, List, Optional

import httpx

from app.core.config import settings


class StockAPIService:
    """Service for fetching stock data from various APIs"""

    def __init__(self):
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.yahoo_finance_enabled = settings.YAHOO_FINANCE_ENABLED
        self.base_url_alpha = "https://www.alphavantage.co/query"
        self.base_url_yahoo = (
            "https://query1.finance.yahoo.com/v8/finance/chart"
        )
        # Lazily-created AsyncClient reused across requests to avoid
        # repeatedly creating/closing connections which harms performance.
        self._client = None

    async def _get_client(self):
        """Return a shared AsyncClient instance, creating it if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get current stock quote"""
        try:
            # Try Alpha Vantage first if API key is available
            if self.alpha_vantage_key:
                quote = await self._get_alpha_vantage_quote(symbol)
                if quote:
                    return quote

            # Fallback to Yahoo Finance
            if self.yahoo_finance_enabled:
                return await self._get_yahoo_quote(symbol)

            return None
        except Exception as e:
            print(f"Error fetching quote for {symbol}: {str(e)}")
            return None

    async def _get_alpha_vantage_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote from Alpha Vantage"""
        try:
            client = await self._get_client()
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
            }
            response = await client.get(self.base_url_alpha, params=params)
            data = response.json()

                if "Global Quote" in data:
                    quote = data["Global Quote"]
                    return {
                        "symbol": quote.get("01. symbol"),
                        "short_name": quote.get("01. symbol"),
                        "price": float(quote.get("05. price", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": float(
                            quote.get(
                                "10. change percent", "0%"
                            ).replace("%", "")
                        ),
                        "volume": int(quote.get("06. volume", 0)),
                        "currency": "USD",
                        "exchange": "NASDAQ",
                    }
        except Exception as e:
            print(f"Alpha Vantage error: {str(e)}")

        return None

    async def _get_yahoo_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote from Yahoo Finance (no API key required)"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_yahoo}/{symbol}"
            params = {"interval": "1d", "range": "1d"}
            response = await client.get(url, params=params)
            data = response.json()

                if "chart" in data and "result" in data["chart"]:
                    result = data["chart"]["result"][0]
                    meta = result.get("meta", {})

                    current_price = meta.get("regularMarketPrice", 0)
                    previous_close = meta.get("previousClose", current_price)
                    change = current_price - previous_close
                    change_percent = (
                        (change / previous_close * 100)
                        if previous_close
                        else 0
                    )

                    return {
                        "symbol": meta.get("symbol", symbol),
                        "short_name": meta.get("shortName", symbol),
                        "long_name": meta.get("longName"),
                        "price": current_price,
                        "change": change,
                        "change_percent": change_percent,
                        "volume": meta.get("regularMarketVolume", 0),
                        "market_cap": meta.get("marketCap"),
                        "currency": meta.get("currency", "USD"),
                        "exchange": meta.get("exchange", "NASDAQ"),
                    }
        except Exception as e:
            print(f"Yahoo Finance error: {str(e)}")

        return None

    async def get_historical_data(
        self, symbol: str, period: str = "1mo"
    ) -> List[Dict]:
        """Get historical stock data"""
        try:
            if self.yahoo_finance_enabled:
                return await self._get_yahoo_historical(symbol, period)
            return []
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return []

    async def _get_yahoo_historical(
        self, symbol: str, period: str
    ) -> List[Dict]:
        """Get historical data from Yahoo Finance"""
        try:
            client = await self._get_client()
            url = f"{self.base_url_yahoo}/{symbol}"
            params = {"interval": "1d", "range": period}
            response = await client.get(url, params=params)
            data = response.json()

                if "chart" in data and "result" in data["chart"]:
                    result = data["chart"]["result"][0]
                    timestamps = result.get("timestamp", [])
                    indicators = result.get("indicators", {})
                    quote = indicators.get("quote", [{}])[0]

                    opens = quote.get("open", [])
                    highs = quote.get("high", [])
                    lows = quote.get("low", [])
                    closes = quote.get("close", [])
                    volumes = quote.get("volume", [])

                    historical_data = []
                    for i, ts in enumerate(timestamps):
                        if i < len(closes) and closes[i]:
                            historical_data.append(
                                {
                                    "date": datetime.fromtimestamp(
                                        ts
                                    ).isoformat(),
                                    "open":
                                        opens[i]
                                        if i < len(opens)
                                        else closes[i],
                                    "high":
                                        highs[i]
                                        if i < len(highs)
                                        else closes[i],
                                    "low":
                                        lows[i]
                                        if i < len(lows)
                                        else closes[i],
                                    "close": closes[i],
                                    "volume": (
                                        int(volumes[i])
                                        if i < len(volumes)
                                        else 0
                                    ),
                                }
                            )

                    return historical_data
        except Exception as e:
            print(f"Yahoo Finance historical error: {str(e)}")

        return []

    async def search_stocks(self, query: str) -> List[Dict]:
        """Search for stocks by symbol or company name"""
        try:
            # For now, return mock data or use a search API
            # In production, integrate with a proper stock search API
            client = await self._get_client()
            # Using Yahoo Finance search
            url = "https://query1.finance.yahoo.com/v1/finance/search"
            params = {"q": query, "quotesCount": 10}
            response = await client.get(url, params=params)
            data = response.json()

                results = []
                if "quotes" in data:
                    for quote in data["quotes"]:
                        results.append(
                            {
                                "symbol": quote.get("symbol"),
                                "short_name": quote.get("shortname"),
                                "long_name": quote.get("longname"),
                                "exchange": quote.get("exchange", "NASDAQ"),
                            }
                        )

                return results
        except Exception as e:
            print(f"Error searching stocks: {str(e)}")
            return []

    async def get_multiple_quotes(self, symbols: List[str]) -> List[Dict]:
        """Get quotes for multiple symbols"""
        quotes = []
        for symbol in symbols:
            quote = await self.get_quote(symbol)
            if quote:
                quotes.append(quote)
        return quotes


# Singleton instance
stock_api_service = StockAPIService()
