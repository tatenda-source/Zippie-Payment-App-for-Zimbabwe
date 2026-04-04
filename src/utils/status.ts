/**
 * Status utilities for transactions and UI states
 * Provides consistent status icons, colors, and labels
 */

import { Check, Clock, X, type LucideIcon } from 'lucide-react';

export type TransactionStatus = 'completed' | 'pending' | 'failed';

/**
 * Get icon component for a given status
 * @param status - The transaction status
 * @returns Lucide icon component
 */
export function getStatusIcon(status: TransactionStatus): LucideIcon {
  switch (status) {
    case 'completed':
      return Check;
    case 'pending':
      return Clock;
    case 'failed':
      return X;
    default:
      return Clock;
  }
}

/**
 * Get color class for status badge
 * @param status - The transaction status
 * @returns Tailwind color classes for badge
 */
export function getStatusColorClass(status: TransactionStatus): string {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-700';
    case 'pending':
      return 'bg-yellow-100 text-yellow-700';
    case 'failed':
      return 'bg-red-100 text-red-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

/**
 * Get icon color class for status
 * @param status - The transaction status
 * @returns Tailwind text color class
 */
export function getStatusIconColor(status: TransactionStatus): string {
  switch (status) {
    case 'completed':
      return 'text-green-600';
    case 'pending':
      return 'text-yellow-600';
    case 'failed':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}

/**
 * Get human-readable status label
 * @param status - The transaction status
 * @returns Formatted status label
 */
export function getStatusLabel(status: TransactionStatus): string {
  switch (status) {
    case 'completed':
      return 'Completed';
    case 'pending':
      return 'Pending';
    case 'failed':
      return 'Failed';
    default:
      return 'Unknown';
  }
}

/**
 * Check if a status is final (not pending)
 * @param status - The transaction status
 * @returns True if status is final
 */
export function isFinalStatus(status: TransactionStatus): boolean {
  return status === 'completed' || status === 'failed';
}

/**
 * Get background color class for status
 * @param status - The transaction status
 * @returns Tailwind background color class
 */
export function getStatusBgColor(status: TransactionStatus): string {
  switch (status) {
    case 'completed':
      return 'bg-green-50';
    case 'pending':
      return 'bg-yellow-50';
    case 'failed':
      return 'bg-red-50';
    default:
      return 'bg-gray-50';
  }
}
