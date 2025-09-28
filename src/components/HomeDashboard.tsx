import React from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { 
  ArrowUpRight, 
  ArrowDownLeft, 
  QrCode, 
  Wallet, 
  History, 
  Settings,
  Check,
  Clock,
  X,
  Eye,
  EyeOff
} from 'lucide-react';
import type { Account, Transaction, Screen } from '../App';

interface HomeDashboardProps {
  accounts: Account[];
  transactions: Transaction[];
  onNavigate: (screen: Screen) => void;
}

export function HomeDashboard({ accounts, transactions, onNavigate }: HomeDashboardProps) {
  const [showBalances, setShowBalances] = React.useState(true);

  const totalUSD = accounts.filter(a => a.currency === 'USD').reduce((sum, a) => sum + a.balance, 0);
  const totalZWL = accounts.filter(a => a.currency === 'ZWL').reduce((sum, a) => sum + a.balance, 0);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <Check className="w-4 h-4 text-green-600" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'failed':
        return <X className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatCurrency = (amount: number, currency: 'USD' | 'ZWL') => {
    if (currency === 'USD') {
      return `$${amount.toFixed(2)}`;
    }
    return `ZWL$${amount.toLocaleString()}`;
  };

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-teal-50 to-white">
      {/* Header */}
      <div className="bg-primary text-primary-foreground px-4 py-6 rounded-b-3xl">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Zippie</h1>
            <p className="text-teal-100">Good morning! 🇿🇼</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowBalances(!showBalances)}
              className="text-white hover:bg-teal-600"
            >
              {showBalances ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </Button>
            <Button
              variant="ghost" 
              size="sm"
              className="text-white hover:bg-teal-600"
            >
              <Settings className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Total Balance */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-teal-100">Total Balance</span>
            <Wallet className="w-5 h-5 text-teal-100" />
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-bold text-white">
              {showBalances ? formatCurrency(totalUSD, 'USD') : '••••••'}
            </div>
            <div className="text-lg text-teal-100">
              {showBalances ? formatCurrency(totalZWL, 'ZWL') : '••••••••'}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-6">
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Button
            onClick={() => onNavigate('send')}
            className="flex flex-col items-center gap-2 h-20 bg-white border border-gray-200 text-gray-700 hover:bg-gray-50"
            variant="outline"
          >
            <ArrowUpRight className="w-6 h-6" />
            <span>Send</span>
          </Button>
          <Button
            onClick={() => onNavigate('request')}
            className="flex flex-col items-center gap-2 h-20 bg-accent text-accent-foreground hover:bg-accent/90"
          >
            <ArrowDownLeft className="w-6 h-6" />
            <span>Request</span>
          </Button>
          <Button
            variant="outline"
            className="flex flex-col items-center gap-2 h-20 bg-white border border-gray-200 text-gray-700 hover:bg-gray-50"
          >
            <QrCode className="w-6 h-6" />
            <span>Scan</span>
          </Button>
        </div>

        {/* Accounts */}
        <div className="space-y-4 mb-6">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">Accounts</h2>
            <Button variant="ghost" size="sm" className="text-primary">
              View All
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {accounts.map((account) => (
              <Card key={account.id} className="border-0 shadow-sm">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: account.color }}
                    />
                    <span className="text-sm font-medium">{account.name}</span>
                  </div>
                  <div className="text-lg font-bold">
                    {showBalances ? formatCurrency(account.balance, account.currency) : '••••••'}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">Recent Activity</h2>
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-primary"
              onClick={() => onNavigate('history')}
            >
              <History className="w-4 h-4 mr-1" />
              View All
            </Button>
          </div>
          <div className="space-y-3">
            {transactions.slice(0, 3).map((transaction) => (
              <Card key={transaction.id} className="border-0 shadow-sm">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                        {transaction.type === 'sent' && <ArrowUpRight className="w-5 h-5 text-red-500" />}
                        {transaction.type === 'received' && <ArrowDownLeft className="w-5 h-5 text-green-500" />}
                        {transaction.type === 'request' && <Clock className="w-5 h-5 text-yellow-500" />}
                      </div>
                      <div>
                        <p className="font-medium">
                          {transaction.type === 'sent' ? `To ${transaction.recipient}` : 
                           transaction.type === 'received' ? `From ${transaction.sender}` : 
                           `Request from ${transaction.recipient}`}
                        </p>
                        <p className="text-sm text-gray-500">{transaction.description}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">
                          {transaction.type === 'sent' ? '-' : '+'}
                          {formatCurrency(transaction.amount, transaction.currency)}
                        </p>
                        {getStatusIcon(transaction.status)}
                      </div>
                      <p className="text-xs text-gray-400">
                        {new Date(transaction.date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}