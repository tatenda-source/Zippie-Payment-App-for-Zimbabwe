/**
 * Stock API Service
 * 
 * Browser-compatible stock market data service
 * Uses multiple data sources with fallbacks
 */

export class StockApiService {
  private static instance: StockApiService;
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private readonly CACHE_TTL = 60000; // 1 minute cache

  private constructor() {}

  static getInstance(): StockApiService {
    if (!StockApiService.instance) {
      StockApiService.instance = new StockApiService();
    }
    return StockApiService.instance;
  }

  private getCached(key: string): any | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.data;
    }
    return null;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  /**
   * Search for stocks by query
   * Uses Yahoo Finance search endpoint
   */
  async searchStocks(query: string): Promise<any[]> {
    try {
      const cacheKey = `search_${query}`;
      const cached = this.getCached(cacheKey);
      if (cached) return cached;

      // Use Yahoo Finance search via public API
      const url = `https://query2.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(query)}&quotesCount=10&newsCount=0`;
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      const results = (data.quotes || [])
        .filter((q: any) => q.quoteType === 'EQUITY' && q.symbol)
        .slice(0, 10)
        .map((q: any) => ({
          symbol: q.symbol,
          shortName: q.shortname || q.longname || q.symbol,
          longName: q.longname || q.shortname || q.symbol,
          exchange: q.exchange || 'UNKNOWN',
        }));

      this.setCache(cacheKey, results);
      return results;
    } catch (error) {
      console.error('Error searching stocks:', error);
      return [];
    }
  }

  /**
   * Get current quote for a stock
   * Uses Yahoo Finance quote endpoint
   */
  async getQuote(symbol: string): Promise<any | null> {
    try {
      const cacheKey = `quote_${symbol}`;
      const cached = this.getCached(cacheKey);
      if (cached) return cached;

      // Use Yahoo Finance quote API
      const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=1d`;
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Quote fetch failed');

      const data = await response.json();
      const result = data.chart?.result?.[0];
      
      if (!result || !result.meta) {
        return null;
      }

      const meta = result.meta;
      const quote = {
        symbol: meta.symbol,
        shortName: meta.shortName || symbol,
        longName: meta.longName || meta.shortName || symbol,
        regularMarketPrice: meta.regularMarketPrice || 0,
        regularMarketChange: meta.regularMarketPrice - (meta.previousClose || meta.regularMarketPrice) || 0,
        regularMarketChangePercent: meta.regularMarketPrice && meta.previousClose
          ? ((meta.regularMarketPrice - meta.previousClose) / meta.previousClose) * 100
          : 0,
        regularMarketPreviousClose: meta.previousClose || 0,
        regularMarketOpen: meta.regularMarketOpen || 0,
        regularMarketDayHigh: meta.regularMarketDayHigh || 0,
        regularMarketDayLow: meta.regularMarketDayLow || 0,
        regularMarketVolume: meta.regularMarketVolume || 0,
        marketCap: meta.marketCap,
        fiftyTwoWeekHigh: meta.fiftyTwoWeekHigh || 0,
        fiftyTwoWeekLow: meta.fiftyTwoWeekLow || 0,
        currency: meta.currency || 'USD',
        exchange: meta.exchangeName || meta.exchange || 'UNKNOWN',
      };

      this.setCache(cacheKey, quote);
      return quote;
    } catch (error) {
      console.error(`Error fetching quote for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get historical data for a stock
   * Uses Yahoo Finance historical data endpoint
   */
  async getHistoricalData(
    symbol: string,
    period: '1d' | '5d' | '1mo' | '3mo' | '6mo' | '1y' | '2y' | '5y' | 'max' = '1mo'
  ): Promise<any[]> {
    try {
      const cacheKey = `historical_${symbol}_${period}`;
      const cached = this.getCached(cacheKey);
      if (cached) return cached;

      const range = period === 'max' ? '10y' : period;
      const interval = this.getInterval(period);
      
      // Use Yahoo Finance chart API
      const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=${interval}&range=${range}`;
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Historical data fetch failed');

      const data = await response.json();
      const result = data.chart?.result?.[0];
      
      if (!result || !result.timestamp || !result.indicators) {
        return [];
      }

      const timestamps = result.timestamp || [];
      const quotes = result.indicators?.quote?.[0] || {};
      const opens = quotes.open || [];
      const highs = quotes.high || [];
      const lows = quotes.low || [];
      const closes = quotes.close || [];
      const volumes = quotes.volume || [];

      const formattedData = timestamps
        .map((timestamp: number, index: number) => {
          const date = new Date(timestamp * 1000);
          return {
            date: date.toISOString().split('T')[0],
            open: opens[index] || 0,
            high: highs[index] || 0,
            low: lows[index] || 0,
            close: closes[index] || 0,
            volume: volumes[index] || 0,
            adjustedClose: closes[index] || 0,
          };
        })
        .filter((item: any) => item.close > 0)
        .reverse(); // Most recent first

      this.setCache(cacheKey, formattedData);
      return formattedData;
    } catch (error) {
      console.error(`Error fetching historical data for ${symbol}:`, error);
      return [];
    }
  }

  /**
   * Get multiple quotes at once
   */
  async getMultipleQuotes(symbols: string[]): Promise<any[]> {
    try {
      // Fetch quotes in parallel with limited concurrency
      const batchSize = 5;
      const quotes: any[] = [];
      
      for (let i = 0; i < symbols.length; i += batchSize) {
        const batch = symbols.slice(i, i + batchSize);
        const batchQuotes = await Promise.all(
          batch.map(symbol => this.getQuote(symbol))
        );
        quotes.push(...batchQuotes.filter(quote => quote !== null));
        
        // Small delay between batches to avoid rate limiting
        if (i + batchSize < symbols.length) {
          await new Promise(resolve => setTimeout(resolve, 200));
        }
      }
      
      return quotes;
    } catch (error) {
      console.error('Error fetching multiple quotes:', error);
      return [];
    }
  }

  private getInterval(period: string): '1d' | '1h' | '5m' | '15m' | '30m' | '1m' {
    if (period === '1d') return '5m';
    if (period === '5d') return '15m';
    if (period === '1mo') return '1d';
    return '1d';
  }
}

export const stockApi = StockApiService.getInstance();
