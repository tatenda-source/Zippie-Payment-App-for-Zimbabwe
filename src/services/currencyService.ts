/**
 * Currency Conversion Service
 * Handles exchange rates and currency conversions
 */

import { logger } from '../utils/logger';

export interface ExchangeRates {
    USD_ZWL: number;
    ZWL_USD: number;
    lastUpdated: string;
}

// Fallback rates (as of typical Zimbabwe rates)
const FALLBACK_RATES: ExchangeRates = {
    USD_ZWL: 25000, // 1 USD = 25,000 ZWL (approximate)
    ZWL_USD: 0.00004, // 1 ZWL = 0.00004 USD
    lastUpdated: new Date().toISOString(),
};

class CurrencyService {
    private rates: ExchangeRates = FALLBACK_RATES;
    private cacheKey = 'exchange_rates_cache';
    private cacheExpiry = 3600000; // 1 hour in milliseconds

    constructor() {
        this.loadCachedRates();
    }

    /**
     * Load cached exchange rates from localStorage
     */
    private loadCachedRates() {
        try {
            const cached = localStorage.getItem(this.cacheKey);
            if (cached) {
                const data = JSON.parse(cached);
                const age = Date.now() - new Date(data.lastUpdated).getTime();

                if (age < this.cacheExpiry) {
                    this.rates = data;
                    logger.info('Loaded cached exchange rates');
                } else {
                    logger.info('Cached rates expired, using fallback');
                }
            }
        } catch (error) {
            logger.error('Error loading cached rates', error);
        }
    }

    /**
     * Save exchange rates to localStorage
     */
    private saveCachedRates() {
        try {
            localStorage.setItem(this.cacheKey, JSON.stringify(this.rates));
        } catch (error) {
            logger.error('Error saving rates to cache', error);
        }
    }

    /**
     * Fetch latest exchange rates
     * In production, this would call a real API
     */
    async fetchRates(): Promise<ExchangeRates> {
        try {
            // TODO: Replace with actual API call
            // For now, we'll simulate an API call with fallback rates
            // Example: const response = await fetch('https://api.exchangerate.host/latest?base=USD&symbols=ZWL');

            await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay

            const newRates: ExchangeRates = {
                ...FALLBACK_RATES,
                lastUpdated: new Date().toISOString(),
            };

            this.rates = newRates;
            this.saveCachedRates();

            return newRates;
        } catch (error) {
            logger.error('Error fetching exchange rates', error);
            return this.rates; // Return cached/fallback rates on error
        }
    }

    /**
     * Get current exchange rates
     */
    getRates(): ExchangeRates {
        return { ...this.rates };
    }

    /**
     * Convert amount from one currency to another
     * @param amount - Amount to convert
     * @param from - Source currency
     * @param to - Target currency
     * @returns Converted amount
     */
    convert(amount: number, from: 'USD' | 'ZWL', to: 'USD' | 'ZWL'): number {
        if (from === to) return amount;

        const rate = from === 'USD' ? this.rates.USD_ZWL : this.rates.ZWL_USD;
        return amount * rate;
    }

    /**
     * Get exchange rate between two currencies
     * @param from - Source currency
     * @param to - Target currency
     * @returns Exchange rate
     */
    getRate(from: 'USD' | 'ZWL', to: 'USD' | 'ZWL'): number {
        if (from === to) return 1;
        return from === 'USD' ? this.rates.USD_ZWL : this.rates.ZWL_USD;
    }

    /**
     * Format conversion for display
     * @param amount - Amount to convert
     * @param from - Source currency
     * @param to - Target currency
     * @returns Formatted conversion string
     */
    formatConversion(amount: number, from: 'USD' | 'ZWL', to: 'USD' | 'ZWL'): string {
        const converted = this.convert(amount, from, to);
        const rate = this.getRate(from, to);

        const fromSymbol = from === 'USD' ? '$' : 'ZWL';
        const toSymbol = to === 'USD' ? '$' : 'ZWL';

        return `${fromSymbol}${amount.toLocaleString()} = ${toSymbol}${converted.toLocaleString()} (Rate: ${rate.toLocaleString()})`;
    }

    /**
     * Check if rates are stale (older than cache expiry)
     */
    areRatesStale(): boolean {
        const age = Date.now() - new Date(this.rates.lastUpdated).getTime();
        return age >= this.cacheExpiry;
    }

    /**
     * Get time until rates expire
     */
    getTimeUntilExpiry(): number {
        const age = Date.now() - new Date(this.rates.lastUpdated).getTime();
        return Math.max(0, this.cacheExpiry - age);
    }
}

// Export singleton instance
export const currencyService = new CurrencyService();
