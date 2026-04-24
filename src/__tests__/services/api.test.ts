/**
 * Tests for API service
 */
import { authAPI, paymentsAPI, setAuthToken, getAuthToken } from '../../services/api';

// Mock fetch
global.fetch = jest.fn();

describe('API Service', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
    localStorage.clear();
  });

  describe('Auth API', () => {
    it('should register a user', async () => {
      const mockResponse = {
        id: 1,
        email: 'test@example.com',
        phone: '+1234567890',
        full_name: 'Test User',
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await authAPI.register({
        email: 'test@example.com',
        phone: '+1234567890',
        full_name: 'Test User',
        password: 'TestPassword123',
      });

      // api.ts wraps headers in `new Headers(...)`, so inspect via .get() rather
      // than object-shape matchers (Headers stringifies as {map: {...}}).
      const [url, options] = (fetch as jest.Mock).mock.calls[0];
      expect(url).toContain('/auth/register');
      expect(options.method).toBe('POST');
      expect((options.headers as Headers).get('Content-Type')).toBe('application/json');
      expect(result).toEqual(mockResponse);
    });

    it('should login a user', async () => {
      const mockResponse = {
        access_token: 'test-token',
        token_type: 'bearer',
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await authAPI.login('test@example.com', 'password');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/x-www-form-urlencoded',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
      expect(localStorage.getItem('auth_token')).toBe('test-token');
    });

    it('should get current user', async () => {
      setAuthToken('test-token');
      const mockResponse = {
        id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await authAPI.getCurrentUser();

      const [url, options] = (fetch as jest.Mock).mock.calls[0];
      expect(url).toContain('/auth/me');
      expect((options.headers as Headers).get('Authorization')).toBe('Bearer test-token');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Payments API', () => {
    beforeEach(() => {
      setAuthToken('test-token');
    });

    it('should get accounts', async () => {
      // getAccounts() runs mapAccount() on each row (numeric id → string,
      // account_type → type, etc). Mock the backend shape; assert the mapped
      // frontend shape.
      const backendShape = [
        {
          id: 1,
          name: 'Main Account',
          balance: 1000,
          currency: 'USD',
          account_type: 'primary',
          color: '#10b981',
          is_active: true,
          user_id: 1,
          created_at: '2026-01-01T00:00:00Z',
        },
      ];

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => backendShape,
      });

      const result = await paymentsAPI.getAccounts();

      const [url, options] = (fetch as jest.Mock).mock.calls[0];
      expect(url).toContain('/payments/accounts');
      expect((options.headers as Headers).get('Authorization')).toBe('Bearer test-token');
      expect(result).toEqual([
        {
          id: '1',
          name: 'Main Account',
          balance: 1000,
          currency: 'USD',
          color: '#10b981',
          type: 'primary',
        },
      ]);
    });

    it('should create a transaction', async () => {
      // createTransaction() runs mapTransaction() on the backend response
      // (numeric id → string, transaction_type → type, created_at → date,
      // payment_method → paymentMethod with default).
      const backendShape = {
        id: 1,
        transaction_type: 'sent',
        amount: 100,
        currency: 'USD',
        status: 'completed',
        recipient: 'recipient@example.com',
        sender: 'me@example.com',
        description: 'Test',
        payment_method: 'zippie_internal',
        created_at: '2026-01-01T00:00:00Z',
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => backendShape,
      });

      const result = await paymentsAPI.createTransaction({
        transaction_type: 'sent',
        amount: 100,
        currency: 'USD',
        recipient: 'recipient@example.com',
        account_id: 1,
      });

      const [url, options] = (fetch as jest.Mock).mock.calls[0];
      expect(url).toContain('/payments/transactions');
      expect(options.method).toBe('POST');
      expect(typeof options.body).toBe('string');
      expect(result).toEqual({
        id: '1',
        type: 'sent',
        amount: 100,
        currency: 'USD',
        recipient: 'recipient@example.com',
        sender: 'me@example.com',
        description: 'Test',
        status: 'completed',
        date: '2026-01-01T00:00:00Z',
        paymentMethod: 'zippie_internal',
      });
    });
  });

  describe('Token Management', () => {
    it('should set and get auth token', () => {
      setAuthToken('test-token');
      expect(getAuthToken()).toBe('test-token');
      expect(localStorage.getItem('auth_token')).toBe('test-token');
    });

    it('should remove auth token', () => {
      setAuthToken('test-token');
      setAuthToken(null);
      expect(getAuthToken()).toBeNull();
      expect(localStorage.getItem('auth_token')).toBeNull();
    });
  });

  describe('Error Handling', () => {
    it('should handle 401 errors by clearing token', async () => {
      setAuthToken('invalid-token');

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      });

      await expect(authAPI.getCurrentUser()).rejects.toThrow('Unauthorized');
      expect(getAuthToken()).toBeNull();
    });

    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(authAPI.getCurrentUser()).rejects.toThrow();
    });
  });
});
