import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { ArrowLeft, Star, TrendingUp, TrendingDown, BarChart3, X } from 'lucide-react';
import { stockApi } from '../services/stockApi';
import type { WatchlistItem, Screen } from '../App';
import type { StockQuote } from '../types/stock';

interface WatchlistProps {
  watchlist: WatchlistItem[];
  onBack: () => void;
  onNavigate: (screen: Screen, data?: any) => void;
  onRemoveFromWatchlist: (symbol: string) => void;
}

export function Watchlist({ watchlist, onBack, onNavigate, onRemoveFromWatchlist }: WatchlistProps) {
  const [quotes, setQuotes] = useState<Record<string, StockQuote>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWatchlistData();
  }, [watchlist]);

  const loadWatchlistData = async () => {
    if (watchlist.length === 0) {
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const symbols = watchlist.map(item => item.symbol);
      const quotesData = await stockApi.getMultipleQuotes(symbols);
      const quotesMap: Record<string, StockQuote> = {};
      quotesData.forEach(quote => {
        quotesMap[quote.symbol] = quote;
      });
      setQuotes(quotesMap);
    } catch (error) {
      console.error('Error loading watchlist data:', error);
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

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-6">
        <div className="flex items-center gap-4 mb-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="text-white hover:bg-white/20"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Star className="w-6 h-6 fill-yellow-400 text-yellow-400" />
              Watchlist
            </h1>
            <p className="text-purple-100 text-sm">{watchlist.length} stocks</p>
          </div>
        </div>
      </div>

      {/* Watchlist Items */}
      <div className="flex-1 px-4 py-6 overflow-y-auto">
        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading watchlist...</div>
        ) : watchlist.length === 0 ? (
          <div className="text-center py-12">
            <Star className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-600 mb-2">Your watchlist is empty</h2>
            <p className="text-gray-500 mb-6">Start adding stocks to track their performance</p>
            <Button onClick={() => onNavigate('stock-search')}>Search Stocks</Button>
          </div>
        ) : (
          <div className="space-y-4">
            {watchlist.map((item) => {
              const quote = quotes[item.symbol];
              return (
                <Card
                  key={item.symbol}
                  className="border-0 shadow-md hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => onNavigate('stock-detail', { symbol: item.symbol })}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-bold text-xl">{item.symbol}</h3>
                          <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                        </div>
                        {quote && (
                          <>
                            <p className="text-sm text-gray-600 mb-2">{quote.shortName}</p>
                            <div className="text-2xl font-bold mb-2">
                              {formatCurrency(quote.regularMarketPrice)}
                            </div>
                            {formatChange(quote.regularMarketChange, quote.regularMarketChangePercent)}
                            {item.targetPrice && (
                              <div className="text-xs text-gray-500 mt-2">
                                Target: {formatCurrency(item.targetPrice)}
                              </div>
                            )}
                          </>
                        )}
                        {!quote && (
                          <p className="text-sm text-gray-500">Loading quote...</p>
                        )}
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-blue-600 hover:text-blue-700"
                          onClick={(e) => {
                            e.stopPropagation();
                            onNavigate('stock-detail', { symbol: item.symbol });
                          }}
                        >
                          <BarChart3 className="w-5 h-5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                          onClick={(e) => {
                            e.stopPropagation();
                            onRemoveFromWatchlist(item.symbol);
                          }}
                        >
                          <X className="w-5 h-5" />
                        </Button>
                      </div>
                    </div>
                    {item.notes && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs text-gray-600">{item.notes}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

