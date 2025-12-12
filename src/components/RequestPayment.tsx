import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import {
  ChevronLeft,
  ArrowDownLeft,
  QrCode,
  Share2,
  MessageSquare,
  Copy,
  Check,
  ArrowRight,
  Users,
  User,
} from 'lucide-react';

interface RequestPaymentProps {
  onBack: () => void;
  onSuccess: (data: any) => Promise<void> | void;
}

export function RequestPayment({ onBack, onSuccess }: RequestPaymentProps) {
  const [step, setStep] = useState<'details' | 'recipients' | 'preview'>('details');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState<'USD' | 'ZWL'>('USD');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [recipients, setRecipients] = useState<string[]>(['']);
  const [copied, setCopied] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const paymentLink = `https://zippie.co.zw/pay/${Math.random().toString(36).substr(2, 9)}`;

  const formatCurrency = (amount: number, currency: 'USD' | 'ZWL') => {
    if (currency === 'USD') {
      return `$${amount.toFixed(2)}`;
    }
    return `ZWL$${amount.toLocaleString()}`;
  };

  const addRecipient = () => {
    setRecipients([...recipients, '']);
  };

  const updateRecipient = (index: number, value: string) => {
    const newRecipients = [...recipients];
    newRecipients[index] = value;
    setRecipients(newRecipients);
  };

  const removeRecipient = (index: number) => {
    if (recipients.length > 1) {
      const newRecipients = recipients.filter((_, i) => i !== index);
      setRecipients(newRecipients);
    }
  };

  const handleContinue = () => {
    if (step === 'details' && amount && description) {
      setStep('recipients');
    } else if (step === 'recipients') {
      setStep('preview');
    }
  };

  const handleCreateRequest = async () => {
    setIsProcessing(true);
    try {
      const requestData = {
        type: 'request',
        amount: parseFloat(amount),
        currency,
        description,
        recipients: recipients.filter(r => r.trim() !== ''),
        dueDate,
        link: paymentLink,
        qrCode: true,
      };
      await onSuccess(requestData);
    } catch (error) {
      console.error('Request failed', error);
      setIsProcessing(false);
    }
  };

  // ... (keeping helper functions as they are not changed in this block replacement target)

  const copyToClipboard = () => {
    navigator.clipboard.writeText(paymentLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareViaWhatsApp = () => {
    const message = `Hi! I'm requesting ${formatCurrency(parseFloat(amount), currency)} for ${description}. Pay here: ${paymentLink}`;
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  const renderDetailsForm = () => (
    <div className='space-y-6'>
      {/* ... keeping content */}
      <div className='text-center mb-6'>
        <h2 className='text-xl font-semibold mb-2'>Request Payment</h2>
        <p className='text-gray-500'>Enter the amount and details</p>
      </div>

      <div className='space-y-4'>
        <div>
          <Label htmlFor='amount'>Amount</Label>
          <div className='flex gap-2'>
            <div className='relative flex-1'>
              <Input
                id='amount'
                type='number'
                placeholder='0.00'
                value={amount}
                onChange={e => setAmount(e.target.value)}
                className='text-lg pr-16'
              />
              <div className='absolute right-3 top-1/2 transform -translate-y-1/2'>
                <select
                  value={currency}
                  onChange={e => setCurrency(e.target.value as 'USD' | 'ZWL')}
                  className='bg-transparent text-sm font-medium border-0 focus:outline-none'
                >
                  <option value='USD'>USD</option>
                  <option value='ZWL'>ZWL</option>
                </select>
              </div>
            </div>
          </div>
          {amount && (
            <p className='text-sm text-gray-500 mt-1'>
              {currency === 'USD'
                ? `≈ ZWL$${(parseFloat(amount) * 25000).toLocaleString()}`
                : `≈ $${(parseFloat(amount) / 25000).toFixed(2)}`}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor='description'>What's this for?</Label>
          <Input
            id='description'
            placeholder='e.g., Dinner split, Bus fare, Airtime'
            value={description}
            onChange={e => setDescription(e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor='due-date'>Due Date (Optional)</Label>
          <Input
            id='due-date'
            type='date'
            value={dueDate}
            onChange={e => setDueDate(e.target.value)}
            min={new Date().toISOString().split('T')[0]}
          />
        </div>

        <div>
          <Label htmlFor='note'>Additional Note (Optional)</Label>
          <Textarea
            id='note'
            placeholder='Any additional details...'
            rows={3}
            className='resize-none'
          />
        </div>
      </div>

      <Button className='w-full' onClick={handleContinue} disabled={!amount || !description}>
        Continue
        <ArrowRight className='w-4 h-4 ml-2' />
      </Button>
    </div>
  );

  const renderRecipientsForm = () => (
    <div className='space-y-6'>
      {/* ... keeping content */}
      <div className='text-center mb-6'>
        <h2 className='text-xl font-semibold mb-2'>Who should pay?</h2>
        <p className='text-gray-500'>Add recipients for this request</p>
      </div>

      <div className='space-y-4'>
        {recipients.map((recipient, index) => (
          <div key={index} className='flex gap-2'>
            <div className='relative flex-1'>
              <User className='w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2' />
              <Input
                placeholder='Phone number or email'
                value={recipient}
                onChange={e => updateRecipient(index, e.target.value)}
                className='pl-10'
              />
            </div>
            {recipients.length > 1 && (
              <Button
                variant='outline'
                size='sm'
                onClick={() => removeRecipient(index)}
                className='px-3'
              >
                ×
              </Button>
            )}
          </div>
        ))}

        <Button variant='outline' onClick={addRecipient} className='w-full'>
          <Users className='w-4 h-4 mr-2' />
          Add Another Person
        </Button>
      </div>

      <Card className='bg-yellow-50 border-yellow-200'>
        <CardContent className='p-4'>
          <div className='flex items-start gap-3'>
            <MessageSquare className='w-5 h-5 text-yellow-600 mt-0.5' />
            <div>
              <p className='font-medium text-yellow-800'>Tip</p>
              <p className='text-sm text-yellow-700'>
                You can also share the payment link later via WhatsApp or SMS to reach more people.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className='flex gap-3'>
        <Button variant='outline' onClick={() => setStep('details')} className='flex-1'>
          Back
        </Button>
        <Button onClick={handleContinue} className='flex-1'>
          Preview
          <ArrowRight className='w-4 h-4 ml-2' />
        </Button>
      </div>
    </div>
  );

  const renderPreview = () => (
    <div className='space-y-6'>
      <div className='text-center mb-6'>
        <h2 className='text-xl font-semibold mb-2'>Payment Request</h2>
        <p className='text-gray-500'>Review and share your request</p>
      </div>

      {/* Request Preview */}
      <Card className='border-0 shadow-lg bg-gradient-to-br from-primary/5 to-accent/5'>
        <CardContent className='p-6 text-center space-y-4'>
          <div className='w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto'>
            <ArrowDownLeft className='w-8 h-8 text-primary' />
          </div>

          <div>
            <h3 className='font-semibold text-gray-600'>You're requesting</h3>
            <div className='text-3xl font-bold text-primary mb-1'>
              {formatCurrency(parseFloat(amount), currency)}
            </div>
            <p className='text-gray-600'>{description}</p>
          </div>

          {dueDate && (
            <Badge variant='outline' className='bg-white'>
              Due: {new Date(dueDate).toLocaleDateString()}
            </Badge>
          )}
        </CardContent>
      </Card>

      {/* QR Code */}
      <Card>
        <CardContent className='p-6 text-center'>
          <div className='w-32 h-32 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4'>
            <QrCode className='w-16 h-16 text-gray-400' />
          </div>
          <p className='text-sm text-gray-600'>Scan to pay instantly</p>
        </CardContent>
      </Card>

      {/* Payment Link */}
      <Card>
        <CardContent className='p-4'>
          <Label className='text-sm font-medium text-gray-600'>Payment Link</Label>
          <div className='flex gap-2 mt-2'>
            <div className='flex-1 p-3 bg-gray-50 rounded border text-sm text-gray-600 break-all'>
              {paymentLink}
            </div>
            <Button variant='outline' size='sm' onClick={copyToClipboard} className='shrink-0'>
              {copied ? <Check className='w-4 h-4' /> : <Copy className='w-4 h-4' />}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recipients */}
      {recipients.filter(r => r.trim() !== '').length > 0 && (
        <Card>
          <CardContent className='p-4'>
            <Label className='text-sm font-medium text-gray-600'>Recipients</Label>
            <div className='mt-2 space-y-2'>
              {recipients
                .filter(r => r.trim() !== '')
                .map((recipient, index) => (
                  <div key={index} className='flex items-center gap-2 text-sm'>
                    <User className='w-4 h-4 text-gray-400' />
                    <span>{recipient}</span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className='space-y-3'>
        <Button onClick={shareViaWhatsApp} className='w-full bg-green-600 hover:bg-green-700'>
          <MessageSquare className='w-4 h-4 mr-2' />
          Share via WhatsApp
        </Button>

        <Button variant='outline' className='w-full'>
          <Share2 className='w-4 h-4 mr-2' />
          Share Link
        </Button>
      </div>

      <div className='flex gap-3'>
        <Button variant='outline' onClick={() => setStep('recipients')} className='flex-1' disabled={isProcessing}>
          Back
        </Button>
        <Button onClick={handleCreateRequest} className='flex-1' disabled={isProcessing}>
          {isProcessing ? 'Creating...' : 'Create Request'}
        </Button>
      </div>
    </div>
  );

  return (
    <div className='min-h-screen bg-gray-50'>
      {/* Header */}
      <div className='bg-white border-b px-4 py-4'>
        <div className='flex items-center gap-4'>
          <Button variant='ghost' size='sm' onClick={onBack}>
            <ChevronLeft className='w-5 h-5' />
          </Button>
          <div className='flex items-center gap-2'>
            <ArrowDownLeft className='w-5 h-5 text-primary' />
            <span className='font-semibold'>Request Payment</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className='p-4'>
        {step === 'details' && renderDetailsForm()}
        {step === 'recipients' && renderRecipientsForm()}
        {step === 'preview' && renderPreview()}
      </div>
    </div>
  );
}
