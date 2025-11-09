import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { ArrowLeft, Star, TrendingUp, TrendingDown, Brain, BarChart3, Activity } from 'lucide-react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { stockApi } from '../services/stockApi';
import { predictionService } from '../services/predictionService';
import type { StockQuote, StockHistoricalData, StockPrediction, TechnicalIndicator, Timeframe } from '../types/stock';
import { format } from 'date-fns';

interface StockDetailProps {
  symbol: string;
  onBack: () => void;
  watchlist: string[];
  onAddToWatchlist: (symbol: string) => void;
  onRemoveFromWatchlist: (symbol: string) => void;
}

export function StockDetail({ 
  symbol, 
  onBack, 
  watchlist,
  onAddToWatchlist,
  onRemoveFromWatchlist 
}: StockDetailProps) {
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [historicalData, setHistoricalData] = useState<StockHistoricalData[]>([]);
  const [predictions, setPredictions] = useState<StockPrediction[]>([]);
  const [technicalIndicators, setTechnicalIndicators] = useState<TechnicalIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<Timeframe>('1mo');
  const [selectedPredictionTimeframe, setSelectedPredictionTimeframe] = useState<'1d' | '1w' | '1m' | '3m'>('1d');

  useEffect(() => {
    loadStockData();
  }, [symbol, timeframe]);

  const loadStockData = async () => {
    setLoading(true);
    try {
      // Load quote
      const quoteData = await stockApi.getQuote(symbol);
      if (quoteData) {
        setQuote(quoteData);
      }

      // Load historical data
      const historical = await stockApi.getHistoricalData(symbol, timeframe);
      setHistoricalData(historical);

      // Calculate technical indicators
      if (historical.length > 0) {
        const indicators = predictionService.calculateTechnicalIndicators(historical);
        setTechnicalIndicators(indicators);
      }

      // Generate predictions
      if (historical.length > 0) {
        try {
          const prediction = await predictionService.predictPrice(
            symbol,
            historical,
            selectedPredictionTimeframe
          );
          setPredictions([prediction]);
        } catch (error) {
          console.error('Error generating prediction:', error);
        }
      }
    } catch (error) {
      console.error('Error loading stock data:', error);
    } finally {
      setLoading(false);
    }
  };

  const isInWatchlist = watchlist.includes(symbol);

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
      <div className={`flex items-center gap-2 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
        <span className="font-semibold text-lg">
          {isPositive ? '+' : ''}{formatCurrency(change)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
        </span>
      </div>
    );
  };

  const getSignalColor = (signal: 'buy' | 'sell' | 'hold') => {
    switch (signal) {
      case 'buy':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'sell':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    }
  };

  const chartData = historicalData.slice().reverse().map(item => ({
    date: format(new Date(item.date), 'MMM dd'),
    price: item.close,
    volume: item.volume,
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Activity className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">Loading stock data...</p>
        </div>
      </div>
    );
  }

  if (!quote) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <p className="text-gray-600 mb-4">Stock not found</p>
        <Button onClick={onBack}>Go Back</Button>
      </div>
    );
  }

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
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold">{symbol}</h1>
              <Star
                className={`w-5 h-5 cursor-pointer ${
                  isInWatchlist ? 'fill-yellow-400 text-yellow-400' : 'text-white/70'
                }`}
                onClick={() => {
                  if (isInWatchlist) {
                    onRemoveFromWatchlist(symbol);
                  } else {
                    onAddToWatchlist(symbol);
                  }
                }}
              />
            </div>
            <p className="text-blue-100 text-sm">{quote.longName}</p>
          </div>
        </div>

        {/* Price Info */}
        <div className="space-y-2">
          <div className="text-3xl font-bold">
            {formatCurrency(quote.regularMarketPrice)}
          </div>
          {formatChange(quote.regularMarketChange, quote.regularMarketChangePercent)}
          <div className="flex gap-4 text-sm text-blue-100">
            <span>High: {formatCurrency(quote.regularMarketDayHigh)}</span>
            <span>Low: {formatCurrency(quote.regularMarketDayLow)}</span>
          </div>
        </div>
      </div>

      {/* Timeframe Selector */}
      <div className="px-4 py-4 bg-white border-b">
        <div className="flex gap-2 overflow-x-auto">
          {(['1d', '5d', '1mo', '3mo', '6mo', '1y'] as Timeframe[]).map((tf) => (
            <Button
              key={tf}
              variant={timeframe === tf ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeframe(tf)}
              className="whitespace-nowrap"
            >
              {tf}
            </Button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="px-4 py-6">
        <Card className="border-0 shadow-md mb-6">
          <CardContent className="p-4">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Price Chart
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorPrice)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* AI Predictions */}
        {predictions.length > 0 && (
          <Card className="border-0 shadow-md mb-6">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-500" />
                  AI Predictions
                </h2>
                <div className="flex gap-2">
                  {(['1d', '1w', '1m', '3m'] as const).map((tf) => (
                    <Button
                      key={tf}
                      variant={selectedPredictionTimeframe === tf ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => {
                        setSelectedPredictionTimeframe(tf);
                        // Reload prediction with new timeframe
                        if (historicalData.length > 0) {
                          predictionService
                            .predictPrice(symbol, historicalData, tf)
                            .then((pred) => setPredictions([pred]))
                            .catch(console.error);
                        }
                      }}
                    >
                      {tf}
                    </Button>
                  ))}
                </div>
              </div>
              {predictions.map((pred) => (
                <div key={pred.timeframe} className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-2xl font-bold">
                        {formatCurrency(pred.predictedPrice)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Confidence: {pred.confidence.toFixed(1)}%
                      </div>
                    </div>
                    <Badge
                      className={`${
                        pred.trend === 'bullish'
                          ? 'bg-green-100 text-green-800'
                          : pred.trend === 'bearish'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {pred.trend.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold">Key Factors:</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                      {pred.reasons.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Technical Indicators */}
        {technicalIndicators.length > 0 && (
          <Card className="border-0 shadow-md mb-6">
            <CardContent className="p-4">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Technical Indicators
              </h2>
              <div className="grid grid-cols-1 gap-3">
                {technicalIndicators.map((indicator, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border ${getSignalColor(indicator.signal)}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">{indicator.name}</span>
                      <Badge className={getSignalColor(indicator.signal)}>
                        {indicator.signal.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="text-sm font-medium mb-1">
                      Value: {indicator.value.toFixed(2)}
                    </div>
                    <div className="text-xs opacity-80">{indicator.description}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stock Info */}
        <Card className="border-0 shadow-md">
          <CardContent className="p-4">
            <h2 className="text-lg font-semibold mb-4">Stock Information</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-600">Previous Close</div>
                <div className="font-semibold">{formatCurrency(quote.regularMarketPreviousClose)}</div>
              </div>
              <div>
                <div className="text-gray-600">Open</div>
                <div className="font-semibold">{formatCurrency(quote.regularMarketOpen)}</div>
              </div>
              <div>
                <div className="text-gray-600">Volume</div>
                <div className="font-semibold">{quote.regularMarketVolume.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-gray-600">52W High</div>
                <div className="font-semibold">{formatCurrency(quote.fiftyTwoWeekHigh)}</div>
              </div>
              <div>
                <div className="text-gray-600">52W Low</div>
                <div className="font-semibold">{formatCurrency(quote.fiftyTwoWeekLow)}</div>
              </div>
              <div>
                <div className="text-gray-600">Exchange</div>
                <div className="font-semibold">{quote.exchange}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

