# Hippie Fintech Platform - Backend API

Integrated P2P Payments + Stock Market Insights Backend

## Tech Stack

- **FastAPI** - Modern, fast web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **JWT** - Authentication
- **scikit-learn** - ML predictions
- **Alpha Vantage / Yahoo Finance** - Stock data

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Update the following:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Generate with `openssl rand -hex 32`
- `ALPHA_VANTAGE_API_KEY` - Get from https://www.alphavantage.co/support/#api-key

### 3. Setup Database

```bash
# Create database
createdb hippie_db

# Run migrations (if using Alembic)
alembic upgrade head
```

Or the app will create tables automatically on first run.

### 4. Run Server

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Stocks
- `GET /api/v1/stocks/quote/{symbol}` - Get stock quote
- `GET /api/v1/stocks/quote?symbols=AAPL,MSFT` - Get multiple quotes
- `GET /api/v1/stocks/historical/{symbol}` - Get historical data
- `GET /api/v1/stocks/predict/{symbol}` - Get prediction
- `GET /api/v1/stocks/search?q=apple` - Search stocks
- `GET /api/v1/stocks/popular` - Get popular stocks

### Payments
- `GET /api/v1/payments/accounts` - Get accounts
- `POST /api/v1/payments/accounts` - Create account
- `GET /api/v1/payments/transactions` - Get transactions
- `POST /api/v1/payments/transactions` - Create transaction
- `GET /api/v1/payments/balance` - Get balance

### Watchlists
- `GET /api/v1/watchlists` - Get watchlist
- `POST /api/v1/watchlists` - Add to watchlist
- `DELETE /api/v1/watchlists/{id}` - Remove from watchlist

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── stocks.py
│   │       ├── payments.py
│   │       └── watchlists.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── stock_api.py
│   │   └── ml_predictor.py
│   └── main.py
├── requirements.txt
└── README.md
```

## Deployment

### Docker

```bash
docker build -t hippie-backend .
docker run -p 8000:8000 hippie-backend
```

### Environment Variables

Required:
- `DATABASE_URL`
- `SECRET_KEY`
- `ALPHA_VANTAGE_API_KEY` (optional, falls back to Yahoo Finance)

Optional:
- `REDIS_URL` - For caching
- `DEBUG` - Enable debug mode
- `CORS_ORIGINS` - Allowed origins

