# Hippie Fintech Platform - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

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

Backend will be running at: http://localhost:8000
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

Frontend will be running at: http://localhost:3000

### 3. Test the Integration

1. **Register a user** via API:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "phone": "+1234567890",
    "full_name": "Test User",
    "password": "password123"
  }'
```

2. **Login**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"
```

3. **Get stock quote** (requires auth token):
```bash
curl -X GET "http://localhost:8000/api/v1/stocks/quote/AAPL" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📁 Project Structure

```
hippie-fintech/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API routes
│   │   ├── core/           # Core configuration
│   │   ├── db/             # Database models
│   │   └── services/       # Business logic
│   ├── requirements.txt
│   └── README.md
├── src/                     # React frontend
│   ├── components/         # UI components
│   ├── services/           # API clients
│   └── App.tsx
└── README.md
```

## 🔑 Key Features

### P2P Payments
- ✅ User registration and authentication
- ✅ Account management
- ✅ Send money
- ✅ Request payments
- ✅ Transaction history
- ✅ Balance tracking

### Stock Market Insights
- ✅ Real-time stock quotes
- ✅ Historical data
- ✅ AI-powered predictions
- ✅ Watchlist management
- ✅ Stock search
- ✅ Technical indicators

## 🛠️ Development

### Backend Development
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend Development
```bash
npm start
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
npm test
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 🔐 Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/hippie_db
SECRET_KEY=your-secret-key-here
ALPHA_VANTAGE_API_KEY=your-api-key (optional)
YAHOO_FINANCE_ENABLED=true
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## 🐳 Docker Deployment

### Backend
```bash
cd backend
docker build -t hippie-backend .
docker run -p 8000:8000 hippie-backend
```

## 📖 Next Steps

1. **Read Integration Guide**: See `INTEGRATION_GUIDE.md` for detailed integration instructions
2. **Update Frontend**: Migrate components to use backend API (see `src/services/api.ts`)
3. **Add Authentication UI**: Create login/register components
4. **Deploy**: Follow deployment instructions in `INTEGRATION_GUIDE.md`

## 🆘 Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in .env is correct
- Check port 8000 is not in use

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check REACT_APP_API_URL in .env
- Verify CORS_ORIGINS includes http://localhost:3000

### Database errors
- Ensure database exists: `createdb hippie_db`
- Check user has permissions
- Verify DATABASE_URL format

## 📞 Support

For detailed documentation:
- Backend: `backend/README.md`
- Integration: `INTEGRATION_GUIDE.md`
- API Docs: http://localhost:8000/api/docs

---

**Happy Coding! 🚀**
