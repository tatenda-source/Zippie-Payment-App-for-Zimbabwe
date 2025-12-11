"""
Integration tests for stock endpoints
"""
from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestStocks:
    """Test stock endpoints"""

    @pytest.fixture
    def mock_stock_quote(self):
        """Mock stock quote data"""
        return {
            "symbol": "AAPL",
            "short_name": "Apple Inc.",
            "long_name": "Apple Inc.",
            "price": 150.0,
            "change": 2.5,
            "change_percent": 1.67,
            "volume": 50000000,
            "currency": "USD",
            "exchange": "NASDAQ",
        }

    @patch("app.api.v1.stocks.stock_api_service.get_quote")
    def test_get_stock_quote(
        self, mock_get_quote, authenticated_client, mock_stock_quote
    ):
        """Test getting stock quote"""

        # Create an async mock
        async def mock_quote(symbol):
            return mock_stock_quote

        mock_get_quote.side_effect = mock_quote

        response = authenticated_client.get("/api/v1/stocks/quote/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.0

    @patch("app.api.v1.stocks.stock_api_service.get_quote")
    def test_get_stock_quote_not_found(
        self, mock_get_quote, authenticated_client
    ):
        """Test getting stock quote for nonexistent symbol"""

        async def mock_quote(symbol):
            return None

        mock_get_quote.side_effect = mock_quote

        response = authenticated_client.get("/api/v1/stocks/quote/INVALID")

        assert response.status_code == 404

    @patch("app.api.v1.stocks.stock_api_service.get_historical_data")
    def test_get_historical_data(
        self, mock_get_historical, authenticated_client
    ):
        """Test getting historical stock data"""
        mock_data = [
            {
                "date": "2024-01-01",
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.0,
                "volume": 1000000,
            },
            {
                "date": "2024-01-02",
                "open": 103.0,
                "high": 108.0,
                "low": 102.0,
                "close": 106.0,
                "volume": 1100000,
            },
        ]

        async def mock_historical(symbol, period):
            return mock_data

        mock_get_historical.side_effect = mock_historical

        response = authenticated_client.get(
            "/api/v1/stocks/historical/AAPL?period=1mo"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @patch("app.api.v1.stocks.stock_api_service.get_historical_data")
    @patch("app.api.v1.stocks.ml_predictor_service.predict")
    def test_get_prediction(
        self, mock_predict, mock_get_historical, authenticated_client
    ):
        """Test getting stock prediction"""
        mock_historical_data = [
            {
                "date": "2024-01-01",
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.0,
                "volume": 1000000,
            }
        ] * 20

        async def mock_historical_func(symbol, period):
            return mock_historical_data

        mock_get_historical.side_effect = mock_historical_func

        mock_predict.return_value = {
            "symbol": "AAPL",
            "predicted_price": 155.0,
            "confidence": 75.0,
            "predicted_change": 5.0,
            "predicted_change_percent": 3.33,
            "timeframe": "1d",
            "prediction_date": "2024-01-01T00:00:00",
        }

        response = authenticated_client.get(
            "/api/v1/stocks/predict/AAPL?timeframe=1d"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "predicted_price" in data
        assert "confidence" in data

    @patch("app.api.v1.stocks.stock_api_service.search_stocks")
    def test_search_stocks(self, mock_search, authenticated_client):
        """Test searching for stocks"""
        mock_results = [
            {
                "symbol": "AAPL",
                "short_name": "Apple Inc.",
                "long_name": "Apple Inc.",
                "exchange": "NASDAQ",
            }
        ]

        async def mock_search_func(query):
            return mock_results

        mock_search.side_effect = mock_search_func

        response = authenticated_client.get("/api/v1/stocks/search?q=apple")

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0

    def test_search_stocks_short_query(self, authenticated_client):
        """Test search with query that's too short"""
        response = authenticated_client.get("/api/v1/stocks/search?q=a")

        assert response.status_code == 400
