/**
 * API Service for Backend Integration
 * Connects frontend to FastAPI backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Authentication token management
let authToken: string | null = localStorage.getItem('auth_token');

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
};

export const getAuthToken = (): string | null => {
  return authToken || localStorage.getItem('auth_token');
};

// API Request helper
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Unauthorized - clear token and redirect to login
      setAuthToken(null);
      throw new Error('Unauthorized');
    }
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Auth API
export const authAPI = {
  register: async (userData: {
    email: string;
    phone: string;
    full_name: string;
    password: string;
  }) => {
    const response = await apiRequest<{ access_token: string; token_type: string }>(
      '/auth/register',
      {
        method: 'POST',
        body: JSON.stringify(userData),
      }
    );
    return response;
  },

  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    setAuthToken(data.access_token);
    return data;
  },

  getCurrentUser: async () => {
    return apiRequest('/auth/me');
  },
};

// Stocks API
export const stocksAPI = {
  getQuote: async (symbol: string) => {
    return apiRequest(`/stocks/quote/${symbol}`);
  },

  getMultipleQuotes: async (symbols: string[]) => {
    const symbolsStr = symbols.join(',');
    return apiRequest(`/stocks/quote?symbols=${symbolsStr}`);
  },

  getHistoricalData: async (symbol: string, period: string = '1mo') => {
    return apiRequest(`/stocks/historical/${symbol}?period=${period}`);
  },

  getPrediction: async (symbol: string, timeframe: string = '1d') => {
    return apiRequest(`/stocks/predict/${symbol}?timeframe=${timeframe}`);
  },

  searchStocks: async (query: string) => {
    return apiRequest(`/stocks/search?q=${encodeURIComponent(query)}`);
  },

  getPopularStocks: async () => {
    return apiRequest('/stocks/popular');
  },
};

// Payments API
export const paymentsAPI = {
  getAccounts: async () => {
    return apiRequest('/payments/accounts');
  },

  createAccount: async (accountData: {
    name: string;
    currency?: string;
    account_type?: string;
    color?: string;
  }) => {
    return apiRequest('/payments/accounts', {
      method: 'POST',
      body: JSON.stringify(accountData),
    });
  },

  getTransactions: async (limit: number = 50) => {
    return apiRequest(`/payments/transactions?limit=${limit}`);
  },

  createTransaction: async (transactionData: {
    transaction_type: string;
    amount: number;
    currency: string;
    recipient: string;
    description?: string;
    payment_method?: string;
    account_id?: number;
  }) => {
    return apiRequest('/payments/transactions', {
      method: 'POST',
      body: JSON.stringify(transactionData),
    });
  },

  getBalance: async () => {
    return apiRequest('/payments/balance');
  },
};

// Watchlists API
export const watchlistsAPI = {
  getWatchlist: async () => {
    return apiRequest('/watchlists');
  },

  addToWatchlist: async (watchlistData: {
    symbol: string;
    exchange?: string;
    target_price?: number;
    notes?: string;
  }) => {
    return apiRequest('/watchlists', {
      method: 'POST',
      body: JSON.stringify(watchlistData),
    });
  },

  removeFromWatchlist: async (watchlistId: number) => {
    return apiRequest(`/watchlists/${watchlistId}`, {
      method: 'DELETE',
    });
  },

  removeFromWatchlistBySymbol: async (symbol: string) => {
    return apiRequest(`/watchlists/symbol/${symbol}`, {
      method: 'DELETE',
    });
  },
};

