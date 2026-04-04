/**
 * API Service for Backend Integration
 * Connects frontend to FastAPI backend
 */

import { logger } from '../utils/logger';
import type { Transaction, TransactionType, TransactionStatus } from '../types/transaction';
import type { Account, Currency, AccountType } from '../types/account';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Authentication token management
// [SECURITY] CAUTION: Storing tokens in localStorage is vulnerable to XSS.
// TODO: Migrate to HttpOnly cookies for better security in production V2.
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
/**
 * Generic API request wrapper with auth handling and logging.
 * @template T - The expected response type
 * @param endpoint - The API endpoint (starting with /)
 * @param options - Fetch options
 */
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers as HeadersInit);

  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const startTime = Date.now();
  logger.apiCall(endpoint, options.method || 'GET');

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    const responseTime = Date.now() - startTime;
    logger.apiResponse(endpoint, response.status, responseTime);

    if (!response.ok) {
      if (response.status === 401) {
        setAuthToken(null);
        // Dispatch event or callback to redirect to login would be better here
        logger.error('Unauthorized API request', new Error('Unauthorized'));
        throw new Error('Unauthorized');
      }
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      logger.error(
        `API request failed: ${endpoint}`,
        new Error(error.detail || `HTTP error! status: ${response.status}`)
      );
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    logger.error(`API request exception: ${endpoint}`, error);
    throw error;
  }
}

// Backend Types mapping
interface BackendAccount {
  id: number;
  name: string;
  currency: string;
  account_type: string;
  color: string;
  balance: number;
  is_active: boolean;
  user_id: number;
  created_at: string;
}

interface BackendTransaction {
  id: number;
  transaction_type: string;
  amount: number;
  currency: string;
  recipient: string;
  sender?: string;
  description?: string;
  payment_method?: string;
  status: string;
  created_at: string;
  account_id?: number;
  fee?: number;
}

// Adapters
const mapAccount = (acc: BackendAccount): Account => ({
  id: acc.id.toString(),
  name: acc.name,
  balance: acc.balance,
  currency: acc.currency as Currency,
  color: acc.color,
  type: acc.account_type as AccountType
});

const mapTransaction = (tx: BackendTransaction): Transaction => ({
  id: tx.id.toString(),
  type: tx.transaction_type as TransactionType,
  amount: tx.amount,
  currency: tx.currency as Currency,
  recipient: tx.recipient,
  sender: tx.sender,
  description: tx.description || '',
  status: tx.status as TransactionStatus,
  date: tx.created_at,
  paymentMethod: tx.payment_method || 'Zippie Balance'
});

// Auth API
export const authAPI = {
  register: async (userData: {
    email: string;
    phone: string;
    full_name: string;
    password: string;
  }) => {
    return apiRequest<{ access_token: string; token_type: string }>(
      '/auth/register',
      {
        method: 'POST',
        body: JSON.stringify(userData),
      }
    );
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

// Payments API
export const paymentsAPI = {
  getAccounts: async (): Promise<Account[]> => {
    const accounts = await apiRequest<BackendAccount[]>('/payments/accounts');
    return accounts.map(mapAccount);
  },

  createAccount: async (accountData: {
    name: string;
    currency?: string;
    account_type?: string;
    color?: string;
  }): Promise<Account> => {
    const account = await apiRequest<BackendAccount>('/payments/accounts', {
      method: 'POST',
      body: JSON.stringify(accountData),
    });
    return mapAccount(account);
  },

  getTransactions: async (limit: number = 50): Promise<Transaction[]> => {
    const transactions = await apiRequest<BackendTransaction[]>(`/payments/transactions?limit=${limit}`);
    return transactions.map(mapTransaction);
  },

  createTransaction: async (transactionData: {
    transaction_type: string;
    amount: number;
    currency: string;
    recipient: string;
    description?: string;
    payment_method?: string;
    account_id?: number | string; // Accept string as we agreed to support string IDs in frontend
  }): Promise<Transaction> => {
    // If account_id is provided as string, try to parse it to int for backend
    const payload = { ...transactionData };
    if (payload.account_id && typeof payload.account_id === 'string') {
      payload.account_id = parseInt(payload.account_id, 10);
    }

    const transaction = await apiRequest<BackendTransaction>('/payments/transactions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return mapTransaction(transaction);
  },

  getBalance: async () => {
    const balanceData = await apiRequest<{ USD: number, ZWL: number, accounts: BackendAccount[] }>('/payments/balance');
    return {
      USD: balanceData.USD,
      ZWL: balanceData.ZWL,
      accounts: balanceData.accounts.map(mapAccount)
    };
  },

  initiatePaynowPayment: async (data: {
    transaction_id: number;
    payment_channel: 'ecocash' | 'onemoney' | 'web';
    phone_number?: string;
  }): Promise<{
    transaction_id: number;
    status: string;
    poll_url?: string;
    redirect_url?: string;
    instructions?: string;
    paynow_reference?: string;
  }> => {
    return apiRequest('/payments/paynow/initiate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  pollTransactionStatus: async (transactionId: number): Promise<{
    transaction_id: number;
    status: string;
    paid: boolean;
    paynow_reference?: string;
  }> => {
    return apiRequest(`/payments/paynow/status/${transactionId}`);
  },
};

