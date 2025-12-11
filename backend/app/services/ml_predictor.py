"""
ML Prediction Service for Stock Price Forecasting
Uses scikit-learn and TensorFlow for predictions
"""

import os
import pickle
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


class MLPredictorService:
    """ML service for stock price predictions"""

    def __init__(self):
        self.models = {}  # Cache models per symbol
        self.scalers = {}  # Cache scalers per symbol
        self.model_dir = "app/models"
        os.makedirs(self.model_dir, exist_ok=True)

    def prepare_features(self, historical_data: List[Dict]) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Prepare features from historical data"""
        if len(historical_data) < 10:
            return None

        df = pd.DataFrame(historical_data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # Calculate technical indicators
        df["sma_5"] = df["close"].rolling(window=5).mean()
        df["sma_10"] = df["close"].rolling(window=10).mean()
        df["sma_20"] = df["close"].rolling(window=20).mean()

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df["close"].ewm(span=12, adjust=False).mean()
        exp2 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = exp1 - exp2
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        # Volume indicators
        df["volume_sma"] = df["volume"].rolling(window=10).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]

        # Price changes
        df["price_change"] = df["close"].pct_change()
        df["volatility"] = df["price_change"].rolling(window=10).std()

        # Remove NaN rows
        df = df.dropna()

        if len(df) < 5:
            return None

        # Select features
        features = [
            "close",
            "volume",
            "sma_5",
            "sma_10",
            "sma_20",
            "rsi",
            "macd",
            "macd_signal",
            "volume_ratio",
            "price_change",
            "volatility",
        ]

        X = df[features].values
        return X, df["close"].values

    def _compute_sma(self, df: pd.DataFrame) -> Tuple[float, float]:
        """Compute short and long simple moving averages used by the simple predictor."""
        sma_5 = df["close"].tail(5).mean()
        sma_10 = df["close"].tail(10).mean() if len(df) >= 10 else sma_5
        return sma_5, sma_10

    def train_model(self, symbol: str, historical_data: List[Dict]) -> bool:
        """Train a model for a specific symbol"""
        try:
            feature_data = self.prepare_features(historical_data)
            if feature_data is None:
                return False

            X, y = feature_data

            if len(X) < 10:
                return False

            # Use last 20% for prediction, rest for training
            split_idx = int(len(X) * 0.8)
            X_train, _ = X[:split_idx], X[split_idx:]
            y_train, _ = y[:split_idx], y[split_idx:]

            if len(X_train) < 5:
                return False

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)

            # Train Random Forest model
            model = RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
            )
            model.fit(X_train_scaled, y_train)

            # Cache model and scaler
            self.models[symbol] = model
            self.scalers[symbol] = scaler

            # Save model
            model_path = os.path.join(self.model_dir, f"{symbol}_model.pkl")
            scaler_path = os.path.join(self.model_dir, f"{symbol}_scaler.pkl")

            with open(model_path, "wb") as f:
                pickle.dump(model, f)
            with open(scaler_path, "wb") as f:
                pickle.dump(scaler, f)

            return True
        except Exception as e:
            print(f"Error training model for {symbol}: {str(e)}")
            return False

    def predict(
        self, symbol: str, historical_data: List[Dict], timeframe: str = "1d"
    ) -> Optional[Dict]:
        """Predict future stock price"""
        try:
            # Prepare features
            feature_data = self.prepare_features(historical_data)
            if feature_data is None:
                return self._simple_prediction(historical_data, timeframe)

            X, y = feature_data

            if len(X) < 5:
                return self._simple_prediction(historical_data, timeframe)

            # Get or train model
            if symbol not in self.models:
                if not self.train_model(symbol, historical_data):
                    return self._simple_prediction(historical_data, timeframe)

            model = self.models[symbol]
            scaler = self.scalers[symbol]

            # Use last data point for prediction
            last_features = X[-1:].reshape(1, -1)
            last_features_scaled = scaler.transform(last_features)

            # Predict
            predicted_price = model.predict(last_features_scaled)[0]
            current_price = historical_data[-1]["close"]

            # Calculate confidence based on model performance
            confidence = self._calculate_confidence(model, scaler, X, y)

            # Adjust prediction based on timeframe
            days = self._timeframe_to_days(timeframe)
            if days > 1:
                # Simple extrapolation for longer timeframes
                trend = (predicted_price - current_price) / current_price
                predicted_price = current_price * (1 + trend * days)

            predicted_change = predicted_price - current_price
            predicted_change_percent = (
                predicted_change / current_price
            ) * 100

            return {
                "symbol": symbol,
                "predicted_price": float(predicted_price),
                "confidence": float(confidence),
                "predicted_change": float(predicted_change),
                "predicted_change_percent": float(predicted_change_percent),
                "timeframe": timeframe,
                "prediction_date": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            print(f"Error predicting for {symbol}: {str(e)}")
            return self._simple_prediction(historical_data, timeframe)

    def _simple_prediction(self, historical_data: List[Dict], timeframe: str) -> Dict:
        """Fallback simple prediction using moving average"""
        if len(historical_data) < 5:
            current_price = historical_data[-1]["close"]
            return {
                "predicted_price": current_price,
                "confidence": 50.0,
                "predicted_change": 0.0,
                "predicted_change_percent": 0.0,
                "timeframe": timeframe,
                "prediction_date": datetime.utcnow().isoformat(),
            }

        df = pd.DataFrame(historical_data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # Simple moving average prediction (use helper to avoid duplication)
        sma_5, sma_10 = self._compute_sma(df)

        current_price = df["close"].iloc[-1]
        trend = (sma_5 - sma_10) / sma_10 if sma_10 > 0 else 0

        days = self._timeframe_to_days(timeframe)
        predicted_price = current_price * (1 + trend * days)

        predicted_change = predicted_price - current_price
        predicted_change_percent = (predicted_change / current_price) * 100

        return {
            "predicted_price": float(predicted_price),
            "confidence": 60.0,  # Lower confidence for simple prediction
            "predicted_change": float(predicted_change),
            "predicted_change_percent": float(predicted_change_percent),
            "timeframe": timeframe,
            "prediction_date": datetime.utcnow().isoformat(),
        }

    def _calculate_confidence(
        self, model, scaler, X: np.ndarray, y: np.ndarray
    ) -> float:
        """Calculate prediction confidence"""
        try:
            if len(X) < 10:
                return 50.0

            X_scaled = scaler.transform(X)
            predictions = model.predict(X_scaled)

            # Calculate R² score
            ss_res = np.sum((y - predictions) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Convert R² to confidence (0-100)
            confidence = max(50, min(95, r2 * 100))
            return confidence
        except Exception:
            return 60.0

    def _timeframe_to_days(self, timeframe: str) -> int:
        """Convert timeframe string to days"""
        timeframe_map = {"1d": 1, "1w": 7, "1m": 30, "3m": 90}
        return timeframe_map.get(timeframe, 1)


# Singleton instance
ml_predictor_service = MLPredictorService()
