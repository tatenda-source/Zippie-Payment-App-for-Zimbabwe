# AI Stock Market Predictor 📈

A modern, AI-powered stock market prediction application built with React and TypeScript. Features real-time stock data, AI-powered price predictions, technical indicators, and comprehensive market analysis tools for investors.

## ✨ Features

- 📊 **Real-Time Stock Data** - Get live quotes and market data
- 🤖 **AI-Powered Predictions** - Machine learning models predict future stock prices
- 📈 **Interactive Charts** - Beautiful charts with multiple timeframes
- 🔍 **Stock Search** - Search and discover stocks by symbol or company name
- ⭐ **Watchlist** - Track your favorite stocks
- 📉 **Technical Indicators** - RSI, MACD, Moving Averages, and more
- 🎯 **Trend Analysis** - Bullish/Bearish/Neutral predictions with confidence scores
- 📱 **Mobile-First** - Optimized for mobile devices

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ 
- npm or yarn

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-stock-predictor

# Install dependencies
npm install

# Start development server
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

## 📊 Stock Market APIs

This application uses multiple stock market APIs to provide comprehensive market data:

### Primary API: Yahoo Finance (No API Key Required)
- **Implementation:** Direct browser fetch calls to Yahoo Finance public endpoints
- **Features:** Real-time quotes, historical data, stock search
- **Rate Limits:** None (reasonable usage)
- **CORS:** ✅ Supported - Works directly in browser
- **Status:** ✅ Active - Works out of the box
- **Endpoints:**
  - Search: `https://query2.finance.yahoo.com/v1/finance/search`
  - Quote: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}`

### Optional APIs (For Extended Features)

#### 1. Alpha Vantage API
- **Website:** https://www.alphavantage.co/
- **Free Tier:** 5 API calls/minute, 500 calls/day
- **Features:** Real-time and historical data, technical indicators
- **Get API Key:** https://www.alphavantage.co/support/#api-key
- **Environment Variable:** `REACT_APP_ALPHA_VANTAGE_API_KEY`

#### 2. Finnhub API
- **Website:** https://finnhub.io/
- **Free Tier:** 60 calls/minute
- **Features:** Real-time quotes, company news, financials
- **Get API Key:** https://finnhub.io/register
- **Environment Variable:** `REACT_APP_FINNHUB_API_KEY`

#### 3. Polygon.io API
- **Website:** https://polygon.io/
- **Free Tier:** Available with registration
- **Features:** Real-time and historical market data
- **Get API Key:** https://polygon.io/
- **Environment Variable:** `REACT_APP_POLYGON_API_KEY`

#### 4. IEX Cloud API
- **Website:** https://iexcloud.io/
- **Free Tier:** Available with registration
- **Features:** Real-time quotes, market data, financials
- **Get API Key:** https://iexcloud.io/
- **Environment Variable:** `REACT_APP_IEX_API_KEY`

### Adding API Keys (Optional)

Create a `.env.local` file in the root directory:

```env
# Optional API keys for extended features
REACT_APP_ALPHA_VANTAGE_API_KEY=your_key_here
REACT_APP_FINNHUB_API_KEY=your_key_here
REACT_APP_POLYGON_API_KEY=your_key_here
REACT_APP_IEX_API_KEY=your_key_here
```

**Note:** The app works perfectly without API keys using Yahoo Finance. API keys are only needed for additional features or higher rate limits.

**For detailed API integration instructions, see [API_INTEGRATION.md](./API_INTEGRATION.md)**

## 🤖 AI Prediction Features

### Machine Learning Models
- **TensorFlow.js** - Client-side ML predictions
- **Linear Regression** - Trend-based predictions
- **Moving Average Analysis** - Technical trend predictions
- **Time Series Analysis** - Historical pattern recognition

### Technical Indicators
- **RSI (Relative Strength Index)** - Overbought/Oversold signals
- **MACD (Moving Average Convergence Divergence)** - Momentum analysis
- **SMA (Simple Moving Averages)** - Trend identification
- **Volatility Analysis** - Risk assessment

### Prediction Timeframes
- **1 Day** - Short-term predictions
- **1 Week** - Weekly forecasts
- **1 Month** - Monthly projections
- **3 Months** - Quarterly outlook

## 🛠️ Available Scripts

```bash
# Development
npm start                 # Start development server
npm run type-check        # TypeScript type checking
npm run lint              # ESLint code quality check
npm run lint:fix          # Auto-fix ESLint issues

