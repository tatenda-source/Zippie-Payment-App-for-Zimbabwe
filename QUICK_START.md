# Quick Start Guide

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

This will install all required packages including:
- React and TypeScript
- Recharts for charts
- TensorFlow.js for AI predictions
- Simple Statistics for calculations
- Tailwind CSS for styling

### 2. Start Development Server

```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

### 3. Start Using the App

#### Search for Stocks
1. Click "Search Stocks" on the dashboard
2. Type a stock symbol (e.g., "AAPL", "MSFT", "GOOGL") or company name
3. Select a stock to view details

#### View Stock Details
- View real-time stock prices
- See interactive price charts
- Check AI predictions with confidence scores
- Review technical indicators (RSI, MACD, etc.)

#### Manage Watchlist
- Click the star icon on any stock to add to watchlist
- View your watchlist from the dashboard
- Remove stocks by clicking the X icon

#### View Predictions
- Navigate to any stock's detail page
- View AI predictions in the "AI Predictions" section
- Switch between timeframes (1d, 1w, 1m, 3m)
- Review confidence scores and trend analysis

## Popular Stock Symbols to Try

- **AAPL** - Apple Inc.
- **MSFT** - Microsoft Corporation
- **GOOGL** - Alphabet Inc. (Google)
- **AMZN** - Amazon.com Inc.
- **TSLA** - Tesla Inc.
- **META** - Meta Platforms Inc. (Facebook)
- **NVDA** - NVIDIA Corporation
- **NFLX** - Netflix Inc.

## Features Overview

### 📊 Real-Time Data
- Live stock prices
- Market changes and percentages
- Volume and market cap
- 52-week highs and lows

### 🤖 AI Predictions
- Price predictions for multiple timeframes
- Confidence scores
- Trend analysis (bullish/bearish/neutral)
- Prediction reasoning

### 📈 Technical Analysis
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Moving Averages
- Volatility indicators
- Buy/Sell/Hold signals

### ⭐ Watchlist
- Track favorite stocks
- Quick access from dashboard
- Real-time updates
- Persistent storage (localStorage)

## Troubleshooting

### API Issues

If you encounter CORS errors or API issues:

1. **Check Browser Console** - Look for error messages
2. **Verify Internet Connection** - Stock data requires internet
3. **Try Different Stock** - Some symbols may not be available
4. **Check API Status** - Yahoo Finance may be temporarily unavailable

### Performance Issues

1. **Clear Cache** - The app caches data for 1 minute
2. **Reduce Watchlist Size** - Large watchlists may slow loading
3. **Check Browser** - Use modern browser (Chrome, Firefox, Safari, Edge)

### Build Issues

```bash
# Clean build
npm run clean

# Type check
npm run type-check

# Lint
npm run lint

# Build
npm run build
```

## Next Steps

1. **Add API Keys (Optional)** - See [README.md](./README.md) for API key setup
2. **Customize UI** - Modify components in `src/components/`
3. **Add Features** - Extend services in `src/services/`
4. **Deploy** - See [README.md](./README.md) for deployment options

## Need Help?

- Check [README.md](./README.md) for detailed documentation
- See [API_INTEGRATION.md](./API_INTEGRATION.md) for API integration
- Review [TRANSFORMATION_SUMMARY.md](./TRANSFORMATION_SUMMARY.md) for changes

## Important Notes

⚠️ **Disclaimer:** This application is for educational purposes only. Stock predictions are not guaranteed. Always consult a financial advisor before making investment decisions.

---

**Happy Trading! 📈**

