# Stock Market API Integration Guide

This document explains how the stock market APIs are integrated and how to extend the application with additional APIs.

## Current Implementation

### Yahoo Finance API (Primary - Browser Compatible)

The application uses Yahoo Finance's public API endpoints directly from the browser:

- **Search API:** `https://query2.finance.yahoo.com/v1/finance/search`
- **Quote API:** `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}`
- **No API Key Required:** Works out of the box
- **Rate Limits:** None (reasonable usage)
- **CORS:** Supported by Yahoo Finance endpoints

### Implementation Details

The `stockApi.ts` service handles:
- Caching (1-minute TTL)
- Error handling
- Data transformation
- Batch requests

## Adding Additional APIs

### 1. Alpha Vantage API

To add Alpha Vantage support:

1. Get API key from https://www.alphavantage.co/support/#api-key
2. Add to `.env.local`:
   ```env
   REACT_APP_ALPHA_VANTAGE_API_KEY=your_key_here
   ```
3. Extend `stockApi.ts`:
   ```typescript
   async getQuoteAlphaVantage(symbol: string): Promise<any> {
     const apiKey = process.env.REACT_APP_ALPHA_VANTAGE_API_KEY;
     const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${apiKey}`;
     const response = await fetch(url);
     const data = await response.json();
     // Transform and return data
   }
   ```

### 2. Finnhub API

To add Finnhub support:

1. Get API key from https://finnhub.io/register
2. Add to `.env.local`:
   ```env
   REACT_APP_FINNHUB_API_KEY=your_key_here
   ```
3. Extend `stockApi.ts`:
   ```typescript
   async getQuoteFinnhub(symbol: string): Promise<any> {
     const apiKey = process.env.REACT_APP_FINNHUB_API_KEY;
     const url = `https://finnhub.io/api/v1/quote?symbol=${symbol}&token=${apiKey}`;
     const response = await fetch(url);
     const data = await response.json();
     // Transform and return data
   }
   ```

### 3. Polygon.io API

To add Polygon.io support:

1. Get API key from https://polygon.io/
2. Add to `.env.local`:
   ```env
   REACT_APP_POLYGON_API_KEY=your_key_here
   ```
3. Extend `stockApi.ts`:
   ```typescript
   async getQuotePolygon(symbol: string): Promise<any> {
     const apiKey = process.env.REACT_APP_POLYGON_API_KEY;
     const url = `https://api.polygon.io/v2/aggs/ticker/${symbol}/prev?apikey=${apiKey}`;
     const response = await fetch(url);
     const data = await response.json();
     // Transform and return data
   }
   ```

### 4. IEX Cloud API

To add IEX Cloud support:

1. Get API key from https://iexcloud.io/
2. Add to `.env.local`:
   ```env
   REACT_APP_IEX_API_KEY=your_key_here
   ```
3. Extend `stockApi.ts`:
   ```typescript
   async getQuoteIEX(symbol: string): Promise<any> {
     const apiKey = process.env.REACT_APP_IEX_API_KEY;
     const url = `https://cloud.iexapis.com/stable/stock/${symbol}/quote?token=${apiKey}`;
     const response = await fetch(url);
     const data = await response.json();
     // Transform and return data
   }
   ```

## CORS Handling

### Browser-Based APIs

Most modern stock market APIs support CORS and work directly from the browser:
- Yahoo Finance ✅
- Alpha Vantage ✅ (with API key)
- Finnhub ✅ (with API key)
- Polygon.io ✅ (with API key)
- IEX Cloud ✅ (with API key)

### If CORS Issues Occur

If you encounter CORS issues, you have two options:

#### Option 1: Use a CORS Proxy (Development Only)

For development, you can use a CORS proxy:

```typescript
const proxyUrl = 'https://cors-anywhere.herokuapp.com/';
const targetUrl = 'https://api.example.com/endpoint';
const response = await fetch(proxyUrl + targetUrl);
```

**Note:** CORS proxies are not recommended for production.

#### Option 2: Backend Proxy (Recommended for Production)

Create a backend API that proxies requests:

```javascript
// Backend (Node.js/Express example)
app.get('/api/stock/:symbol', async (req, res) => {
  const { symbol } = req.params;
  const response = await fetch(`https://api.example.com/quote/${symbol}`);
  const data = await response.json();
  res.json(data);
});
```

Then call your backend from the frontend:

```typescript
const response = await fetch(`/api/stock/${symbol}`);
const data = await response.json();
```

## API Rate Limits

### Yahoo Finance
- **Limit:** None (reasonable usage)
- **Recommended:** Max 100 requests/minute per user

### Alpha Vantage
- **Free Tier:** 5 calls/minute, 500 calls/day
- **Paid Tier:** Higher limits available

### Finnhub
- **Free Tier:** 60 calls/minute
- **Paid Tier:** Higher limits available

### Polygon.io
- **Free Tier:** Limited
- **Paid Tier:** Higher limits available

### IEX Cloud
- **Free Tier:** Limited
- **Paid Tier:** Higher limits available

## Error Handling

The service includes error handling:

```typescript
try {
  const quote = await stockApi.getQuote(symbol);
  if (!quote) {
    // Handle no data
  }
} catch (error) {
  // Handle error
  console.error('Error fetching quote:', error);
}
```

## Caching Strategy

- **Cache TTL:** 1 minute
- **Cache Key:** Based on symbol and timeframe
- **Cache Storage:** In-memory Map
- **Cache Invalidation:** Automatic after TTL

## Best Practices

1. **Always use caching** to reduce API calls
2. **Handle errors gracefully** with fallbacks
3. **Respect rate limits** with request throttling
4. **Use environment variables** for API keys
5. **Implement retry logic** for failed requests
6. **Monitor API usage** to avoid unexpected costs

## Testing APIs

Test individual APIs:

```typescript
// Test Yahoo Finance
const quote = await stockApi.getQuote('AAPL');
console.log(quote);

// Test search
const results = await stockApi.searchStocks('Apple');
console.log(results);

// Test historical data
const historical = await stockApi.getHistoricalData('AAPL', '1mo');
console.log(historical);
```

## Troubleshooting

### Common Issues

1. **CORS Errors:**
   - Use a backend proxy for production
   - Check API documentation for CORS support

2. **Rate Limit Errors:**
   - Implement request throttling
   - Use caching to reduce API calls
   - Consider upgrading API tier

3. **API Key Errors:**
   - Verify API key is correct
   - Check environment variables are loaded
   - Ensure API key has proper permissions

4. **Data Format Issues:**
   - Check API response format
   - Update data transformation logic
   - Handle missing fields gracefully

## Additional Resources

- [Yahoo Finance API Documentation](https://www.yahoofinanceapi.com/)
- [Alpha Vantage Documentation](https://www.alphavantage.co/documentation/)
- [Finnhub Documentation](https://finnhub.io/docs/api)
- [Polygon.io Documentation](https://polygon.io/docs)
- [IEX Cloud Documentation](https://iexcloud.io/docs/api/)

