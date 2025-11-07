import { useState, useCallback, useMemo, useEffect } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { StockDashboard } from './components/StockDashboard';
import { StockSearch } from './components/StockSearch';
import { StockDetail } from './components/StockDetail';
import { Watchlist } from './components/Watchlist';
import type { WatchlistItem } from './types/stock';

export type Screen = 'home' | 'search' | 'detail' | 'watchlist';
export type StockQuote = any; // Re-export for components
export { type WatchlistItem };

interface ScreenData {
  symbol?: string;
  [key: string]: any;
}

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('home');
  const [screenData, setScreenData] = useState<ScreenData>({});
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>(() => {
    // Load watchlist from localStorage
    try {
      const saved = localStorage.getItem('stockWatchlist');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Save watchlist to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem('stockWatchlist', JSON.stringify(watchlist));
    } catch (error) {
      console.error('Error saving watchlist to localStorage:', error);
    }
  }, [watchlist]);

  const handleNavigate = useCallback((screen: Screen, data?: ScreenData) => {
    setCurrentScreen(screen);
    if (data) {
      setScreenData(data);
    }
  }, []);

  const handleBack = useCallback(() => {
    setCurrentScreen('home');
    setScreenData({});
  }, []);

  const handleAddToWatchlist = useCallback((symbol: string) => {
    setWatchlist(prev => {
      // Check if already in watchlist
      if (prev.some(item => item.symbol === symbol)) {
        return prev;
      }
      return [...prev, {
        symbol,
        addedAt: new Date().toISOString(),
      }];
    });
  }, []);

  const handleRemoveFromWatchlist = useCallback((symbol: string) => {
    setWatchlist(prev => prev.filter(item => item.symbol !== symbol));
  }, []);

  const handleSelectStock = useCallback((symbol: string) => {
    handleNavigate('detail', { symbol });
  }, [handleNavigate]);

  const watchlistSymbols = useMemo(() => 
    watchlist.map(item => item.symbol),
    [watchlist]
  );

  // Memoized screen renderer
  const renderScreen = useMemo(() => {
    switch (currentScreen) {
      case 'home':
        return (
          <StockDashboard
            watchlist={watchlist}
            onNavigate={handleNavigate}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
          />
        );
      case 'search':
        return (
          <StockSearch
            onBack={handleBack}
            onSelectStock={handleSelectStock}
            watchlist={watchlistSymbols}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
          />
        );
      case 'detail':
        return screenData.symbol ? (
          <StockDetail
            symbol={screenData.symbol}
            onBack={handleBack}
            watchlist={watchlistSymbols}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
          />
        ) : (
          <StockDashboard
            watchlist={watchlist}
            onNavigate={handleNavigate}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
          />
        );
      case 'watchlist':
        return (
          <Watchlist
            watchlist={watchlist}
            onBack={handleBack}
            onNavigate={handleNavigate}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
          />
        );
      default:
        return (
          <StockDashboard
            watchlist={watchlist}
            onNavigate={handleNavigate}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
          />
        );
    }
  }, [
    currentScreen,
    screenData,
    watchlist,
    watchlistSymbols,
    handleNavigate,
    handleBack,
    handleAddToWatchlist,
    handleRemoveFromWatchlist,
    handleSelectStock,
  ]);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 max-w-md mx-auto">
        {renderScreen}
      </div>
    </ErrorBoundary>
  );
}
