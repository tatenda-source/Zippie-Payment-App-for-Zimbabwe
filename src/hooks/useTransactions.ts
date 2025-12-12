/**
 * Custom hook for transaction management
 */

import { useState, useCallback, useEffect } from 'react';
import type { Transaction, TransactionFilter, PaymentData } from '../types/transaction';
import { paymentsAPI } from '../services/api';

export interface UseTransactionsReturn {
    transactions: Transaction[];
    loading: boolean;
    error: string | null;
    addTransaction: (data: PaymentData) => Promise<Transaction>;
    getFilteredTransactions: (filter?: TransactionFilter) => Transaction[];
    getTransactionById: (id: string) => Transaction | undefined;
    getRecentTransactions: (limit: number) => Transaction[];
    refreshTransactions: () => Promise<void>;
}

/**
 * Hook for managing transactions
 * @param initialTransactions - Initial transaction data (fallback)
 * @returns Transaction state and methods
 */
export function useTransactions(
    initialTransactions: Transaction[] = []
): UseTransactionsReturn {
    const [transactions, setTransactions] = useState<Transaction[]>(initialTransactions);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const refreshTransactions = useCallback(async () => {
        setLoading(true);
        try {
            const data = await paymentsAPI.getTransactions();
            setTransactions(data);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch transactions:', err);
            setError('Failed to fetch transactions');
            // Keep initialTransactions if fetch fails to avoid empty screen in demo mode?
            // For now, let's assume valid API connection or empty state.
        } finally {
            setLoading(false);
        }
    }, []);

    // Initial fetch
    useEffect(() => {
        refreshTransactions();
    }, [refreshTransactions]);

    const addTransaction = useCallback(
        async (data: PaymentData): Promise<Transaction> => {
            setLoading(true);
            try {
                const newTransaction = await paymentsAPI.createTransaction({
                    transaction_type: data.type === 'send' ? 'sent' : 'request',
                    amount: data.amount,
                    currency: data.currency,
                    recipient: data.recipient || data.recipients?.join(', ') || 'Multiple recipients',
                    description: data.description,
                    payment_method: data.paymentMethod,
                    account_id: data.account, // API service handles string->int conversion if needed
                });

                setTransactions(prev => [newTransaction, ...prev]);
                return newTransaction;
            } catch (err) {
                console.error('Failed to create transaction:', err);
                setError('Failed to create transaction');
                throw err;
            } finally {
                setLoading(false);
            }
        },
        []
    );

    const getFilteredTransactions = useCallback(
        (filter?: TransactionFilter): Transaction[] => {
            if (!filter) return transactions;

            return transactions.filter(transaction => {
                if (filter.type && transaction.type !== filter.type) return false;
                if (filter.status && transaction.status !== filter.status) return false;
                if (filter.currency && transaction.currency !== filter.currency) return false;

                if (filter.startDate) {
                    const txDate = new Date(transaction.date);
                    const startDate = new Date(filter.startDate);
                    if (txDate < startDate) return false;
                }

                if (filter.endDate) {
                    const txDate = new Date(transaction.date);
                    const endDate = new Date(filter.endDate);
                    if (txDate > endDate) return false;
                }

                if (filter.searchTerm) {
                    const searchLower = filter.searchTerm.toLowerCase();
                    const matchesRecipient = transaction.recipient.toLowerCase().includes(searchLower);
                    const matchesSender = transaction.sender?.toLowerCase().includes(searchLower);
                    const matchesDescription = transaction.description.toLowerCase().includes(searchLower);
                    if (!matchesRecipient && !matchesSender && !matchesDescription) return false;
                }

                return true;
            });
        },
        [transactions]
    );

    const getTransactionById = useCallback(
        (id: string): Transaction | undefined => {
            return transactions.find(tx => tx.id === id);
        },
        [transactions]
    );

    const getRecentTransactions = useCallback(
        (limit: number): Transaction[] => {
            return transactions.slice(0, limit);
        },
        [transactions]
    );

    return {
        transactions,
        loading,
        error,
        addTransaction,
        getFilteredTransactions,
        getTransactionById,
        getRecentTransactions,
        refreshTransactions,
    };
}
