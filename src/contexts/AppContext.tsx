/**
 * App Context
 * Central state management for accounts, transactions, and navigation
 */

import { createContext, useContext, ReactNode, useState, useCallback } from 'react';
import { useNavigation } from '../hooks/useNavigation';
import { useTransactions } from '../hooks/useTransactions';
import type { Account } from '../types/account';
import type { Transaction, PaymentData } from '../types/transaction';
import type { Screen, ScreenData } from '../types/navigation';

// Sample account data
const initialAccounts: Account[] = [
    {
        id: '1',
        name: 'Main Account',
        balance: 1250.5,
        currency: 'USD',
        color: '#10b981',
        type: 'primary',
    },
    { id: '2', name: 'Savings', balance: 5000.0, currency: 'USD', color: '#3b82f6', type: 'savings' },
    { id: '3', name: 'ZWL Account', balance: 85000, currency: 'ZWL', color: '#f59e0b', type: 'zwl' },
];

// Sample transaction data
const initialTransactions: Transaction[] = [
    {
        id: '1',
        type: 'sent',
        amount: 50.0,
        currency: 'USD',
        recipient: 'John Doe',
        description: 'Lunch payment',
        status: 'completed',
        date: new Date().toISOString(),
        paymentMethod: 'Zippie',
    },
    {
        id: '2',
        type: 'received',
        amount: 100.0,
        currency: 'USD',
        recipient: 'You',
        sender: 'Jane Smith',
        description: 'Reimbursement',
        status: 'completed',
        date: new Date(Date.now() - 86400000).toISOString(),
        paymentMethod: 'Zippie',
    },
    {
        id: '3',
        type: 'request',
        amount: 25.0,
        currency: 'USD',
        recipient: 'Mike Johnson',
        description: 'Shared expenses',
        status: 'pending',
        date: new Date(Date.now() - 172800000).toISOString(),
    },
];

interface AppContextValue {
    // Accounts
    accounts: Account[];
    updateAccountBalance: (accountName: string, amount: number) => void;

    // Transactions
    transactions: Transaction[];
    addTransaction: (data: PaymentData) => Transaction;
    getRecentTransactions: (limit: number) => Transaction[];

    // Navigation
    currentScreen: Screen;
    screenData: ScreenData;
    navigate: (screen: Screen, data?: ScreenData) => void;
    goBack: () => void;

    // Payment handling
    handlePaymentSuccess: (data: PaymentData) => void;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
    const [accounts, setAccounts] = useState<Account[]>(initialAccounts);
    const navigation = useNavigation('home');
    const transactionManager = useTransactions(initialTransactions);

    const updateAccountBalance = useCallback((accountName: string, amount: number) => {
        setAccounts(prev =>
            prev.map(account => {
                if (account.name === accountName) {
                    return {
                        ...account,
                        balance: account.balance - amount,
                    };
                }
                return account;
            })
        );
    }, []);

    const addTransaction = useCallback(
        (data: PaymentData): Transaction => {
            return transactionManager.addTransaction(data);
        },
        [transactionManager]
    );

    const handlePaymentSuccess = useCallback(
        (data: PaymentData) => {
            // Update accounts if money was sent
            if (data.type === 'send' && data.account) {
                updateAccountBalance(data.account, data.amount + (data.fee || 0));
            }

            // Add transaction
            addTransaction(data);

            // Navigate to success screen
            navigation.navigate('payment-success', {
                paymentData: {
                    ...data,
                    link: data.link || `https://zippie.co.zw/pay/${Math.random().toString(36).substr(2, 9)}`,
                },
            });
        },
        [updateAccountBalance, addTransaction, navigation]
    );

    return (
        <AppContext.Provider
            value={{
                accounts,
                updateAccountBalance,
                transactions: transactionManager.transactions,
                addTransaction,
                getRecentTransactions: transactionManager.getRecentTransactions,
                currentScreen: navigation.currentScreen,
                screenData: navigation.screenData,
                navigate: navigation.navigate,
                goBack: navigation.goBack,
                handlePaymentSuccess,
            }}
        >
            {children}
        </AppContext.Provider>
    );
}

export function useApp() {
    const context = useContext(AppContext);
    if (context === undefined) {
        throw new Error('useApp must be used within an AppProvider');
    }
    return context;
}
