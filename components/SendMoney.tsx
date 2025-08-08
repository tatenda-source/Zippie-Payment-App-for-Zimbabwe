import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { Badge } from './ui/badge';
import { 
  ChevronLeft, 
  Wallet,
  User,
  MessageSquare,
  Shield,
  Clock,
  ArrowRight
} from 'lucide-react';
import type { Account } from '../App';

interface SendMoneyProps {
  accounts: Account[];
  onBack: () => void;
  onSuccess: (data: any) => void;
}

export function SendMoney({ accounts, onBack, onSuccess }: SendMoneyProps) {
  const [step, setStep] = useState<'source' | 'recipient' | 'confirm'>('source');
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [amount, setAmount] = useState('');
  const [recipient, setRecipient] = useState('');
  const [description, setDescription] = useState('');
  const [recipientMethod, setRecipientMethod] = useState('phone');

  const formatCurrency = (amount: number, currency: 'USD' | 'ZWL') => {
    if (currency === 'USD') {
      return `$${amount.toFixed(2)}`;
    }
    return `ZWL$${amount.toLocaleString()}`;
  };

  const handleContinue = () => {
    if (step === 'source' && selectedAccount) {
      setStep('recipient');
    } else if (step === 'recipient' && amount && recipient) {
      setStep('confirm');
    }
  };

  const handleSend = () => {
    const transactionData = {
      type: 'send',
      amount: parseFloat(amount),
      currency: selectedAccount?.currency,
      recipient,
      description,
      account: selectedAccount?.name,
      fee: parseFloat(amount) * 0.01 // 1% fee
    };
    onSuccess(transactionData);
  };

  const renderSourceSelection = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-xl font-semibold mb-2">Select Payment Source</h2>
        <p className="text-gray-500">Choose which account to send from</p>
      </div>

      <div className="space-y-3">
        {accounts.map((account) => (
          <Card
            key={account.id}
            className={`cursor-pointer transition-all ${
              selectedAccount?.id === account.id 
                ? 'ring-2 ring-primary border-primary' 
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setSelectedAccount(account)}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: account.color }}
                  />
                  <div>
                    <p className="font-medium">{account.name}</p>
                    <p className="text-sm text-gray-500 capitalize">{account.type} Account</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold">{formatCurrency(account.balance, account.currency)}</p>
                  <Badge variant="secondary" className="text-xs">
                    {account.currency}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Button 
        className="w-full" 
        onClick={handleContinue}
        disabled={!selectedAccount}
      >
        Continue
        <ArrowRight className="w-4 h-4 ml-2" />
      </Button>
    </div>
  );

  const renderRecipientForm = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-xl font-semibold mb-2">Send Money</h2>
        <p className="text-gray-500">Enter recipient details and amount</p>
      </div>

      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div 
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: selectedAccount?.color }}
            />
            <div>
              <p className="font-medium">{selectedAccount?.name}</p>
              <p className="text-sm text-gray-600">
                Balance: {formatCurrency(selectedAccount?.balance || 0, selectedAccount?.currency || 'USD')}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <div>
          <Label htmlFor="amount">Amount</Label>
          <div className="relative">
            <Input
              id="amount"
              type="number"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="text-lg pr-12"
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-gray-500">
              {selectedAccount?.currency}
            </div>
          </div>
        </div>

        <div>
          <Label htmlFor="recipient-method">Send to</Label>
          <Select value={recipientMethod} onValueChange={setRecipientMethod}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="phone">Phone Number</SelectItem>
              <SelectItem value="account">Account Number</SelectItem>
              <SelectItem value="email">Email Address</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="recipient">
            {recipientMethod === 'phone' ? 'Phone Number' : 
             recipientMethod === 'account' ? 'Account Number' : 'Email Address'}
          </Label>
          <Input
            id="recipient"
            placeholder={
              recipientMethod === 'phone' ? '+263 77 123 4567' : 
              recipientMethod === 'account' ? '1234567890' : 'email@example.com'
            }
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor="description">Description (Optional)</Label>
          <Input
            id="description"
            placeholder="What's this for?"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
      </div>

      <div className="flex gap-3">
        <Button variant="outline" onClick={() => setStep('source')} className="flex-1">
          Back
        </Button>
        <Button 
          onClick={handleContinue} 
          disabled={!amount || !recipient}
          className="flex-1"
        >
          Review
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );

  const renderConfirmation = () => {
    const fee = parseFloat(amount) * 0.01;
    const total = parseFloat(amount) + fee;

    return (
      <div className="space-y-6">
        <div className="text-center mb-6">
          <h2 className="text-xl font-semibold mb-2">Confirm Payment</h2>
          <p className="text-gray-500">Review your transaction details</p>
        </div>

        <Card className="border-0 shadow-lg">
          <CardContent className="p-6 space-y-4">
            <div className="text-center pb-4 border-b">
              <div className="text-3xl font-bold text-primary mb-1">
                {formatCurrency(parseFloat(amount), selectedAccount?.currency || 'USD')}
              </div>
              <p className="text-gray-600">{description || 'Payment'}</p>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">From</span>
                <span className="font-medium">{selectedAccount?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">To</span>
                <span className="font-medium">{recipient}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Processing fee</span>
                <span className="font-medium">
                  {formatCurrency(fee, selectedAccount?.currency || 'USD')}
                </span>
              </div>
              <Separator />
              <div className="flex justify-between font-semibold">
                <span>Total</span>
                <span>{formatCurrency(total, selectedAccount?.currency || 'USD')}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
              <Shield className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-700">
                This transaction is protected and encrypted
              </span>
            </div>

            <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-blue-700">
                Estimated processing time: Instant
              </span>
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button variant="outline" onClick={() => setStep('recipient')} className="flex-1">
            Back
          </Button>
          <Button onClick={handleSend} className="flex-1">
            Send Money
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ChevronLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center gap-2">
            <Wallet className="w-5 h-5 text-primary" />
            <span className="font-semibold">Send Money</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {step === 'source' && renderSourceSelection()}
        {step === 'recipient' && renderRecipientForm()}
        {step === 'confirm' && renderConfirmation()}
      </div>
    </div>
  );
}