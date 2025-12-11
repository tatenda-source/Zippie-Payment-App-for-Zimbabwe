/**
 * Custom hook for transaction management
 */

import { useState, useCallback } from 'react';
import type { Transaction, TransactionFilter, PaymentData } from '../types/transaction';

export interface UseTransactionsReturn {
    transactions: Transaction[];
    addTransaction: (data: PaymentData) => Transaction;
    getFilteredTransactions: (filter?: TransactionFilter) => Transaction[];
    getTransactionById: (id: string) => Transaction | undefined;
    getRecentTransactions: (limit: number) => Transaction[];
}

/**
 * Hook for managing transactions
 * @param initialTransactions - Initial transaction data
 * @returns Transaction state and methods
 */
export function useTransactions(
    initialTransactions: Transaction[] = []
): UseTransactionsReturn {
    const [transactions, setTransactions] = useState<Transaction[]>(initialTransactions);

    const addTransaction = useCallback(
        (data: PaymentData): Transaction => {
            const newTransaction: Transaction = {
                id: Date.now().toString(),
                type: data.type === 'send' ? 'sent' : 'request',
                amount: data.amount,
                currency: data.currency,
                recipient: data.recipient || data.recipients?.join(', ') || 'Multiple recipients',
                description: data.description,
                status: 'completed',
                date: new Date().toISOString(),
                paymentMethod: data.paymentMethod || 'Zippie',
            };

            setTransactions(prev => [newTransaction, ...prev]);
            return newTransaction;
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
        addTransaction,
        getFilteredTransactions,
        getTransactionById,
        getRecentTransactions,
    };
}
