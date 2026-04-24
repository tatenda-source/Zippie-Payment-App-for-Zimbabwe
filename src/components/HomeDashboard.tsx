import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import {
  ArrowUpRight,
  ArrowDownLeft,
  QrCode,
  Wallet,
  History,
  Settings,
  Eye,
  EyeOff,
  Clock,
} from 'lucide-react';
import { formatCurrency } from '../utils/currency';
import { getStatusIcon } from '../utils/status';
import type { Account, Transaction, Screen } from '../App';

interface HomeDashboardProps {
  accounts: Account[];
  transactions: Transaction[];
  onNavigate: (screen: Screen) => void;
}

export function HomeDashboard({ accounts, transactions, onNavigate }: HomeDashboardProps) {
  const [showBalances, setShowBalances] = useState(true);

  const totalUSD = accounts
    .filter(a => a.currency === 'USD')
    .reduce((sum, a) => sum + a.balance, 0);
  const totalZWL = accounts
    .filter(a => a.currency === 'ZWL')
    .reduce((sum, a) => sum + a.balance, 0);

  return (
    <div className='flex flex-col min-h-screen bg-background'>
      {/* Header */}
      <div className='bg-primary text-primary-foreground px-4 py-6 rounded-b-3xl'>
        <div className='flex justify-between items-start mb-6'>
          <div>
            <h1 className='text-2xl font-bold'>Zippie</h1>
            <p className='text-primary-foreground/70'>Good morning!</p>
          </div>
          <div className='flex gap-2'>
            <Button
              variant='ghost'
              size='icon'
              onClick={() => setShowBalances(!showBalances)}
              className='text-primary-foreground hover:bg-primary-foreground/10 min-w-11 min-h-11'
              aria-label={showBalances ? 'Hide balances' : 'Show balances'}
              aria-pressed={showBalances}
            >
              {showBalances ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
            </Button>
            <Button
              variant='ghost'
              size='icon'
              className='text-primary-foreground hover:bg-primary-foreground/10 min-w-11 min-h-11'
              aria-label='Settings'
            >
              <Settings className='w-5 h-5' />
            </Button>
          </div>
        </div>

        {/* Total Balance */}
        <div className='space-y-2'>
          <div className='flex items-center justify-between'>
            <span className='text-primary-foreground/70'>Total Balance</span>
            <Wallet className='w-5 h-5 text-primary-foreground/70' />
          </div>
          <div className='space-y-1'>
            <div className='text-2xl font-bold'>
              {showBalances ? formatCurrency(totalUSD, 'USD') : '••••••'}
            </div>
            <div className='text-lg text-primary-foreground/70'>
              {showBalances ? formatCurrency(totalZWL, 'ZWL') : '••••••••'}
            </div>
            <div className='text-xs text-primary-foreground/50 mt-2'>
              1 USD = 25,000 ZWL (approx)
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className='px-4 py-6'>
        <div className='grid grid-cols-3 gap-4 mb-6'>
          <Button
            onClick={() => onNavigate('send')}
            className='flex flex-col items-center gap-2 h-20 bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
            variant='outline'
          >
            <ArrowUpRight className='w-6 h-6' />
            <span>Send</span>
          </Button>
          <Button
            onClick={() => onNavigate('request')}
            className='flex flex-col items-center gap-2 h-20 bg-accent text-accent-foreground hover:bg-accent/90'
          >
            <ArrowDownLeft className='w-6 h-6' />
            <span>Request</span>
          </Button>
          <Button
            variant='outline'
            className='flex flex-col items-center gap-2 h-20 bg-card border border-border text-foreground hover:bg-muted'
          >
            <QrCode className='w-6 h-6' />
            <span>Scan</span>
          </Button>
        </div>

        {/* Accounts */}
        <div className='space-y-4 mb-6'>
          <div className='flex justify-between items-center'>
            <h2 className='text-lg font-semibold'>Accounts</h2>
            <Button variant='ghost' size='sm' className='text-primary'>
              View All
            </Button>
          </div>
          <div className='grid grid-cols-2 gap-3'>
            {accounts.map(account => (
              <Card key={account.id} className='border-0 shadow-sm'>
                <CardContent className='p-4'>
                  <div className='flex items-center gap-3 mb-2'>
                    <div
                      className='w-3 h-3 rounded-full'
                      style={{ backgroundColor: account.color }}
                    />
                    <span className='text-sm font-medium'>{account.name}</span>
                  </div>
                  <div className='text-lg font-bold'>
                    {showBalances ? formatCurrency(account.balance, account.currency) : '••••••'}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Recent Transactions */}
        <div className='space-y-4'>
          <div className='flex justify-between items-center'>
            <h2 className='text-lg font-semibold'>Recent Activity</h2>
            <Button
              variant='ghost'
              size='sm'
              className='text-primary'
              onClick={() => onNavigate('history')}
            >
              <History className='w-4 h-4 mr-1' />
              View All
            </Button>
          </div>
          <div className='space-y-3'>
            {transactions.slice(0, 3).map(transaction => (
              <Card key={transaction.id} className='border-0 shadow-sm'>
                <CardContent className='p-4'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-muted rounded-full flex items-center justify-center'>
                        {transaction.type === 'sent' && (
                          <ArrowUpRight className='w-5 h-5 text-red-700 dark:text-red-400' />
                        )}
                        {transaction.type === 'received' && (
                          <ArrowDownLeft className='w-5 h-5 text-green-700 dark:text-green-400' />
                        )}
                        {transaction.type === 'request' && (
                          <Clock className='w-5 h-5 text-yellow-700 dark:text-yellow-400' />
                        )}
                      </div>
                      <div>
                        <p className='font-medium'>
                          {transaction.type === 'sent'
                            ? `To ${transaction.recipient}`
                            : transaction.type === 'received'
                              ? `From ${transaction.sender}`
                              : `Request from ${transaction.recipient}`}
                        </p>
                        <p className='text-sm text-muted-foreground'>{transaction.description}</p>
                      </div>
                    </div>
                    <div className='text-right'>
                      <div className='flex items-center gap-2'>
                        <p className='font-semibold'>
                          {transaction.type === 'sent' ? '-' : '+'}
                          {formatCurrency(transaction.amount, transaction.currency)}
                        </p>
                        {(() => {
                          const Icon = getStatusIcon(
                            transaction.status as 'completed' | 'pending' | 'failed'
                          );
                          const iconColor =
                            transaction.status === 'completed'
                              ? 'text-green-700 dark:text-green-400'
                              : transaction.status === 'pending'
                                ? 'text-yellow-700 dark:text-yellow-400'
                                : 'text-red-700 dark:text-red-400';
                          return <Icon className={`w-4 h-4 ${iconColor}`} />;
                        })()}
                      </div>
                      <p className='text-xs text-muted-foreground/70'>
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
