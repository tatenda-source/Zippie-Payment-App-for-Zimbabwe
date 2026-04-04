# Codebase Cleanup Changelog

**Date:** 2026-04-04
**Goal:** Strip Zippie down to its core — a focused P2P payment system. Remove all non-core features that add complexity without serving the primary use case.

---

## Summary of Changes

### Removed: Stock Market Module (Backend)
- **`backend/app/api/v1/stocks.py`** — Stock quote, historical data, prediction, search, and Yahoo proxy endpoints
- **`backend/app/services/stock_api.py`** — Alpha Vantage + Yahoo Finance API integration service (had syntax errors)
- **`backend/app/services/ml_predictor.py`** — RandomForest ML price prediction service (~266 lines)
- **`backend/tests/integration/test_stocks.py`** — Integration tests for stock endpoints
- **`backend/tests/unit/test_ml_predictor.py`** — Unit tests for ML predictor

### Removed: Watchlist Module (Backend)
- **`backend/app/api/v1/watchlists.py`** — CRUD endpoints for stock watchlists
- **`backend/tests/integration/test_watchlists.py`** — Integration tests for watchlist endpoints

### Removed: Watchlist Database Model
- **`Watchlist` class** from `backend/app/db/models.py` — Stock tracking table with symbol, exchange, target_price, notes
- **`watchlists` relationship** removed from `User` model
- **Watchlist schemas** removed from `backend/app/db/schemas.py` (WatchlistBase, WatchlistCreate, WatchlistResponse)
- **Stock schemas** removed from `backend/app/db/schemas.py` (StockQuote, StockHistoricalData, StockPrediction)

### Removed: Unused Frontend Components
- **`src/components/CurrencyConverter.tsx`** (~159 lines) — Never imported or rendered anywhere
- **`src/components/QRCodeGenerator.tsx`** (~117 lines) — Never imported or rendered anywhere

### Removed: Unused Frontend Services & Types
- **`src/services/currencyService.ts`** (~157 lines) — Only consumed by unused CurrencyConverter
- **`src/types/stock.ts`** (~62 lines) — StockQuote, StockPrediction, WatchlistItem types; zero imports
- **`stocksAPI`** object from `src/services/api.ts` — 6 unused API methods for stock data
- **`watchlistsAPI`** object from `src/services/api.ts` — 4 unused API methods for watchlist CRUD

### Removed: Bloated Dependencies
From `backend/requirements.txt`:
- **`tensorflow==2.15.0`** — Only used by removed ML predictor
- **`scikit-learn==1.3.2`** — Only used by removed ML predictor
- **`pandas==2.2.1`** — Only used by removed ML predictor & stock service
- **`numpy==1.26.2`** — Only used by removed ML predictor
- **`aiohttp==3.9.1`** — Only used by removed stock API service
- **`requests==2.31.0`** — Only used by removed stock API service
- Removed duplicate `httpx` entries (was listed 3 times)

### Updated: Backend Configuration
- **`backend/app/api/v1/__init__.py`** — Removed stock and watchlist router imports/includes
- **`backend/app/main.py`** — Updated app title/description, removed stock/ML references from health check and root endpoint
- **`backend/app/services/__init__.py`** — Kept as empty module init

### Updated: Frontend
- **`src/services/api.ts`** — Cleaned to only export auth + payments APIs

---

## What Was Kept (Core P2P)

### Backend
- Auth API (register, login, me)
- Payments API (accounts CRUD, transactions CRUD, balance)
- User, Account, Transaction database models
- JWT authentication & password hashing
- Auth + payment integration tests
- Security unit tests

### Frontend
- HomeDashboard, SendMoney, RequestPayment, PaymentSuccess, TransactionHistory
- TransactionFilter, ErrorBoundary
- Full Radix UI component library
- Auth + Payments API client
- Navigation, transactions, localStorage hooks
- Currency, date, status, logger utilities

---

## Impact

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Backend Python files | ~15 | ~10 | ~33% |
| Frontend components | 9 | 7 | ~22% |
| Frontend services | 3 | 1 | ~67% |
| Backend dependencies | 25+ | ~18 | ~28% |
| Dead code lines removed | ~1,300+ | 0 | 100% |
| Docker image size (est.) | Large (TensorFlow) | Much smaller | ~60-70% |
