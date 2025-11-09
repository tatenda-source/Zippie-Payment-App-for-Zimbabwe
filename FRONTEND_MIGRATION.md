# Frontend Migration Guide

This guide explains how to migrate the frontend from mock data/localStorage to the backend API.

## Current State

- Components use mock data or localStorage
- Stock predictions run on frontend (TensorFlow.js)
- No authentication
- No backend connection

## Target State

- All data from backend API
- ML predictions on backend
- JWT authentication
- Real-time data from APIs

## Migration Steps

### Step 1: Update API Service

The API service is already created at `src/services/api.ts`. This handles all backend communication.

### Step 2: Add Authentication Context

Create an authentication context to manage user state:

```typescript
// src/contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI, getAuthToken, setAuthToken } from '../services/api';

interface AuthContextType {
  user: any | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: any) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const token = getAuthToken();
    if (token) {
      loadUser();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async () => {
    try {
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
    } catch (error) {
      setAuthToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    await authAPI.login(email, password);
    await loadUser();
  };

  const register = async (userData: any) => {
    await authAPI.register(userData);
    await login(userData.email, userData.password);
  };

  const logout = () => {
    setAuthToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### Step 3: Update App.tsx

Wrap the app with AuthProvider and add authentication check:

```typescript
// src/App.tsx
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './contexts/AuthContext';

function AppContent() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  // ... existing app content
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
```

### Step 4: Update HomeDashboard

Replace mock data with API calls:

```typescript
// src/components/HomeDashboard.tsx
import { useEffect, useState } from 'react';
import { paymentsAPI } from '../services/api';

export function HomeDashboard() {
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [accountsData, transactionsData] = await Promise.all([
        paymentsAPI.getAccounts(),
        paymentsAPI.getTransactions(10)
      ]);
      setAccounts(accountsData);
      setTransactions(transactionsData);
    } catch (error) {
      console.error('Error loading data:', error);
      // Show error message to user
    } finally {
      setLoading(false);
    }
  };

  // ... rest of component
}
```

### Step 5: Update StockDashboard

Replace frontend stock API with backend API:

```typescript
// src/components/StockDashboard.tsx
import { stocksAPI, watchlistsAPI } from '../services/api';

export function StockDashboard() {
  const [quotes, setQuotes] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [popularStocks, watchlistData] = await Promise.all([
        stocksAPI.getPopularStocks(),
        watchlistsAPI.getWatchlist()
      ]);
      setQuotes(popularStocks.stocks);
      setWatchlist(watchlistData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToWatchlist = async (symbol: string) => {
    try {
      await watchlistsAPI.addToWatchlist({ symbol });
      await loadData();
    } catch (error) {
      console.error('Error adding to watchlist:', error);
    }
  };

  // ... rest of component
}
```

### Step 6: Update StockDetail

Use backend for predictions:

```typescript
// src/components/StockDetail.tsx
import { stocksAPI } from '../services/api';

export function StockDetail({ symbol }: { symbol: string }) {
  const [prediction, setPrediction] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);

  useEffect(() => {
    loadData();
  }, [symbol]);

  const loadData = async () => {
    try {
      const [historical, pred] = await Promise.all([
        stocksAPI.getHistoricalData(symbol, '1mo'),
        stocksAPI.getPrediction(symbol, '1d')
      ]);
      setHistoricalData(historical);
      setPrediction(pred);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  // ... rest of component
}
```

### Step 7: Update SendMoney

Create transactions via API:

```typescript
// src/components/SendMoney.tsx
import { paymentsAPI } from '../services/api';

export function SendMoney({ onSuccess }: { onSuccess: () => void }) {
  const handleSend = async (transactionData: any) => {
    try {
      await paymentsAPI.createTransaction(transactionData);
      onSuccess();
    } catch (error) {
      console.error('Error sending money:', error);
      // Show error message
    }
  };

  // ... rest of component
}
```

### Step 8: Create Login/Register Components

```typescript
// src/components/Login.tsx
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError('');
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Login form */}
    </form>
  );
}
```

## Migration Checklist

### Authentication
- [ ] Create AuthContext
- [ ] Add Login component
- [ ] Add Register component
- [ ] Update App.tsx to use AuthProvider
- [ ] Add protected routes

### Payments
- [ ] Update HomeDashboard to use paymentsAPI
- [ ] Update SendMoney to use paymentsAPI
- [ ] Update RequestPayment to use paymentsAPI
- [ ] Update TransactionHistory to use paymentsAPI
- [ ] Remove mock data

### Stocks
- [ ] Update StockDashboard to use stocksAPI
- [ ] Update StockSearch to use stocksAPI
- [ ] Update StockDetail to use stocksAPI
- [ ] Update Watchlist to use watchlistsAPI
- [ ] Remove frontend prediction service (optional)

### Error Handling
- [ ] Add error boundaries
- [ ] Add loading states
- [ ] Add error messages
- [ ] Handle API errors gracefully

### Testing
- [ ] Test authentication flow
- [ ] Test payment flows
- [ ] Test stock features
- [ ] Test error handling

## Common Issues

### CORS Errors
- Ensure backend CORS_ORIGINS includes frontend URL
- Check REACT_APP_API_URL is correct

### Authentication Errors
- Verify token is being stored
- Check token expiration
- Ensure token is included in requests

### API Errors
- Check backend is running
- Verify database is connected
- Check API endpoint URLs
- Review backend logs

## Next Steps

1. Complete authentication UI
2. Migrate all components to use API
3. Add error handling
4. Add loading states
5. Test end-to-end flows
6. Deploy to production

## Support

For issues:
1. Check backend logs
2. Check browser console
3. Verify environment variables
4. Review API documentation: http://localhost:8000/api/docs

