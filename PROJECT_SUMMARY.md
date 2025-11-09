# Hippie Fintech Platform - Project Summary

## 🎯 Project Overview

**Hippie** is an integrated fintech platform that combines **P2P payments** with **stock market insights**. Users can send money, track transactions, and get AI-powered stock predictions all in one app.

## ✨ Key Features

### P2P Payment Module
- ✅ User registration and JWT authentication
- ✅ Multiple account management (USD, ZWL)
- ✅ Send money to other users
- ✅ Request payments
- ✅ Transaction history and filtering
- ✅ Real-time balance tracking
- ✅ QR code payments (UI ready)

### Stock Market Module (InvestIQ)
- ✅ Real-time stock quotes (Alpha Vantage + Yahoo Finance)
- ✅ Historical stock data
- ✅ AI-powered price predictions (ML models)
- ✅ Technical indicators (RSI, MACD, Moving Averages)
- ✅ Watchlist management
- ✅ Stock search functionality
- ✅ Popular stocks dashboard
- ✅ Confidence scores for predictions

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── app/
│   ├── api/v1/          # REST API endpoints
│   │   ├── auth.py      # Authentication
│   │   ├── stocks.py    # Stock market API
│   │   ├── payments.py  # P2P payments API
│   │   └── watchlists.py # Watchlist management
│   ├── core/            # Core configuration
│   │   ├── config.py    # Settings
│   │   └── security.py  # JWT & password hashing
│   ├── db/              # Database layer
│   │   ├── models.py    # SQLAlchemy models
│   │   ├── schemas.py   # Pydantic schemas
│   │   └── database.py  # DB connection
│   ├── services/        # Business logic
│   │   ├── stock_api.py # Stock data fetching
│   │   └── ml_predictor.py # ML predictions
│   └── main.py          # FastAPI app
└── requirements.txt
```

### Frontend (React + TypeScript)
```
src/
├── components/          # UI components
│   ├── HomeDashboard.tsx
│   ├── SendMoney.tsx
│   ├── StockDashboard.tsx
│   ├── StockDetail.tsx
│   └── ...
├── services/
│   ├── api.ts          # Backend API client
│   ├── stockApi.ts     # Stock API (legacy, can be removed)
│   └── predictionService.ts # ML service (legacy)
└── App.tsx
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **JWT** - Authentication
- **scikit-learn** - ML predictions
- **pandas** - Data processing
- **httpx** - HTTP client for stock APIs

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Lucide React** - Icons

### APIs
- **Alpha Vantage** - Stock data (optional, requires API key)
- **Yahoo Finance** - Stock data (free, no API key)

## 📊 Database Schema

### Users
- id, email, phone, full_name
- hashed_password, is_active, is_verified
- created_at, updated_at

### Accounts
- id, user_id, name, balance
- currency (USD/ZWL), account_type
- color, is_active

### Transactions
- id, user_id, account_id
- transaction_type (sent/received/request)
- amount, currency, recipient, sender
- description, status, payment_method
- fee, metadata

### Watchlists
- id, user_id, symbol
- exchange, target_price, notes
- created_at, updated_at

## 🔐 Authentication Flow

1. User registers with email, phone, password
2. Backend creates user and default account
3. User logs in with email/password
4. Backend returns JWT token
5. Frontend stores token in localStorage
6. All API requests include token in Authorization header

## 📈 Stock Prediction Flow

1. User searches or selects a stock
2. Frontend requests historical data from backend
3. Backend fetches data from Yahoo Finance/Alpha Vantage
4. Backend runs ML model (RandomForest) on historical data
5. Model predicts future price with confidence score
6. Frontend displays prediction with charts and indicators

## 🚀 Getting Started

### Quick Start
```bash
# 1. Setup backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your config
uvicorn app.main:app --reload

# 2. Setup frontend
npm install
echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env
npm start
```

### API Endpoints

**Authentication**
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

**Stocks**
- `GET /api/v1/stocks/quote/{symbol}` - Get quote
- `GET /api/v1/stocks/historical/{symbol}` - Get historical data
- `GET /api/v1/stocks/predict/{symbol}` - Get prediction
- `GET /api/v1/stocks/search?q=apple` - Search stocks
- `GET /api/v1/stocks/popular` - Get popular stocks

**Payments**
- `GET /api/v1/payments/accounts` - Get accounts
- `POST /api/v1/payments/accounts` - Create account
- `GET /api/v1/payments/transactions` - Get transactions
- `POST /api/v1/payments/transactions` - Create transaction
- `GET /api/v1/payments/balance` - Get balance

**Watchlists**
- `GET /api/v1/watchlists` - Get watchlist
- `POST /api/v1/watchlists` - Add to watchlist
- `DELETE /api/v1/watchlists/{id}` - Remove from watchlist

## 📝 Environment Variables

### Backend
```env
DATABASE_URL=postgresql://user:password@localhost:5432/hippie_db
SECRET_KEY=your-secret-key-here
ALPHA_VANTAGE_API_KEY=your-api-key (optional)
YAHOO_FINANCE_ENABLED=true
CORS_ORIGINS=http://localhost:3000
DEBUG=true
```

### Frontend
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## 🧪 Testing

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
npm test
```

## 📦 Deployment

### Backend (Docker)
```bash
cd backend
docker build -t hippie-backend .
docker run -p 8000:8000 hippie-backend
```

### Frontend
```bash
npm run build
# Deploy build/ directory to Vercel/Netlify
```

## 🔄 Migration Path

### Current State
- Frontend uses mock data and localStorage
- Stock predictions use frontend TensorFlow.js
- No backend integration yet

### Target State
- Frontend connects to FastAPI backend
- All data stored in PostgreSQL
- ML predictions run on backend
- JWT authentication enabled
- Real stock data from APIs

### Migration Steps
1. ✅ Backend API created
2. ✅ Database models defined
3. ✅ API client created in frontend
4. ⏳ Update components to use API
5. ⏳ Add authentication UI
6. ⏳ Remove mock data
7. ⏳ Deploy to production

## 🎯 Next Steps

### Immediate
1. Update frontend components to use `src/services/api.ts`
2. Add login/register UI components
3. Replace mock data with API calls
4. Test end-to-end flows

### Short-term
1. Add error handling and loading states
2. Implement real-time stock updates (WebSockets)
3. Add caching for stock data (Redis)
4. Improve ML model accuracy
5. Add more technical indicators

### Long-term
1. Micro-investing feature (invest from wallet)
2. Portfolio tracking
3. AI-driven financial recommendations
4. Push notifications for stock alerts
5. Social features (share predictions)
6. Mobile app (React Native)

## 📚 Documentation

- **Quick Start**: `QUICK_START.md`
- **Integration Guide**: `INTEGRATION_GUIDE.md`
- **Backend README**: `backend/README.md`
- **API Docs**: http://localhost:8000/api/docs (when running)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## 📄 License

MIT License

## 🙏 Acknowledgments

- Alpha Vantage for stock data API
- Yahoo Finance for free stock data
- FastAPI team for the excellent framework
- React team for the amazing UI library

---

**Built with ❤️ for the fintech community**

