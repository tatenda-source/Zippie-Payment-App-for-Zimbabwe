import { useState, useCallback, useMemo, useEffect } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { HomeDashboard } from './components/HomeDashboard';
import { SendMoney } from './components/SendMoney';
import { RequestPayment } from './components/RequestPayment';
import { TransactionHistory } from './components/TransactionHistory';
import { PaymentSuccess } from './components/PaymentSuccess';
import { StockDashboard } from './components/StockDashboard';
import { StockSearch } from './components/StockSearch';
import { StockDetail } from './components/StockDetail';
import { Watchlist } from './components/Watchlist';
import type { WatchlistItem } from './types/stock';

export type Screen = 'home' | 'send' | 'request' | 'history' | 'stocks' | 'stock-search' | 'stock-detail' | 'watchlist' | 'payment-success';
export type StockQuote = any; // Re-export for components
export { type WatchlistItem };

export interface Account {
  id: string;
  name: string;
  balance: number;
  currency: 'USD' | 'ZWL';
  color: string;
  type?: string;
}

export interface Transaction {
  id: string;
  type: 'sent' | 'received' | 'request';
  amount: number;
  currency: 'USD' | 'ZWL';
  recipient: string;
  sender?: string;
  description: string;
  status: 'completed' | 'pending' | 'failed';
  date: string;
  paymentMethod?: string;
}

interface ScreenData {
  symbol?: string;
  paymentData?: any;
  [key: string]: any;
}

// Sample account data
const initialAccounts: Account[] = [
  { id: '1', name: 'Main Account', balance: 1250.50, currency: 'USD', color: '#10b981', type: 'primary' },
  { id: '2', name: 'Savings', balance: 5000.00, currency: 'USD', color: '#3b82f6', type: 'savings' },
  { id: '3', name: 'ZWL Account', balance: 85000, currency: 'ZWL', color: '#f59e0b', type: 'zwl' },
];

// Sample transaction data
const initialTransactions: Transaction[] = [
  {
    id: '1',
    type: 'sent',
    amount: 50.00,
    currency: 'USD',
    recipient: 'John Doe',
    description: 'Lunch payment',
    status: 'completed',
    date: new Date().toISOString(),
    paymentMethod: 'Zippie',
  },
  {
    id: '2',
    type: 'received',
    amount: 100.00,
    currency: 'USD',
    recipient: 'You',
    sender: 'Jane Smith',
    description: 'Reimbursement',
    status: 'completed',
    date: new Date(Date.now() - 86400000).toISOString(),
    paymentMethod: 'Zippie',
  },
  {
    id: '3',
    type: 'request',
    amount: 25.00,
    currency: 'USD',
    recipient: 'Mike Johnson',
    description: 'Shared expenses',
    status: 'pending',
    date: new Date(Date.now() - 172800000).toISOString(),
  },
];

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('home');
  const [screenData, setScreenData] = useState<ScreenData>({});
  const [accounts, setAccounts] = useState<Account[]>(initialAccounts);
  const [transactions, setTransactions] = useState<Transaction[]>(initialTransactions);
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
    } else {
      setScreenData({});
    }
  }, []);

  const handleBack = useCallback(() => {
    setCurrentScreen('home');
    setScreenData({});
  }, []);

  const handlePaymentSuccess = useCallback((data: any) => {
    // Create new transaction
    const newTransaction: Transaction = {
      id: Date.now().toString(),
      type: data.type === 'send' ? 'sent' : 'request',
      amount: data.amount,
      currency: data.currency,
      recipient: data.recipient || 'Multiple recipients',
      description: data.description,
      status: 'completed',
      date: new Date().toISOString(),
      paymentMethod: data.paymentMethod || 'Zippie',
    };

    // Update accounts if money was sent
    if (data.type === 'send' && data.account) {
      setAccounts(prev => prev.map(account => {
        if (account.name === data.account) {
          return {
            ...account,
            balance: account.balance - data.amount - (data.fee || 0),
          };
        }
        return account;
      }));
    }

    setTransactions(prev => [newTransaction, ...prev]);
    handleNavigate('payment-success', { paymentData: { ...data, link: data.link || `https://zippie.co.zw/pay/${Math.random().toString(36).substr(2, 9)}` } });
  }, [handleNavigate]);

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
    handleNavigate('stock-detail', { symbol });
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
          <HomeDashboard
            accounts={accounts}
            transactions={transactions}
            onNavigate={handleNavigate}
          />
        );
      case 'send':
        return (
          <SendMoney
            accounts={accounts}
            onBack={handleBack}
            onSuccess={handlePaymentSuccess}
          />
        );
      case 'request':
        return (
          <RequestPayment
            onBack={handleBack}
            onSuccess={handlePaymentSuccess}
          />
        );
      case 'history':
        return (
          <TransactionHistory
            transactions={transactions}
            onBack={handleBack}
          />
        );
      case 'payment-success':
        return (
          <PaymentSuccess
            data={screenData.paymentData || {}}
            onBack={handleBack}
          />
        );
      case 'stocks':
        return (
          <StockDashboard
            watchlist={watchlist}
            onNavigate={handleNavigate}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
            onBack={handleBack}
          />
        );
      case 'stock-search':
        return (
          <StockSearch
            onBack={handleBack}
            onSelectStock={handleSelectStock}
            watchlist={watchlistSymbols}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
          />
        );
      case 'stock-detail':
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
          <HomeDashboard
            accounts={accounts}
            transactions={transactions}
            onNavigate={handleNavigate}
          />
        );
    }
  }, [
    currentScreen,
    screenData,
    accounts,
    transactions,
    watchlist,
    watchlistSymbols,
    handleNavigate,
    handleBack,
    handlePaymentSuccess,
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
