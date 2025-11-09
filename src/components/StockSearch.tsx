import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent } from './ui/card';
import { ArrowLeft, Search, Star, TrendingUp, TrendingDown } from 'lucide-react';
import { stockApi } from '../services/stockApi';

interface StockSearchProps {
  onBack: () => void;
  onSelectStock: (symbol: string) => void;
  watchlist: string[];
  onAddToWatchlist: (symbol: string) => void;
  onRemoveFromWatchlist: (symbol: string) => void;
}

interface SearchResult {
  symbol: string;
  shortName: string;
  longName: string;
  exchange: string;
}

export function StockSearch({ 
  onBack, 
  onSelectStock, 
  watchlist,
  onAddToWatchlist,
  onRemoveFromWatchlist 
}: StockSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [quotes, setQuotes] = useState<Record<string, any>>({});

  useEffect(() => {
    const searchStocks = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }

      setLoading(true);
      try {
        const searchResults = await stockApi.searchStocks(query);
        setResults(searchResults);

        // Fetch quotes for results
        if (searchResults.length > 0) {
          const symbols = searchResults.map(r => r.symbol);
          const quotesData = await stockApi.getMultipleQuotes(symbols);
          const quotesMap: Record<string, any> = {};
          quotesData.forEach(quote => {
            quotesMap[quote.symbol] = quote;
          });
          setQuotes(quotesMap);
        }
      } catch (error) {
        console.error('Error searching stocks:', error);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(searchStocks, 300);
    return () => clearTimeout(debounce);
  }, [query]);

  const isInWatchlist = (symbol: string) => watchlist.includes(symbol);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatChange = (quote: any) => {
    if (!quote) return null;
    const isPositive = quote.regularMarketChange >= 0;
    return (
      <div className={`flex items-center gap-1 text-xs ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        <span>
          {isPositive ? '+' : ''}{quote.regularMarketChangePercent.toFixed(2)}%
        </span>
      </div>
    );
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-6">
        <div className="flex items-center gap-4 mb-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="text-white hover:bg-white/20"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="text-2xl font-bold">Search Stocks</h1>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            type="text"
            placeholder="Search by symbol or company name..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-10 bg-white text-gray-900 border-0 focus:ring-2 focus:ring-white/50"
          />
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 px-4 py-6 overflow-y-auto">
        {loading && (
          <div className="text-center py-8 text-gray-500">Searching...</div>
        )}

        {!loading && query.length < 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Popular Stocks</h2>
            <div className="grid grid-cols-1 gap-3">
              {['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'].map((symbol) => (
                <Card
                  key={symbol}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => onSelectStock(symbol)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-bold text-lg">{symbol}</h3>
                      </div>
                      <Star
                        className={`w-5 h-5 cursor-pointer ${
                          isInWatchlist(symbol)
                            ? 'fill-yellow-400 text-yellow-400'
                            : 'text-gray-300'
                        }`}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (isInWatchlist(symbol)) {
                            onRemoveFromWatchlist(symbol);
                          } else {
                            onAddToWatchlist(symbol);
                          }
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {!loading && results.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Search Results</h2>
            {results.map((result) => {
              const quote = quotes[result.symbol];
              return (
                <Card
                  key={result.symbol}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => onSelectStock(result.symbol)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-bold text-lg">{result.symbol}</h3>
                          <Star
                            className={`w-4 h-4 cursor-pointer ${
                              isInWatchlist(result.symbol)
                                ? 'fill-yellow-400 text-yellow-400'
                                : 'text-gray-300'
                            }`}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (isInWatchlist(result.symbol)) {
                                onRemoveFromWatchlist(result.symbol);
                              } else {
                                onAddToWatchlist(result.symbol);
                              }
                            }}
                          />
                        </div>
                        <p className="text-sm text-gray-600 mb-1">{result.shortName}</p>
                        <p className="text-xs text-gray-400">{result.exchange}</p>
                        {quote && (
                          <div className="mt-2">
                            <div className="text-lg font-bold">
                              {formatCurrency(quote.regularMarketPrice)}
                            </div>
                            {formatChange(quote)}
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {!loading && query.length >= 2 && results.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No stocks found for "{query}"
          </div>
        )}
      </div>
    </div>
  );
}

