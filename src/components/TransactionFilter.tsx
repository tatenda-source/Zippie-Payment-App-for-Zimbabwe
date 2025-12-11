/**
 * Transaction Filter Component
 * Provides filtering controls for transaction history
 */

import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Search, X, Filter } from 'lucide-react';
import type { TransactionFilter as FilterType } from '../types/transaction';

interface TransactionFilterProps {
    onFilterChange: (filter: FilterType) => void;
    activeFilterCount: number;
}

export function TransactionFilter({ onFilterChange, activeFilterCount }: TransactionFilterProps) {
    const [showFilters, setShowFilters] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [type, setType] = useState<string>('all');
    const [status, setStatus] = useState<string>('all');
    const [currency, setCurrency] = useState<string>('all');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const applyFilters = () => {
        const filter: FilterType = {
            searchTerm: searchTerm || undefined,
            type: type !== 'all' ? (type as 'sent' | 'received' | 'request') : undefined,
            status: status !== 'all' ? (status as 'completed' | 'pending' | 'failed') : undefined,
            currency: currency !== 'all' ? (currency as 'USD' | 'ZWL') : undefined,
            startDate: startDate || undefined,
            endDate: endDate || undefined,
        };
        onFilterChange(filter);
    };

    const clearFilters = () => {
        setSearchTerm('');
        setType('all');
        setStatus('all');
        setCurrency('all');
        setStartDate('');
        setEndDate('');
        onFilterChange({});
    };

    const handleSearchChange = (value: string) => {
        setSearchTerm(value);
        // Auto-apply search as user types
        const filter: FilterType = {
            searchTerm: value || undefined,
            type: type !== 'all' ? (type as 'sent' | 'received' | 'request') : undefined,
            status: status !== 'all' ? (status as 'completed' | 'pending' | 'failed') : undefined,
            currency: currency !== 'all' ? (currency as 'USD' | 'ZWL') : undefined,
            startDate: startDate || undefined,
            endDate: endDate || undefined,
        };
        onFilterChange(filter);
    };

    return (
        <div className='space-y-3'>
            {/* Search Bar */}
            <div className='relative'>
                <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400' />
                <Input
                    type='text'
                    placeholder='Search transactions...'
                    value={searchTerm}
                    onChange={e => handleSearchChange(e.target.value)}
                    className='pl-10 pr-10'
                />
                {searchTerm && (
                    <button
                        onClick={() => handleSearchChange('')}
                        className='absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600'
                    >
                        <X className='w-4 h-4' />
                    </button>
                )}
            </div>

            {/* Filter Toggle Button */}
            <div className='flex items-center justify-between'>
                <Button
                    variant='outline'
                    size='sm'
                    onClick={() => setShowFilters(!showFilters)}
                    className='gap-2'
                >
                    <Filter className='w-4 h-4' />
                    Filters
                    {activeFilterCount > 0 && (
                        <span className='ml-1 px-2 py-0.5 bg-primary text-primary-foreground text-xs rounded-full'>
                            {activeFilterCount}
                        </span>
                    )}
                </Button>
                {activeFilterCount > 0 && (
                    <Button variant='ghost' size='sm' onClick={clearFilters}>
                        Clear All
                    </Button>
                )}
            </div>

            {/* Filter Panel */}
            {showFilters && (
                <Card className='border-0 shadow-sm'>
                    <CardContent className='p-4 space-y-4'>
                        {/* Type Filter */}
                        <div className='space-y-2'>
                            <Label>Transaction Type</Label>
                            <Select value={type} onValueChange={setType}>
                                <SelectTrigger>
                                    <SelectValue placeholder='All types' />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value='all'>All Types</SelectItem>
                                    <SelectItem value='sent'>Sent</SelectItem>
                                    <SelectItem value='received'>Received</SelectItem>
                                    <SelectItem value='request'>Request</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Status Filter */}
                        <div className='space-y-2'>
                            <Label>Status</Label>
                            <Select value={status} onValueChange={setStatus}>
                                <SelectTrigger>
                                    <SelectValue placeholder='All statuses' />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value='all'>All Statuses</SelectItem>
                                    <SelectItem value='completed'>Completed</SelectItem>
                                    <SelectItem value='pending'>Pending</SelectItem>
                                    <SelectItem value='failed'>Failed</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Currency Filter */}
                        <div className='space-y-2'>
                            <Label>Currency</Label>
                            <Select value={currency} onValueChange={setCurrency}>
                                <SelectTrigger>
                                    <SelectValue placeholder='All currencies' />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value='all'>All Currencies</SelectItem>
                                    <SelectItem value='USD'>USD</SelectItem>
                                    <SelectItem value='ZWL'>ZWL</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Date Range */}
                        <div className='grid grid-cols-2 gap-3'>
                            <div className='space-y-2'>
                                <Label>From Date</Label>
                                <Input
                                    type='date'
                                    value={startDate}
                                    onChange={e => setStartDate(e.target.value)}
                                />
                            </div>
                            <div className='space-y-2'>
                                <Label>To Date</Label>
                                <Input
                                    type='date'
                                    value={endDate}
                                    onChange={e => setEndDate(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Apply Button */}
                        <Button onClick={applyFilters} className='w-full'>
                            Apply Filters
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
