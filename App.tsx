import React, { useState } from 'react';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { 
  ArrowUpRight, 
  ArrowDownLeft, 
  QrCode, 
  Plus, 
  Wallet, 
  History, 
  Settings, 
  ChevronLeft,
  Share2,
  Check,
  Clock,
  X
} from 'lucide-react';
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

  const mockAccounts: Account[] = [
    { id: '1', name: 'EcoCash', type: 'mobile', balance: 250.50, currency: 'USD', color: '#f59e0b' },
    { id: '2', name: 'OneMoney', type: 'mobile', balance: 1500.00, currency: 'ZWL', color: '#ef4444' },
    { id: '3', name: 'Steward Bank', type: 'bank', balance: 850.25, currency: 'USD', color: '#3b82f6' },
    { id: '4', name: 'CBZ ZIPIT', type: 'bank', balance: 2250.00, currency: 'ZWL', color: '#10b981' },
  ];

  const mockTransactions: Transaction[] = [
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
  ];

  const handleSendSuccess = (data: any) => {
    setSuccessData(data);
    setCurrentScreen('success');
  };

  const handleRequestSuccess = (data: any) => {
    setSuccessData(data);
    setCurrentScreen('success');
  };

  const renderScreen = () => {
    switch (currentScreen) {
      case 'home':
        return (
          <HomeDashboard
            accounts={mockAccounts}
            transactions={mockTransactions}
            onNavigate={setCurrentScreen}
          />
        );
      case 'send':
        return (
          <SendMoney
            accounts={mockAccounts}
            onBack={() => setCurrentScreen('home')}
            onSuccess={handleSendSuccess}
          />
        );
      case 'request':
        return (
          <RequestPayment
            onBack={() => setCurrentScreen('home')}
            onSuccess={handleRequestSuccess}
          />
        );
      case 'history':
        return (
          <TransactionHistory
            transactions={mockTransactions}
            onBack={() => setCurrentScreen('home')}
          />
        );
      case 'success':
        return (
          <PaymentSuccess
            data={successData}
            onBack={() => setCurrentScreen('home')}
          />
        );
      default:
        return (
          <HomeDashboard
            accounts={mockAccounts}
            transactions={mockTransactions}
            onNavigate={setCurrentScreen}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 max-w-md mx-auto">
      {renderScreen()}
    </div>
  );
}