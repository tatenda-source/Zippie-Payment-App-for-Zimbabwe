/**
 * Transaction-related type definitions
 */

import type { Currency } from './account';

export type TransactionType = 'sent' | 'received' | 'request';
export type TransactionStatus = 'completed' | 'pending' | 'failed' | 'processing';
export type PaymentChannel = 'ecocash' | 'onemoney' | 'web';

export interface Transaction {
  id: string;
  type: TransactionType;
  amount: number;
  currency: Currency;
  recipient: string;
  sender?: string;
  description: string;
  status: TransactionStatus;
  date: string;
  paymentMethod?: string;
  fee?: number;
}

export interface TransactionFilter {
  type?: TransactionType;
  status?: TransactionStatus;
  currency?: Currency;
  startDate?: string;
  endDate?: string;
  searchTerm?: string;
}

export interface PaymentData {
  type: 'send' | 'request';
  amount: number;
  currency: Currency;
  recipient?: string;
  recipients?: string[];
  description: string;
  account?: string;
  fee?: number;
  paymentMethod?: string;
  paymentChannel?: PaymentChannel;
  phoneNumber?: string;
  link?: string;
}
