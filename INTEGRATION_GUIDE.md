# Hippie Fintech Platform - Integration Guide

## Overview

This guide explains how to integrate the backend API with the frontend React application.

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   React App     │────────▶│   FastAPI       │
│   (Frontend)    │◀────────│   (Backend)     │
│   Port 3000     │         │   Port 8000     │
└─────────────────┘         └─────────────────┘
                                      │
                                      ▼
                              ┌─────────────────┐
                              │   PostgreSQL    │
                              │   (Database)    │
                              └─────────────────┘
```

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations (if using Alembic)
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
# Navigate to project root
cd ..

# Install dependencies (if not already done)
npm install

# Create .env file in root directory
echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env

# Start frontend
npm start
```

### 3. Database Setup

```bash
# Install PostgreSQL (if not installed)
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql

# Create database
createdb hippie_db

# Update DATABASE_URL in backend/.env
DATABASE_URL=postgresql://username:password@localhost:5432/hippie_db
```

## API Integration

### Authentication Flow

1. **Register User**
```typescript
import { authAPI } from './services/api';

const user = await authAPI.register({
  email: 'user@example.com',
  phone: '+1234567890',
  full_name: 'John Doe',
  password: 'password123'
});
```

2. **Login**
```typescript
const { access_token } = await authAPI.login('user@example.com', 'password123');
// Token is automatically stored in localStorage
```

3. **Get Current User**
```typescript
const user = await authAPI.getCurrentUser();
```

### Stock Market Integration

```typescript
import { stocksAPI } from './services/api';

// Get stock quote
const quote = await stocksAPI.getQuote('AAPL');

// Get multiple quotes
const quotes = await stocksAPI.getMultipleQuotes(['AAPL', 'MSFT', 'GOOGL']);

// Get historical data
const historical = await stocksAPI.getHistoricalData('AAPL', '1mo');

// Get prediction
const prediction = await stocksAPI.getPrediction('AAPL', '1d');

// Search stocks
const results = await stocksAPI.searchStocks('apple');
```

### Payments Integration

```typescript
import { paymentsAPI } from './services/api';

// Get accounts
const accounts = await paymentsAPI.getAccounts();

// Create account
const account = await paymentsAPI.createAccount({
  name: 'Savings',
  currency: 'USD',
  account_type: 'savings'
});

// Get transactions
const transactions = await paymentsAPI.getTransactions(50);

// Create transaction
const transaction = await paymentsAPI.createTransaction({
  transaction_type: 'sent',
  amount: 100.00,
  currency: 'USD',
  recipient: 'John Doe',
  description: 'Payment for services'
});

// Get balance
const balance = await paymentsAPI.getBalance();
```

### Watchlist Integration

```typescript
import { watchlistsAPI } from './services/api';

// Get watchlist
const watchlist = await watchlistsAPI.getWatchlist();

// Add to watchlist
const item = await watchlistsAPI.addToWatchlist({
  symbol: 'AAPL',
  exchange: 'NASDAQ',
  target_price: 150.00
});

// Remove from watchlist
await watchlistsAPI.removeFromWatchlist(item.id);
// Or by symbol
await watchlistsAPI.removeFromWatchlistBySymbol('AAPL');
```

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/hippie_db
SECRET_KEY=your-secret-key-here
ALPHA_VANTAGE_API_KEY=your-api-key-here
YAHOO_FINANCE_ENABLED=true
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
DEBUG=true
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Updating Frontend Components

### Example: Update HomeDashboard to use API

```typescript
import { useEffect, useState } from 'react';
import { paymentsAPI } from '../services/api';

export function HomeDashboard() {
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accountsData, transactionsData] = await Promise.all([
        paymentsAPI.getAccounts(),
        paymentsAPI.getTransactions(10)
      ]);
      setAccounts(accountsData);
      setTransactions(transactionsData);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  // ... rest of component
}
```

### Example: Update StockDashboard to use API

```typescript
import { stocksAPI, watchlistsAPI } from '../services/api';

export function StockDashboard() {
  const [quotes, setQuotes] = useState([]);
  const [watchlist, setWatchlist] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [popularStocks, watchlistData] = await Promise.all([
        stocksAPI.getPopularStocks(),
        watchlistsAPI.getWatchlist()
      ]);
      setQuotes(popularStocks.stocks);
      setWatchlist(watchlistData);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  // ... rest of component
}
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
npm test
```

## Deployment

### Backend Deployment

1. **Docker** (Recommended)
```bash
cd backend
docker build -t hippie-backend .
docker run -p 8000:8000 hippie-backend
```

2. **Heroku**
```bash
heroku create hippie-backend
heroku addons:create heroku-postgresql
git push heroku main
```

### Frontend Deployment

1. **Build**
```bash
npm run build
```

2. **Deploy to Vercel/Netlify**
```bash
# Vercel
vercel deploy

# Netlify
netlify deploy --prod
```

## Troubleshooting

### CORS Issues
- Ensure `CORS_ORIGINS` in backend `.env` includes your frontend URL
- Check that backend is running on port 8000
- Verify frontend is using correct `REACT_APP_API_URL`

### Authentication Issues
- Verify token is being stored in localStorage
- Check that token is included in API requests
- Ensure backend SECRET_KEY is set correctly

### Database Issues
- Verify PostgreSQL is running
- Check DATABASE_URL is correct
- Ensure database exists: `createdb hippie_db`

### Stock API Issues
- Verify ALPHA_VANTAGE_API_KEY is set (optional, falls back to Yahoo Finance)
- Check network connectivity
- Verify stock symbols are valid

## Next Steps

1. **Add Authentication UI** - Create login/register components
2. **Update Components** - Migrate all components to use API
3. **Add Error Handling** - Implement proper error handling and user feedback
4. **Add Loading States** - Show loading indicators during API calls
5. **Add Caching** - Implement caching for stock data
6. **Add Real-time Updates** - Use WebSockets for real-time stock updates

## Support

For issues or questions:
1. Check API documentation: http://localhost:8000/api/docs
2. Review backend logs
3. Check browser console for frontend errors
4. Verify environment variables are set correctly

