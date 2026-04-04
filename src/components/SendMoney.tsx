import { useState, useEffect, useCallback } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { Badge } from './ui/badge';
import { ChevronLeft, Wallet, Shield, Clock, ArrowRight, Smartphone, Globe, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { logger } from '../utils/logger';
import { paymentsAPI } from '../services/api';
import type { Account } from '../App';
import type { PaymentChannel } from '../types/transaction';

interface SendMoneyProps {
  accounts: Account[];
  onBack: () => void;
  onSuccess: (data: any) => Promise<void> | void;
}

type Step = 'source' | 'recipient' | 'payment-method' | 'confirm' | 'processing';

interface ProcessingState {
  status: 'initiating' | 'waiting' | 'completed' | 'failed';
  instructions?: string;
  transactionId?: number;
  errorMessage?: string;
}

export function SendMoney({ accounts, onBack, onSuccess }: SendMoneyProps) {
  const [step, setStep] = useState<Step>('source');
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [amount, setAmount] = useState('');
  const [recipient, setRecipient] = useState('');
  const [description, setDescription] = useState('');
  const [recipientMethod, setRecipientMethod] = useState('phone');
  const [isProcessing, setIsProcessing] = useState(false);

  // Paynow-specific state
  const [paymentChannel, setPaymentChannel] = useState<PaymentChannel>('ecocash');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [processingState, setProcessingState] = useState<ProcessingState>({
    status: 'initiating',
  });

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
      setStep('payment-method');
    } else if (step === 'payment-method') {
      setStep('confirm');
    }
  };

  // Auto-fill phone number from recipient if sending to phone
  useEffect(() => {
    if (recipientMethod === 'phone' && recipient) {
      setPhoneNumber(recipient);
    }
  }, [recipientMethod, recipient]);

  const handleSend = async () => {
    setIsProcessing(true);
    setStep('processing');
    setProcessingState({ status: 'initiating' });

    try {
      // Step 1: Create a pending transaction
      const transaction = await paymentsAPI.createTransaction({
        transaction_type: 'sent',
        amount: parseFloat(amount),
        currency: selectedAccount?.currency || 'USD',
        recipient,
        description,
        payment_method: paymentChannel,
        account_id: selectedAccount?.id,
      });

      // Step 2: Initiate Paynow payment
      const paynowResponse = await paymentsAPI.initiatePaynowPayment({
        transaction_id: parseInt(transaction.id),
        payment_channel: paymentChannel,
        phone_number: paymentChannel !== 'web' ? phoneNumber : undefined,
      });

      if (paymentChannel === 'web' && paynowResponse.redirect_url) {
        // Store transaction ID for when user returns
        sessionStorage.setItem('pending_paynow_tx', transaction.id);
        window.location.href = paynowResponse.redirect_url;
        return;
      }

      // Mobile flow: show instructions and start polling
      setProcessingState({
        status: 'waiting',
        instructions: paynowResponse.instructions,
        transactionId: paynowResponse.transaction_id,
      });
    } catch (error: any) {
      logger.error('Payment initiation failed', error);
      setProcessingState({
        status: 'failed',
        errorMessage: error?.message || 'Failed to initiate payment',
      });
    }
  };

  // Poll for payment status
  const handlePaymentConfirmed = useCallback(async () => {
    const fee = parseFloat(amount) * 0.01;
    await onSuccess({
      type: 'send',
      amount: parseFloat(amount),
      currency: selectedAccount?.currency || 'USD',
      recipient,
      description,
      account: selectedAccount?.name,
      fee,
      paymentMethod: paymentChannel,
      paymentChannel,
      phoneNumber,
    });
  }, [amount, selectedAccount, recipient, description, paymentChannel, phoneNumber, onSuccess]);

  useEffect(() => {
    if (processingState.status !== 'waiting' || !processingState.transactionId) return;

    const startTime = Date.now();
    const TIMEOUT = 120_000; // 2 minutes
    const INTERVAL = 5_000; // 5 seconds

    const intervalId = setInterval(async () => {
      if (Date.now() - startTime > TIMEOUT) {
        clearInterval(intervalId);
        setProcessingState(prev => ({
          ...prev,
          status: 'failed',
          errorMessage: 'Payment timed out. Please check your phone and try again.',
        }));
        return;
      }

      try {
        const result = await paymentsAPI.pollTransactionStatus(
          processingState.transactionId!
        );

        if (result.paid || result.status === 'completed') {
          clearInterval(intervalId);
          setProcessingState(prev => ({ ...prev, status: 'completed' }));
          await handlePaymentConfirmed();
        } else if (result.status === 'failed') {
          clearInterval(intervalId);
          setProcessingState(prev => ({
            ...prev,
            status: 'failed',
            errorMessage: 'Payment was declined or cancelled.',
          }));
        }
      } catch {
        // Silently retry on network errors
      }
    }, INTERVAL);

    return () => clearInterval(intervalId);
  }, [processingState.status, processingState.transactionId, handlePaymentConfirmed]);

  const handleRetry = () => {
    setIsProcessing(false);
    setStep('payment-method');
    setProcessingState({ status: 'initiating' });
  };

  const renderSourceSelection = () => (
    <div className='space-y-6'>
      <div className='text-center mb-6'>
        <h2 className='text-xl font-semibold mb-2'>Select Payment Source</h2>
        <p className='text-gray-500'>Choose which account to send from</p>
      </div>

      <div className='space-y-3'>
        {accounts.map(account => (
          <Card
            key={account.id}
            className={`cursor-pointer transition-all ${selectedAccount?.id === account.id
              ? 'ring-2 ring-primary border-primary'
              : 'border-gray-200 hover:border-gray-300'
              }`}
            onClick={() => setSelectedAccount(account)}
          >
            <CardContent className='p-4'>
              <div className='flex items-center justify-between'>
                <div className='flex items-center gap-3'>
                  <div
                    className='w-4 h-4 rounded-full'
                    style={{ backgroundColor: account.color }}
                  />
                  <div>
                    <p className='font-medium'>{account.name}</p>
                    <p className='text-sm text-gray-500 capitalize'>{account.type} Account</p>
                  </div>
                </div>
                <div className='text-right'>
                  <p className='font-semibold'>
                    {formatCurrency(account.balance, account.currency)}
                  </p>
                  <Badge variant='secondary' className='text-xs'>
                    {account.currency}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Button className='w-full' onClick={handleContinue} disabled={!selectedAccount}>
        Continue
        <ArrowRight className='w-4 h-4 ml-2' />
      </Button>
    </div>
  );

  const renderRecipientForm = () => (
    <div className='space-y-6'>
      <div className='text-center mb-6'>
        <h2 className='text-xl font-semibold mb-2'>Send Money</h2>
        <p className='text-gray-500'>Enter recipient details and amount</p>
      </div>

      <Card className='border-primary/20 bg-primary/5'>
        <CardContent className='p-4'>
          <div className='flex items-center gap-3'>
            <div
              className='w-4 h-4 rounded-full'
              style={{ backgroundColor: selectedAccount?.color }}
            />
            <div>
              <p className='font-medium'>{selectedAccount?.name}</p>
              <p className='text-sm text-gray-600'>
                Balance:{' '}
                {formatCurrency(selectedAccount?.balance || 0, selectedAccount?.currency || 'USD')}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className='space-y-4'>
        <div>
          <Label htmlFor='amount'>Amount</Label>
          <div className='relative'>
            <Input
              id='amount'
              type='number'
              placeholder='0.00'
              value={amount}
              onChange={e => setAmount(e.target.value)}
              className='text-lg pr-12'
            />
            <div className='absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-gray-500'>
              {selectedAccount?.currency}
            </div>
          </div>
        </div>

        <div>
          <Label htmlFor='recipient-method'>Send to</Label>
          <Select value={recipientMethod} onValueChange={setRecipientMethod}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value='phone'>Phone Number</SelectItem>
              <SelectItem value='account'>Account Number</SelectItem>
              <SelectItem value='email'>Email Address</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor='recipient'>
            {recipientMethod === 'phone'
              ? 'Phone Number'
              : recipientMethod === 'account'
                ? 'Account Number'
                : 'Email Address'}
          </Label>
          <Input
            id='recipient'
            placeholder={
              recipientMethod === 'phone'
                ? '+263 77 123 4567'
                : recipientMethod === 'account'
                  ? '1234567890'
                  : 'email@example.com'
            }
            value={recipient}
            onChange={e => setRecipient(e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor='description'>Description (Optional)</Label>
          <Input
            id='description'
            placeholder="What's this for?"
            value={description}
            onChange={e => setDescription(e.target.value)}
          />
        </div>
      </div>

      <div className='flex gap-3'>
        <Button variant='outline' onClick={() => setStep('source')} className='flex-1'>
          Back
        </Button>
        <Button onClick={handleContinue} disabled={!amount || !recipient} className='flex-1'>
          Continue
          <ArrowRight className='w-4 h-4 ml-2' />
        </Button>
      </div>
    </div>
  );

  const renderPaymentMethodSelection = () => (
    <div className='space-y-6'>
      <div className='text-center mb-6'>
        <h2 className='text-xl font-semibold mb-2'>Payment Method</h2>
        <p className='text-gray-500'>Choose how to pay</p>
      </div>

      <div className='space-y-3'>
        {/* EcoCash */}
        <Card
          className={`cursor-pointer transition-all ${paymentChannel === 'ecocash'
            ? 'ring-2 ring-green-500 border-green-500'
            : 'border-gray-200 hover:border-gray-300'
            }`}
          onClick={() => setPaymentChannel('ecocash')}
        >
          <CardContent className='p-4'>
            <div className='flex items-center gap-3'>
              <div className='w-10 h-10 bg-green-100 rounded-full flex items-center justify-center'>
                <Smartphone className='w-5 h-5 text-green-600' />
              </div>
              <div className='flex-1'>
                <p className='font-medium'>EcoCash</p>
                <p className='text-sm text-gray-500'>Pay with EcoCash mobile money</p>
              </div>
              <Badge variant='secondary' className='bg-green-50 text-green-700'>Popular</Badge>
            </div>
          </CardContent>
        </Card>

        {/* OneMoney */}
        <Card
          className={`cursor-pointer transition-all ${paymentChannel === 'onemoney'
            ? 'ring-2 ring-blue-500 border-blue-500'
            : 'border-gray-200 hover:border-gray-300'
            }`}
          onClick={() => setPaymentChannel('onemoney')}
        >
          <CardContent className='p-4'>
            <div className='flex items-center gap-3'>
              <div className='w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center'>
                <Smartphone className='w-5 h-5 text-blue-600' />
              </div>
              <div className='flex-1'>
                <p className='font-medium'>OneMoney</p>
                <p className='text-sm text-gray-500'>Pay with OneMoney mobile money</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Web Checkout */}
        <Card
          className={`cursor-pointer transition-all ${paymentChannel === 'web'
            ? 'ring-2 ring-purple-500 border-purple-500'
            : 'border-gray-200 hover:border-gray-300'
            }`}
          onClick={() => setPaymentChannel('web')}
        >
          <CardContent className='p-4'>
            <div className='flex items-center gap-3'>
              <div className='w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center'>
                <Globe className='w-5 h-5 text-purple-600' />
              </div>
              <div className='flex-1'>
                <p className='font-medium'>Web Checkout</p>
                <p className='text-sm text-gray-500'>Visa, Mastercard, ZimSwitch</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Phone number for mobile methods */}
      {paymentChannel !== 'web' && (
        <div>
          <Label htmlFor='phone-number'>
            {paymentChannel === 'ecocash' ? 'EcoCash' : 'OneMoney'} Number
          </Label>
          <Input
            id='phone-number'
            placeholder='0771234567'
            value={phoneNumber}
            onChange={e => setPhoneNumber(e.target.value)}
          />
          <p className='text-xs text-gray-500 mt-1'>
            Enter the mobile number registered with {paymentChannel === 'ecocash' ? 'EcoCash' : 'OneMoney'}
          </p>
        </div>
      )}

      <div className='flex gap-3'>
        <Button variant='outline' onClick={() => setStep('recipient')} className='flex-1'>
          Back
        </Button>
        <Button
          onClick={handleContinue}
          disabled={paymentChannel !== 'web' && !phoneNumber}
          className='flex-1'
        >
          Review
          <ArrowRight className='w-4 h-4 ml-2' />
        </Button>
      </div>
    </div>
  );

  const renderConfirmation = () => {
    const fee = parseFloat(amount) * 0.01;
    const total = parseFloat(amount) + fee;
    const channelLabel = paymentChannel === 'ecocash' ? 'EcoCash' : paymentChannel === 'onemoney' ? 'OneMoney' : 'Web Checkout';

    return (
      <div className='space-y-6'>
        <div className='text-center mb-6'>
          <h2 className='text-xl font-semibold mb-2'>Confirm Payment</h2>
          <p className='text-gray-500'>Review your transaction details</p>
        </div>

        <Card className='border-0 shadow-lg'>
          <CardContent className='p-6 space-y-4'>
            <div className='text-center pb-4 border-b'>
              <div className='text-3xl font-bold text-primary mb-1'>
                {formatCurrency(parseFloat(amount), selectedAccount?.currency || 'USD')}
              </div>
              <p className='text-gray-600'>{description || 'Payment'}</p>
            </div>

            <div className='space-y-3'>
              <div className='flex justify-between'>
                <span className='text-gray-600'>From</span>
                <span className='font-medium'>{selectedAccount?.name}</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-gray-600'>To</span>
                <span className='font-medium'>{recipient}</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-gray-600'>Payment method</span>
                <span className='font-medium'>{channelLabel}</span>
              </div>
              {paymentChannel !== 'web' && (
                <div className='flex justify-between'>
                  <span className='text-gray-600'>Phone</span>
                  <span className='font-medium'>{phoneNumber}</span>
                </div>
              )}
              <div className='flex justify-between'>
                <span className='text-gray-600'>Processing fee</span>
                <span className='font-medium'>
                  {formatCurrency(fee, selectedAccount?.currency || 'USD')}
                </span>
              </div>
              <Separator />
              <div className='flex justify-between font-semibold'>
                <span>Total</span>
                <span>{formatCurrency(total, selectedAccount?.currency || 'USD')}</span>
              </div>
            </div>

            <div className='flex items-center gap-2 p-3 bg-green-50 rounded-lg'>
              <Shield className='w-4 h-4 text-green-600' />
              <span className='text-sm text-green-700'>
                Secured by Paynow Zimbabwe
              </span>
            </div>

            <div className='flex items-center gap-2 p-3 bg-blue-50 rounded-lg'>
              <Clock className='w-4 h-4 text-blue-600' />
              <span className='text-sm text-blue-700'>
                {paymentChannel === 'web'
                  ? 'You will be redirected to complete payment'
                  : 'You will receive a prompt on your phone'}
              </span>
            </div>
          </CardContent>
        </Card>

        <div className='flex gap-3'>
          <Button variant='outline' onClick={() => setStep('payment-method')} className='flex-1' disabled={isProcessing}>
            Back
          </Button>
          <Button onClick={handleSend} className='flex-1' disabled={isProcessing}>
            {isProcessing ? 'Processing...' : 'Pay Now'}
          </Button>
        </div>
      </div>
    );
  };

  const renderProcessingScreen = () => {
    const channelLabel = paymentChannel === 'ecocash' ? 'EcoCash' : paymentChannel === 'onemoney' ? 'OneMoney' : 'Web Checkout';

    return (
      <div className='space-y-6'>
        <div className='text-center mb-6'>
          {processingState.status === 'initiating' && (
            <>
              <Loader2 className='w-12 h-12 text-primary animate-spin mx-auto mb-4' />
              <h2 className='text-xl font-semibold mb-2'>Initiating Payment</h2>
              <p className='text-gray-500'>Connecting to {channelLabel}...</p>
            </>
          )}

          {processingState.status === 'waiting' && (
            <>
              <div className='w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4'>
                <Smartphone className='w-8 h-8 text-yellow-600 animate-pulse' />
              </div>
              <h2 className='text-xl font-semibold mb-2'>Waiting for Approval</h2>
              <p className='text-gray-500'>
                {processingState.instructions || 'Check your phone to approve the payment'}
              </p>
            </>
          )}

          {processingState.status === 'completed' && (
            <>
              <CheckCircle2 className='w-12 h-12 text-green-500 mx-auto mb-4' />
              <h2 className='text-xl font-semibold mb-2'>Payment Confirmed!</h2>
              <p className='text-gray-500'>Redirecting to confirmation...</p>
            </>
          )}

          {processingState.status === 'failed' && (
            <>
              <div className='w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4'>
                <AlertCircle className='w-8 h-8 text-red-600' />
              </div>
              <h2 className='text-xl font-semibold mb-2'>Payment Failed</h2>
              <p className='text-gray-500'>
                {processingState.errorMessage || 'Something went wrong. Please try again.'}
              </p>
            </>
          )}
        </div>

        {processingState.status === 'waiting' && (
          <Card className='bg-blue-50 border-blue-200'>
            <CardContent className='p-4'>
              <div className='flex items-start gap-3'>
                <Clock className='w-5 h-5 text-blue-600 mt-0.5' />
                <div>
                  <p className='font-medium text-blue-900'>Waiting for confirmation</p>
                  <p className='text-sm text-blue-700 mt-1'>
                    Open your {channelLabel} app or dial the USSD code on your phone to approve.
                    This will timeout after 2 minutes.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {processingState.status === 'waiting' && (
          <div className='text-center'>
            <p className='text-sm text-gray-500 mb-2'>
              Sending {formatCurrency(parseFloat(amount), selectedAccount?.currency || 'USD')} to {recipient}
            </p>
          </div>
        )}

        {processingState.status === 'failed' && (
          <div className='flex gap-3'>
            <Button variant='outline' onClick={onBack} className='flex-1'>
              Cancel
            </Button>
            <Button onClick={handleRetry} className='flex-1'>
              Try Again
            </Button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className='min-h-screen bg-gray-50'>
      {/* Header */}
      <div className='bg-white border-b px-4 py-4'>
        <div className='flex items-center gap-4'>
          <Button variant='ghost' size='sm' onClick={step === 'processing' ? undefined : onBack} disabled={step === 'processing'}>
            <ChevronLeft className='w-5 h-5' />
          </Button>
          <div className='flex items-center gap-2'>
            <Wallet className='w-5 h-5 text-primary' />
            <span className='font-semibold'>Send Money</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className='p-4'>
        {step === 'source' && renderSourceSelection()}
        {step === 'recipient' && renderRecipientForm()}
        {step === 'payment-method' && renderPaymentMethodSelection()}
        {step === 'confirm' && renderConfirmation()}
        {step === 'processing' && renderProcessingScreen()}
      </div>
    </div>
  );
}
