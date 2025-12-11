/**
 * Currency formatting utilities
 * Centralized currency formatting logic used across the application
 */

export type Currency = 'USD' | 'ZWL';

/**
 * Format a number as currency with the appropriate symbol
 * @param amount - The amount to format
 * @param currency - The currency type (USD or ZWL)
 * @returns Formatted currency string
 */
export function formatCurrency(amount: number, currency: Currency = 'USD'): string {
  const absAmount = Math.abs(amount);
  const formattedAmount = absAmount.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  const symbol = currency === 'USD' ? '$' : 'ZWL';
  const sign = amount < 0 ? '-' : '';

  return `${sign}${symbol}${formattedAmount}`;
}

/**
 * Format stock price change with sign and percentage
 * @param change - The absolute change amount
 * @param changePercent - The percentage change
 * @returns Formatted change string
 */
export function formatChange(change: number, changePercent: number): string {
  const sign = change >= 0 ? '+' : '';
  const formattedChange = Math.abs(change).toFixed(2);
  const formattedPercent = Math.abs(changePercent).toFixed(2);

  return `${sign}$${formattedChange} (${sign}${formattedPercent}%)`;
}

/**
 * Format amount for display without currency symbol
 * @param amount - The amount to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted amount string
 */
export function formatAmount(amount: number, decimals: number = 2): string {
  return amount.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Parse a currency string to a number
 * @param currencyString - String like "$1,234.56" or "ZWL1,234.56"
 * @returns Parsed number
 */
export function parseCurrency(currencyString: string): number {
  const cleaned = currencyString.replace(/[^0-9.-]/g, '');
  return parseFloat(cleaned) || 0;
}

/**
 * Get currency symbol for a given currency type
 * @param currency - The currency type
 * @returns Currency symbol
 */
export function getCurrencySymbol(currency: Currency): string {
  return currency === 'USD' ? '$' : 'ZWL';
}

/**
 * Calculate fee based on amount and percentage
 * @param amount - Transaction amount
 * @param feePercent - Fee percentage (default: 1.5%)
 * @returns Calculated fee
 */
export function calculateFee(amount: number, feePercent: number = 1.5): number {
  return (amount * feePercent) / 100;
}

/**
 * Get color class for positive/negative changes
 * @param value - The value to check
 * @returns Tailwind color class
 */
export function getChangeColorClass(value: number): string {
  if (value > 0) return 'text-green-600';
  if (value < 0) return 'text-red-600';
  return 'text-gray-600';
}
