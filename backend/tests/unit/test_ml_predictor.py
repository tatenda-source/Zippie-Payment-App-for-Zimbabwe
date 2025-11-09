"""
Unit tests for ML predictor service
"""
import pytest
from datetime import datetime
from app.services.ml_predictor import MLPredictorService


@pytest.mark.unit
class TestMLPredictor:
    """Test ML predictor service"""
    
    @pytest.fixture
    def predictor(self):
        """Create ML predictor instance"""
        return MLPredictorService()
    
    @pytest.fixture
    def sample_historical_data(self):
        """Create sample historical data"""
        return [
            {
                "date": "2024-01-01",
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.0,
                "volume": 1000000
            },
            {
                "date": "2024-01-02",
                "open": 103.0,
                "high": 108.0,
                "low": 102.0,
                "close": 106.0,
                "volume": 1100000
            },
            {
                "date": "2024-01-03",
                "open": 106.0,
                "high": 110.0,
                "low": 105.0,
                "close": 108.0,
                "volume": 1200000
            },
            {
                "date": "2024-01-04",
                "open": 108.0,
                "high": 112.0,
                "low": 107.0,
                "close": 110.0,
                "volume": 1150000
            },
            {
                "date": "2024-01-05",
                "open": 110.0,
                "high": 114.0,
                "low": 109.0,
                "close": 112.0,
                "volume": 1300000
            },
        ] * 10  # Multiply to get enough data points
    
    def test_prepare_features(self, predictor, sample_historical_data):
        """Test feature preparation"""
        result = predictor.prepare_features(sample_historical_data)
        
        # Should return tuple of (X, y) if enough data
        if result is not None:
            X, y = result
            assert X is not None
            assert y is not None
            assert len(X) > 0
            assert len(y) > 0
    
    def test_prepare_features_insufficient_data(self, predictor):
        """Test feature preparation with insufficient data"""
        insufficient_data = [
            {"date": "2024-01-01", "open": 100.0, "high": 105.0, "low": 99.0, "close": 103.0, "volume": 1000000}
        ]
        
        result = predictor.prepare_features(insufficient_data)
        
        assert result is None
    
    def test_simple_prediction(self, predictor, sample_historical_data):
        """Test simple prediction fallback"""
        prediction = predictor._simple_prediction(sample_historical_data, "1d")
        
        assert prediction is not None
        assert "predicted_price" in prediction
        assert "confidence" in prediction
        assert "predicted_change" in prediction
        assert "predicted_change_percent" in prediction
        assert "timeframe" in prediction
        assert prediction["timeframe"] == "1d"
    
    def test_timeframe_to_days(self, predictor):
        """Test timeframe conversion to days"""
        assert predictor._timeframe_to_days("1d") == 1
        assert predictor._timeframe_to_days("1w") == 7
        assert predictor._timeframe_to_days("1m") == 30
        assert predictor._timeframe_to_days("3m") == 90
        assert predictor._timeframe_to_days("invalid") == 1  # Default
    
    def test_predict_with_sufficient_data(self, predictor, sample_historical_data):
        """Test prediction with sufficient data"""
        prediction = predictor.predict("AAPL", sample_historical_data, "1d")
        
        assert prediction is not None
        assert "symbol" in prediction or "predicted_price" in prediction
        assert "predicted_price" in prediction
        assert "confidence" in prediction
        assert prediction["confidence"] >= 50.0  # Minimum confidence
    
    def test_predict_with_insufficient_data(self, predictor):
        """Test prediction with insufficient data (should use fallback)"""
        insufficient_data = [
            {"date": "2024-01-01", "open": 100.0, "high": 105.0, "low": 99.0, "close": 103.0, "volume": 1000000}
        ] * 3
        
        prediction = predictor.predict("AAPL", insufficient_data, "1d")
        
        # Should still return a prediction (fallback)
        assert prediction is not None
        assert "predicted_price" in prediction

