export interface StockQuote {
  symbol: string;
  shortName: string;
  longName: string;
  regularMarketPrice: number;
  regularMarketChange: number;
  regularMarketChangePercent: number;
  regularMarketPreviousClose: number;
  regularMarketOpen: number;
  regularMarketDayHigh: number;
  regularMarketDayLow: number;
  regularMarketVolume: number;
  marketCap?: number;
  fiftyTwoWeekHigh: number;
  fiftyTwoWeekLow: number;
  currency: string;
  exchange: string;
}

export interface StockHistoricalData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adjustedClose?: number;
}

export interface StockPrediction {
  symbol: string;
  predictedPrice: number;
  confidence: number;
  predictionDate: string;
  timeframe: '1d' | '1w' | '1m' | '3m';
  trend: 'bullish' | 'bearish' | 'neutral';
  reasons: string[];
}

export interface TechnicalIndicator {
  name: string;
  value: number;
  signal: 'buy' | 'sell' | 'hold';
  description: string;
}

export interface StockDetail {
  quote: StockQuote;
  historicalData: StockHistoricalData[];
  predictions: StockPrediction[];
  technicalIndicators: TechnicalIndicator[];
}

export interface WatchlistItem {
  symbol: string;
  addedAt: string;
  targetPrice?: number;
  notes?: string;
}

export type Timeframe = '1d' | '5d' | '1mo' | '3mo' | '6mo' | '1y' | '2y' | '5y' | 'max';
