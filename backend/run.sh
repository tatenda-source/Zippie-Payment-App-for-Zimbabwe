#!/bin/bash

# Hippie Fintech Platform - Backend Startup Script

echo "🚀 Starting Hippie Fintech Platform Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration before running!"
    exit 1
fi

# Check if database exists
echo "🗄️  Checking database connection..."
python -c "from app.core.config import settings; from sqlalchemy import create_engine; engine = create_engine(settings.DATABASE_URL); engine.connect()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Database connection failed. Please check your DATABASE_URL in .env"
    exit 1
fi

# Start server
echo "🌟 Starting FastAPI server..."
echo "📚 API Documentation: http://localhost:8000/api/docs"
echo "🔗 API Base URL: http://localhost:8000/api/v1"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

