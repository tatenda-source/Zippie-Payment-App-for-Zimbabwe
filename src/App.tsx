import React, { useState, useCallback, useMemo } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { HomeDashboard } from './components/HomeDashboard';
import { SendMoney } from './components/SendMoney';
import { RequestPayment } from './components/RequestPayment';
import { TransactionHistory } from './components/TransactionHistory';
import { PaymentSuccess } from './components/PaymentSuccess';

export type Account = {
  id: string;
  name: string;
  type: 'mobile' | 'bank';
  balance: number;
  currency: 'USD' | 'ZWL';
  color: string;
};

export type Transaction = {
  id: string;
  type: 'sent' | 'received' | 'request';
  amount: number;
  currency: 'USD' | 'ZWL';
  recipient: string;
  sender: string;
  description: string;
  status: 'completed' | 'pending' | 'failed';
  date: string;
  paymentMethod?: string;
};

export type Screen = 'home' | 'send' | 'request' | 'history' | 'success';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('home');
  const [successData, setSuccessData] = useState<any>(null);

  // Memoized mock data to prevent unnecessary re-renders
  const mockAccounts: Account[] = useMemo(() => [
    { id: '1', name: 'EcoCash', type: 'mobile', balance: 250.50, currency: 'USD', color: '#f59e0b' },
    { id: '2', name: 'OneMoney', type: 'mobile', balance: 1500.00, currency: 'ZWL', color: '#ef4444' },
    { id: '3', name: 'Steward Bank', type: 'bank', balance: 850.25, currency: 'USD', color: '#3b82f6' },
    { id: '4', name: 'CBZ ZIPIT', type: 'bank', balance: 2250.00, currency: 'ZWL', color: '#10b981' },
  ], []);

  const mockTransactions: Transaction[] = useMemo(() => [
    {
      id: '1',
      type: 'received',
      amount: 50.00,
      currency: 'USD',
      recipient: 'You',
      sender: 'Tendai Mukamuri',
      description: 'Lunch money',
      status: 'completed',
      date: '2025-01-08T10:30:00Z',
      paymentMethod: 'EcoCash'
    },
    {
      id: '2',
      type: 'sent',
      amount: 25.00,
      currency: 'USD',
      recipient: 'Chipo Nhongo',
      sender: 'You',
      description: 'Coffee',
      status: 'completed',
      date: '2025-01-07T14:15:00Z',
      paymentMethod: 'Steward Bank'
    },
    {
      id: '3',
      type: 'request',
      amount: 75.00,
      currency: 'USD',
      recipient: 'Tadiwa Mazuva',
      sender: 'You',
      description: 'Dinner split',
      status: 'pending',
      date: '2025-01-07T19:45:00Z'
    }
  ], []);

  // Memoized callback functions to prevent unnecessary re-renders
  const handleSendSuccess = useCallback((data: any) => {
    setSuccessData(data);
    setCurrentScreen('success');
  }, []);

  const handleRequestSuccess = useCallback((data: any) => {
    setSuccessData(data);
    setCurrentScreen('success');
  }, []);

  const handleNavigate = useCallback((screen: Screen) => {
    setCurrentScreen(screen);
  }, []);

  const handleBack = useCallback(() => {
    setCurrentScreen('home');
  }, []);

  // Memoized screen renderer to prevent unnecessary re-renders
  const renderScreen = useMemo(() => {
    switch (currentScreen) {
      case 'home':
        return (
          <HomeDashboard
            accounts={mockAccounts}
            transactions={mockTransactions}
            onNavigate={handleNavigate}
          />
        );
      case 'send':
        return (
          <SendMoney
            accounts={mockAccounts}
            onBack={handleBack}
            onSuccess={handleSendSuccess}
          />
        );
      case 'request':
        return (
          <RequestPayment
            onBack={handleBack}
            onSuccess={handleRequestSuccess}
          />
        );
      case 'history':
        return (
          <TransactionHistory
            transactions={mockTransactions}
            onBack={handleBack}
          />
        );
      case 'success':
        return (
          <PaymentSuccess
            data={successData}
            onBack={handleBack}
          />
        );
      default:
        return (
          <HomeDashboard
            accounts={mockAccounts}
            transactions={mockTransactions}
            onNavigate={handleNavigate}
          />
        );
    }
  }, [currentScreen, mockAccounts, mockTransactions, handleNavigate, handleBack, handleSendSuccess, handleRequestSuccess, successData]);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 max-w-md mx-auto">
        {renderScreen}
      </div>
    </ErrorBoundary>
  );
}