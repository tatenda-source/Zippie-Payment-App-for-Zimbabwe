/**
 * Currency Converter Component
 * Shows live currency conversion preview
 */

import { useState, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ArrowRightLeft, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { currencyService } from '../services/currencyService';
import { formatCurrency } from '../utils/currency';

interface CurrencyConverterProps {
    defaultAmount?: number;
    defaultFrom?: 'USD' | 'ZWL';
    defaultTo?: 'USD' | 'ZWL';
    onConvert?: (amount: number, from: 'USD' | 'ZWL', to: 'USD' | 'ZWL', converted: number) => void;
}

export function CurrencyConverter({
    defaultAmount = 0,
    defaultFrom = 'USD',
    defaultTo = 'ZWL',
    onConvert,
}: CurrencyConverterProps) {
    const [amount, setAmount] = useState(defaultAmount);
    const [fromCurrency, setFromCurrency] = useState<'USD' | 'ZWL'>(defaultFrom);
    const [toCurrency, setToCurrency] = useState<'USD' | 'ZWL'>(defaultTo);
    const [converted, setConverted] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [lastUpdated, setLastUpdated] = useState('');

    useEffect(() => {
        const rates = currencyService.getRates();
        setLastUpdated(new Date(rates.lastUpdated).toLocaleTimeString());
    }, []);

    useEffect(() => {
        const result = currencyService.convert(amount, fromCurrency, toCurrency);
        setConverted(result);

        if (onConvert) {
            onConvert(amount, fromCurrency, toCurrency, result);
        }
    }, [amount, fromCurrency, toCurrency, onConvert]);

    const handleSwapCurrencies = () => {
        setFromCurrency(toCurrency);
        setToCurrency(fromCurrency);
    };

    const handleRefreshRates = async () => {
        setIsRefreshing(true);
        try {
            const rates = await currencyService.fetchRates();
            setLastUpdated(new Date(rates.lastUpdated).toLocaleTimeString());

            // Recalculate conversion with new rates
            const result = currencyService.convert(amount, fromCurrency, toCurrency);
            setConverted(result);
        } finally {
            setIsRefreshing(false);
        }
    };

    const rate = currencyService.getRate(fromCurrency, toCurrency);

    return (
        <Card className='border-0 shadow-sm'>
            <CardContent className='p-4 space-y-4'>
                <div className='flex items-center justify-between'>
                    <h3 className='font-semibold text-gray-900'>Currency Converter</h3>
                    <Button
                        variant='ghost'
                        size='sm'
                        onClick={handleRefreshRates}
                        disabled={isRefreshing}
                        className='gap-2'
                    >
                        <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                </div>

                {/* From Currency */}
                <div className='space-y-2'>
                    <Label>From</Label>
                    <div className='flex gap-2'>
                        <Input
                            type='number'
                            value={amount}
                            onChange={e => setAmount(parseFloat(e.target.value) || 0)}
                            placeholder='0.00'
                            className='flex-1'
                        />
                        <Select value={fromCurrency} onValueChange={(v: 'USD' | 'ZWL') => setFromCurrency(v)}>
                            <SelectTrigger className='w-24'>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value='USD'>USD</SelectItem>
                                <SelectItem value='ZWL'>ZWL</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                {/* Swap Button */}
                <div className='flex justify-center'>
                    <Button
                        variant='outline'
                        size='sm'
                        onClick={handleSwapCurrencies}
                        className='rounded-full w-10 h-10 p-0'
                    >
                        <ArrowRightLeft className='w-4 h-4' />
                    </Button>
                </div>

                {/* To Currency */}
                <div className='space-y-2'>
                    <Label>To</Label>
                    <div className='flex gap-2'>
                        <Input
                            type='text'
                            value={formatCurrency(converted, toCurrency)}
                            readOnly
                            className='flex-1 bg-gray-50'
                        />
                        <Select value={toCurrency} onValueChange={(v: 'USD' | 'ZWL') => setToCurrency(v)}>
                            <SelectTrigger className='w-24'>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value='USD'>USD</SelectItem>
                                <SelectItem value='ZWL'>ZWL</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                {/* Exchange Rate Info */}
                <div className='pt-3 border-t space-y-1'>
                    <div className='flex justify-between text-sm'>
                        <span className='text-gray-600'>Exchange Rate:</span>
                        <span className='font-medium'>1 {fromCurrency} = {rate.toLocaleString()} {toCurrency}</span>
                    </div>
                    <div className='flex justify-between text-xs text-gray-500'>
                        <span>Last updated:</span>
                        <span>{lastUpdated}</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
