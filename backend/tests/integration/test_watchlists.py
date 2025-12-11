"""
Integration tests for watchlist endpoints
"""
import pytest


@pytest.mark.integration
class TestWatchlists:
    """Test watchlist endpoints"""

    def test_get_watchlist(self, authenticated_client):
        """Test getting user watchlist"""
        response = authenticated_client.get("/api/v1/watchlists")

        assert response.status_code == 200
        watchlist = response.json()
        assert isinstance(watchlist, list)

    def test_add_to_watchlist(self, authenticated_client):
        """Test adding stock to watchlist"""
        watchlist_data = {
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "target_price": 150.0,
            "notes": "Watch for buy opportunity",
        }

        response = authenticated_client.post(
            "/api/v1/watchlists", json=watchlist_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["exchange"] == "NASDAQ"
        assert data["target_price"] == 150.0

    def test_add_duplicate_to_watchlist(self, authenticated_client):
        """Test adding duplicate stock to watchlist"""
        watchlist_data = {"symbol": "AAPL", "exchange": "NASDAQ"}

        # Add first time
        response1 = authenticated_client.post(
            "/api/v1/watchlists", json=watchlist_data
        )
        assert response1.status_code == 200

        # Try to add again
        response2 = authenticated_client.post(
            "/api/v1/watchlists", json=watchlist_data
        )
        assert response2.status_code == 400
        assert "already" in response2.json()["detail"].lower()

    def test_remove_from_watchlist(self, authenticated_client):
        """Test removing stock from watchlist"""
        # Add to watchlist first
        watchlist_data = {"symbol": "MSFT", "exchange": "NASDAQ"}
        add_response = authenticated_client.post(
            "/api/v1/watchlists", json=watchlist_data
        )
        watchlist_id = add_response.json()["id"]

        # Remove from watchlist
        response = authenticated_client.delete(
            f"/api/v1/watchlists/{watchlist_id}"
        )

        assert response.status_code == 200
        assert "message" in response.json()

    def test_remove_from_watchlist_by_symbol(self, authenticated_client):
        """Test removing stock from watchlist by symbol"""
        # Add to watchlist first
        watchlist_data = {"symbol": "GOOGL", "exchange": "NASDAQ"}
        authenticated_client.post("/api/v1/watchlists", json=watchlist_data)

        # Remove by symbol
        response = authenticated_client.delete(
            "/api/v1/watchlists/symbol/GOOGL"
        )

        assert response.status_code == 200
        assert "message" in response.json()

    def test_remove_nonexistent_watchlist_item(self, authenticated_client):
        """Test removing nonexistent watchlist item"""
        response = authenticated_client.delete("/api/v1/watchlists/99999")

        assert response.status_code == 404