# Production
npm run build             # Production build
npm run build:prod        # Production build with NODE_ENV=production
npm run preview           # Preview production build locally
npm run analyze           # Analyze bundle size

# Maintenance
npm run clean             # Clean build artifacts and cache
npm run prebuild          # Pre-build checks (clean + type-check + lint)
```

## 📁 Project Structure

```
src/
├── components/           # React components
│   ├── ui/              # Reusable UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── StockDashboard.tsx    # Main dashboard
│   ├── StockSearch.tsx       # Stock search component
│   ├── StockDetail.tsx       # Stock detail with charts
│   ├── Watchlist.tsx         # Watchlist management
│   └── ErrorBoundary.tsx     # Error handling
├── services/            # Business logic
│   ├── stockApi.ts          # Stock data API service
│   └── predictionService.ts # AI prediction service
├── types/               # TypeScript types
│   └── stock.ts            # Stock-related types
├── App.tsx              # Main application component
├── index.tsx            # Application entry point
└── index.css            # Global styles
```

## 🎨 Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Accessible component primitives
- **Lucide React** - Beautiful icons
- **Recharts** - Interactive charts
- **TensorFlow.js** - Machine learning
- **Yahoo Finance API** - Stock market data
- **Simple Statistics** - Statistical calculations
- **Date-fns** - Date formatting

## 🔧 Configuration

### Environment Variables

Create `.env.local` for local development (optional):

```env
# Stock Market API Keys (Optional)
REACT_APP_ALPHA_VANTAGE_API_KEY=your_key
REACT_APP_FINNHUB_API_KEY=your_key
REACT_APP_POLYGON_API_KEY=your_key
REACT_APP_IEX_API_KEY=your_key
```

### Tailwind CSS

The project uses Tailwind CSS for styling. Configuration is in `tailwind.config.js`.

### TypeScript

Strict TypeScript configuration in `tsconfig.json` with:
- Strict type checking
- No unused variables
- No implicit returns
- Override modifiers required

## 🚀 Deployment

### Static Hosting (Recommended)

```bash
npm run build
# Deploy the 'build' folder to your hosting service
```

**Recommended Platforms:**
- Vercel
- Netlify  
- AWS S3 + CloudFront
- GitHub Pages

### Docker

```bash
# Build Docker image
docker build -t ai-stock-predictor .

# Run container
docker run -p 3000:80 ai-stock-predictor
```

## 📊 Performance

- **Bundle Size:** Optimized with code splitting
- **Build Time:** Optimized with pre-build checks
- **TypeScript:** Strict mode enabled
- **Code Quality:** ESLint compliant
- **Data Caching:** 1-minute cache for API calls

## 🔒 Security

- Error boundaries for graceful error handling
- Type-safe development with TypeScript
- Secure environment variable handling
- Production-ready security configurations
- API key protection (client-side only)

## 📱 Mobile Optimization

- Responsive design for all screen sizes
- Touch-friendly interface
- Mobile-first approach
- PWA-ready structure

## 🌐 Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers
- Progressive enhancement
- Graceful degradation

## 🎯 Usage Examples

### Searching for Stocks
1. Click "Search Stocks" on the dashboard
2. Type a stock symbol (e.g., "AAPL") or company name
3. Select a stock to view details

### Viewing Predictions
1. Navigate to a stock's detail page
2. View AI predictions in the "AI Predictions" section
3. Switch between timeframes (1d, 1w, 1m, 3m)
4. Review confidence scores and trend analysis

### Managing Watchlist
1. Click the star icon on any stock to add to watchlist
2. View your watchlist from the dashboard
3. Remove stocks by clicking the X icon

### Analyzing Technical Indicators
1. View technical indicators on stock detail pages
2. Review RSI, MACD, and Moving Average signals
3. Check buy/sell/hold recommendations

## ⚠️ Disclaimer

**Important:** This application is for educational and informational purposes only. Stock market predictions are not guaranteed and should not be used as the sole basis for investment decisions. Always consult with a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the [Production Deployment Guide](./PRODUCTION_DEPLOYMENT.md)
- Review the code documentation
- Open an issue for bugs or feature requests

---

**Built with ❤️ for Investors 📈**
