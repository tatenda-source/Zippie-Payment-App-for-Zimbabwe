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

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

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

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/me'),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('Payments API', () => {
    beforeEach(() => {
      setAuthToken('test-token');
    });

    it('should get accounts', async () => {
      const mockResponse = [
        {
          id: 1,
          name: 'Main Account',
          balance: 1000,
          currency: 'USD',
        },
      ];

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await paymentsAPI.getAccounts();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/payments/accounts'),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    it('should create a transaction', async () => {
      const mockResponse = {
        id: 1,
        transaction_type: 'sent',
        amount: 100,
        currency: 'USD',
        status: 'completed',
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await paymentsAPI.createTransaction({
        transaction_type: 'sent',
        amount: 100,
        currency: 'USD',
        recipient: 'recipient@example.com',
        account_id: 1,
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/payments/transactions'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(String),
        })
      );

      expect(result).toEqual(mockResponse);
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
