import { useState, useMemo } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { ChevronLeft, History, ArrowUpRight, ArrowDownLeft, Clock, Download } from 'lucide-react';
import { TransactionFilter } from './TransactionFilter';
import { formatCurrency } from '../utils/currency';
import { getStatusIcon, getStatusColorClass } from '../utils/status';
import { formatTransactionDate } from '../utils/date';
import { logger } from '../utils/logger';
import type { Transaction } from '../App';
import type { TransactionFilter as FilterType } from '../types/transaction';

interface TransactionHistoryProps {
  transactions: Transaction[];
  onBack: () => void;
}

export function TransactionHistory({ transactions, onBack }: TransactionHistoryProps) {
  const [filter, setFilter] = useState<FilterType>({});

  const filteredTransactions = useMemo(() => {
    return transactions.filter(transaction => {
      // Search filter
      if (filter.searchTerm) {
        const searchLower = filter.searchTerm.toLowerCase();
        const matchesRecipient = transaction.recipient.toLowerCase().includes(searchLower);
        const matchesSender = transaction.sender?.toLowerCase().includes(searchLower);
        const matchesDescription = transaction.description.toLowerCase().includes(searchLower);
        if (!matchesRecipient && !matchesSender && !matchesDescription) return false;
      }

      // Type filter
      if (filter.type && transaction.type !== filter.type) return false;

      // Status filter
      if (filter.status && transaction.status !== filter.status) return false;

      // Currency filter
      if (filter.currency && transaction.currency !== filter.currency) return false;

      // Date range filter
      if (filter.startDate) {
        const txDate = new Date(transaction.date);
        const startDate = new Date(filter.startDate);
        if (txDate < startDate) return false;
      }

      if (filter.endDate) {
        const txDate = new Date(transaction.date);
        const endDate = new Date(filter.endDate);
        endDate.setHours(23, 59, 59, 999); // Include entire end date
        if (txDate > endDate) return false;
      }

      return true;
    });
  }, [transactions, filter]);

  const groupTransactionsByDate = (transactions: Transaction[]) => {
    const groups: { [key: string]: Transaction[] } = {};

    transactions.forEach(transaction => {
      const date = new Date(transaction.date).toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date]?.push(transaction);
    });

    return groups;
  };

  const groupedTransactions = groupTransactionsByDate(filteredTransactions);
  const sortedDates = Object.keys(groupedTransactions).sort(
    (a, b) => new Date(b).getTime() - new Date(a).getTime()
  );

  const totalsByStatus = transactions.reduce(
    (acc, transaction) => {
      if (!acc[transaction.status]) {
        acc[transaction.status] = 0;
      }
      acc[transaction.status]++;
      return acc;
    },
    {} as Record<string, number>
  );

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filter.searchTerm) count++;
    if (filter.type) count++;
    if (filter.status) count++;
    if (filter.currency) count++;
    if (filter.startDate) count++;
    if (filter.endDate) count++;
    return count;
  }, [filter]);

  const handleExport = () => {
    logger.info('Exporting transactions to CSV');
    try {
      if (filteredTransactions.length === 0) {
        logger.warn('No transactions to export');
        return;
      }

      const headers = [
        'Date',
        'Type',
        'Amount',
        'Currency',
        'Status',
        'Recipient',
        'Sender',
        'Description',
        'Payment Method',
      ];
      const csvContent = [
        headers.join(','),
        ...filteredTransactions.map(t =>
          [
            new Date(t.date).toISOString(),
            t.type,
            t.amount,
            t.currency,
            t.status,
            `"${t.recipient.replace(/"/g, '""')}"`,
            `"${(t.sender || '').replace(/"/g, '""')}"`,
            `"${t.description.replace(/"/g, '""')}"`,
            `"${(t.paymentMethod || '').replace(/"/g, '""')}"`,
          ].join(',')
        ),
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `transactions_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (error) {
      logger.error('Failed to export transactions', error);
    }
  };

  return (
    <div className='min-h-screen bg-background'>
      {/* Header */}
      <div className='bg-card border-b px-4 py-4'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-4'>
            <Button
              variant='ghost'
              size='icon'
              onClick={onBack}
              aria-label='Go back'
              className='min-w-11 min-h-11'
            >
              <ChevronLeft className='w-5 h-5' />
            </Button>
            <div className='flex items-center gap-2'>
              <History className='w-5 h-5 text-primary' />
              <span className='font-semibold'>Transaction History</span>
            </div>
          </div>
          <Button
            variant='ghost'
            size='icon'
            onClick={handleExport}
            aria-label='Export transactions'
            className='min-w-11 min-h-11'
          >
            <Download className='w-4 h-4' />
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className='p-4 bg-card border-b'>
        <div className='grid grid-cols-3 gap-4'>
          <div className='text-center'>
            <div className='text-lg font-semibold text-green-700 dark:text-green-400'>
              {totalsByStatus['completed'] || 0}
            </div>
            <div className='text-xs text-muted-foreground'>Completed</div>
          </div>
          <div className='text-center'>
            <div className='text-lg font-semibold text-yellow-700 dark:text-yellow-400'>
              {totalsByStatus['pending'] || 0}
            </div>
            <div className='text-xs text-muted-foreground'>Pending</div>
          </div>
          <div className='text-center'>
            <div className='text-lg font-semibold text-red-700 dark:text-red-400'>
              {totalsByStatus['failed'] || 0}
            </div>
            <div className='text-xs text-muted-foreground'>Failed</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className='p-4'>
        <TransactionFilter onFilterChange={setFilter} activeFilterCount={activeFilterCount} />
      </div>

      {/* Results Count */}
      {activeFilterCount > 0 && (
        <div className='px-4 pb-2'>
          <p className='text-sm text-gray-600'>
            Showing {filteredTransactions.length} of {transactions.length} transactions
          </p>
        </div>
      )}

      {/* Transactions List */}
      <div className='px-4 pb-4 space-y-6'>
        {sortedDates.length === 0 ? (
          <Card className='border-0 shadow-sm'>
            <CardContent className='p-8 text-center'>
              <History className='w-12 h-12 text-gray-300 mx-auto mb-4' />
              <p className='text-gray-500'>No transactions found</p>
              <p className='text-sm text-gray-400'>Try adjusting your search or filters</p>
            </CardContent>
          </Card>
        ) : (
          sortedDates.map(dateString => (
            <div key={dateString} className='space-y-3'>
              <div className='flex items-center gap-3'>
                <div className='text-sm font-medium text-muted-foreground'>
                  {formatTransactionDate(dateString)}
                </div>
                <div className='flex-1 h-px bg-border' />
              </div>

              <div className='space-y-3'>
                {groupedTransactions[dateString]?.map(transaction => {
                  const StatusIcon = getStatusIcon(
                    transaction.status as 'completed' | 'pending' | 'failed'
                  );
                  const statusColorClass = getStatusColorClass(
                    transaction.status as 'completed' | 'pending' | 'failed'
                  );

                  return (
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
                            <div className='flex-1'>
                              <div className='flex items-center gap-2 mb-1'>
                                <p className='font-medium'>
                                  {transaction.type === 'sent'
                                    ? `To ${transaction.recipient}`
                                    : transaction.type === 'received'
                                      ? `From ${transaction.sender || 'Unknown'}`
                                      : `Request to ${transaction.recipient}`}
                                </p>
                                <Badge className={`${statusColorClass} border-0`}>
                                  {transaction.status.charAt(0).toUpperCase() +
                                    transaction.status.slice(1)}
                                </Badge>
                              </div>
                              <p className='text-sm text-gray-500'>{transaction.description}</p>
                              {transaction.paymentMethod && (
                                <p className='text-xs text-gray-400 mt-1'>
                                  via {transaction.paymentMethod}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className='text-right'>
                            <div className='flex items-center gap-2 mb-1'>
                              <p className='font-semibold'>
                                {transaction.type === 'sent' ? '-' : '+'}
                                {formatCurrency(transaction.amount, transaction.currency)}
                              </p>
                              <StatusIcon className='w-4 h-4' />
                            </div>
                            <p className='text-xs text-gray-400'>
                              {new Date(transaction.date).toLocaleTimeString('en-US', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
