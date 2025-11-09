# Hippie Fintech Platform 🚀

**Integrated P2P Payments + Stock Market Insights**

A comprehensive fintech platform that combines peer-to-peer payments with AI-powered stock market predictions. Send money, track transactions, and get intelligent investment insights all in one app.

## ✨ Features

### 💸 P2P Payments
- User registration and authentication (JWT)
- Multiple account management (USD, ZWL)
- Send money to other users
- Request payments
- Transaction history and filtering
- Real-time balance tracking
- QR code payments (UI ready)

### 📈 Stock Market Insights (InvestIQ)
- Real-time stock quotes (Alpha Vantage + Yahoo Finance)
- Historical stock data with interactive charts
- AI-powered price predictions (ML models)
- Technical indicators (RSI, MACD, Moving Averages)
- Watchlist management
- Stock search functionality
- Popular stocks dashboard
- Confidence scores for predictions

## 🏗️ Architecture

### Full-Stack Application
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **ML**: scikit-learn + TensorFlow (backend predictions)
- **APIs**: Alpha Vantage + Yahoo Finance

### Project Structure
```
hippie-fintech/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # REST API endpoints
│   │   ├── core/           # Configuration
│   │   ├── db/             # Database models
│   │   └── services/       # Business logic
│   └── requirements.txt
├── src/                     # React frontend
│   ├── components/         # UI components
│   ├── services/           # API clients
│   └── App.tsx
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- npm or yarn

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database URL and API keys

# Create database
createdb hippie_db

# Start backend
uvicorn app.main:app --reload --port 8000
```

Backend API: http://localhost:8000
API Docs: http://localhost:8000/api/docs

### 2. Frontend Setup

```bash
# From project root
npm install

# Create .env file
echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env

# Start frontend
npm start
```

Frontend: http://localhost:3000

## 📚 Documentation

- **Quick Start**: [`QUICK_START.md`](./QUICK_START.md) - 5-minute setup guide
- **Integration Guide**: [`INTEGRATION_GUIDE.md`](./INTEGRATION_GUIDE.md) - Detailed integration instructions
- **Project Summary**: [`PROJECT_SUMMARY.md`](./PROJECT_SUMMARY.md) - Complete project overview
- **Backend README**: [`backend/README.md`](./backend/README.md) - Backend API documentation

## 🔑 Key Features

### Authentication
- JWT-based authentication
- Secure password hashing (bcrypt)
- User registration and login
- Protected API routes

### Payments
- Multiple currency support (USD, ZWL)
- Transaction history
- Account management
- Real-time balance updates

### Stock Market
- Real-time quotes from Yahoo Finance
- Historical data visualization
- ML-powered predictions
- Technical analysis
- Watchlist management

## 🛠️ Tech Stack

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- Recharts
- Lucide React

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT Authentication
- scikit-learn (ML)

### APIs
- Yahoo Finance (free, no API key)
- Alpha Vantage (optional, requires API key)

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Stocks
- `GET /api/v1/stocks/quote/{symbol}` - Get stock quote
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

## 🔐 Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/hippie_db
SECRET_KEY=your-secret-key-here
ALPHA_VANTAGE_API_KEY=your-api-key (optional)
YAHOO_FINANCE_ENABLED=true
CORS_ORIGINS=http://localhost:3000
DEBUG=true
```

### Frontend (.env)
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

## 🎯 Roadmap

### Immediate
- [x] Backend API structure
- [x] Database models
- [x] Stock API integration
- [x] ML prediction service
- [ ] Frontend API integration
- [ ] Authentication UI
- [ ] Error handling

### Short-term
- [ ] Real-time stock updates (WebSockets)
- [ ] Caching (Redis)
- [ ] Improved ML models
- [ ] More technical indicators
- [ ] Mobile app (React Native)

### Long-term
- [ ] Micro-investing feature
- [ ] Portfolio tracking
- [ ] AI financial recommendations
- [ ] Push notifications
- [ ] Social features

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

## ⚠️ Disclaimer

**Important:** This application is for educational and informational purposes only. Stock market predictions are not guaranteed and should not be used as the sole basis for investment decisions. Always consult with a qualified financial advisor before making investment decisions.

---

**Built with ❤️ for the fintech community 🚀**

For detailed setup instructions, see [`QUICK_START.md`](./QUICK_START.md)
