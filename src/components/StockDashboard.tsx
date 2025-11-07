import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { 
  Search, 
  TrendingUp, 
  TrendingDown, 
  Star, 
  Activity,
  BarChart3,
  Brain,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import type { WatchlistItem, Screen } from '../App';
import type { StockQuote } from '../types/stock';
import { stockApi } from '../services/stockApi';

interface StockDashboardProps {
  watchlist: WatchlistItem[];
  onNavigate: (screen: Screen, data?: any) => void;
  onAddToWatchlist: (symbol: string) => void;
  onRemoveFromWatchlist: (symbol: string) => void;
}

const POPULAR_STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX'];

export function StockDashboard({ 
  watchlist, 
  onNavigate, 
  onAddToWatchlist,
  onRemoveFromWatchlist 
}: StockDashboardProps) {
  const [popularStocks, setPopularStocks] = useState<StockQuote[]>([]);
  const [watchlistQuotes, setWatchlistQuotes] = useState<StockQuote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [watchlist]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load popular stocks
      const popular = await stockApi.getMultipleQuotes(POPULAR_STOCKS);
      setPopularStocks(popular);

      // Load watchlist stocks
      if (watchlist.length > 0) {
        const symbols = watchlist.map(item => item.symbol);
        const quotes = await stockApi.getMultipleQuotes(symbols);
        setWatchlistQuotes(quotes);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatChange = (change: number, changePercent: number) => {
    const isPositive = change >= 0;
    return (
      <div className={`flex items-center gap-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
        <span className="font-semibold">
          {isPositive ? '+' : ''}{formatCurrency(change)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
        </span>
      </div>
    );
  };

  const isInWatchlist = (symbol: string) => {
    return watchlist.some(item => item.symbol === symbol);
  };

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-6 rounded-b-3xl shadow-lg">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white">AI Stock Predictor</h1>
            <p className="text-blue-100 mt-1">Smart predictions for investors</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onNavigate('search')}
            className="text-white hover:bg-blue-700/50"
          >
            <Search className="w-5 h-5" />
          </Button>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3">
            <div className="text-blue-100 text-xs">Active Stocks</div>
            <div className="text-xl font-bold">{popularStocks.length}</div>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3">
            <div className="text-blue-100 text-xs">Watchlist</div>
            <div className="text-xl font-bold">{watchlist.length}</div>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3">
            <div className="text-blue-100 text-xs">AI Predictions</div>
            <div className="text-xl font-bold">
              <Brain className="w-5 h-5 inline" />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-6">
        <div className="grid grid-cols-2 gap-4 mb-6">
          <Button
            onClick={() => onNavigate('search')}
            className="flex flex-col items-center gap-2 h-24 bg-gradient-to-br from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700"
          >
            <Search className="w-6 h-6" />
            <span>Search Stocks</span>
          </Button>
          <Button
            onClick={() => onNavigate('watchlist')}
            className="flex flex-col items-center gap-2 h-24 bg-gradient-to-br from-purple-500 to-purple-600 text-white hover:from-purple-600 hover:to-purple-700"
          >
            <Star className="w-6 h-6" />
            <span>Watchlist</span>
          </Button>
        </div>

        {/* Watchlist Preview */}
        {watchlistQuotes.length > 0 && (
          <div className="space-y-4 mb-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Star className="w-5 h-5 text-yellow-500" />
                Your Watchlist
              </h2>
              <Button 
                variant="ghost" 
                size="sm" 
                className="text-primary"
                onClick={() => onNavigate('watchlist')}
              >
                View All
              </Button>
            </div>
            <div className="space-y-3">
              {watchlistQuotes.slice(0, 3).map((quote) => (
                <Card 
                  key={quote.symbol} 
                  className="border-0 shadow-md hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => onNavigate('detail', { symbol: quote.symbol })}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-bold text-lg">{quote.symbol}</h3>
                          <Star 
                            className={`w-4 h-4 ${isInWatchlist(quote.symbol) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (isInWatchlist(quote.symbol)) {
                                onRemoveFromWatchlist(quote.symbol);
                              } else {
                                onAddToWatchlist(quote.symbol);
                              }
                            }}
                          />
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{quote.shortName}</p>
                        <div className="text-2xl font-bold">
                          {formatCurrency(quote.regularMarketPrice)}
                        </div>
                      </div>
                      <div className="text-right">
                        {formatChange(quote.regularMarketChange, quote.regularMarketChangePercent)}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-2 text-blue-600"
                          onClick={(e) => {
                            e.stopPropagation();
                            onNavigate('detail', { symbol: quote.symbol });
                          }}
                        >
                          <BarChart3 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Popular Stocks */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-500" />
              Popular Stocks
            </h2>
          </div>
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading stocks...</div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {popularStocks.map((quote) => (
                <Card 
                  key={quote.symbol} 
                  className="border-0 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onNavigate('detail', { symbol: quote.symbol })}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="flex items-center gap-1">
                          <h3 className="font-bold">{quote.symbol}</h3>
                          <Star 
                            className={`w-3 h-3 cursor-pointer ${isInWatchlist(quote.symbol) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (isInWatchlist(quote.symbol)) {
                                onRemoveFromWatchlist(quote.symbol);
                              } else {
                                onAddToWatchlist(quote.symbol);
                              }
                            }}
                          />
                        </div>
                        <p className="text-xs text-gray-500">{quote.shortName}</p>
                      </div>
                    </div>
                    <div className="text-lg font-bold mb-1">
                      {formatCurrency(quote.regularMarketPrice)}
                    </div>
                    <div className="text-xs">
                      {formatChange(quote.regularMarketChange, quote.regularMarketChangePercent)}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

