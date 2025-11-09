import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { 
  Check,
  Download,
  Share2,
  Home,
  MessageSquare,
  Copy,
  Calendar,
  User,
  CreditCard,
  ArrowDownLeft
} from 'lucide-react';

interface PaymentSuccessProps {
  data: any;
  onBack: () => void;
}

export function PaymentSuccess({ data, onBack }: PaymentSuccessProps) {
  const [copied, setCopied] = useState(false);

  const formatCurrency = (amount: number, currency: 'USD' | 'ZWL') => {
    if (currency === 'USD') {
      return `$${amount?.toFixed(2)}`;
    }
    return `ZWL$${amount?.toLocaleString()}`;
  };

  const copyToClipboard = () => {
    if (data.link) {
      navigator.clipboard.writeText(data.link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const shareViaWhatsApp = () => {
    let message = '';
    if (data.type === 'request') {
      message = `Hi! I'm requesting ${formatCurrency(data.amount, data.currency)} for ${data.description}. Pay here: ${data.link}`;
    } else {
      message = `Payment confirmation: I sent ${formatCurrency(data.amount, data.currency)} for ${data.description}. Transaction ID: TXN${Date.now().toString().slice(-6)}`;
    }
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  const generateReceiptData = () => {
    const transactionId = `TXN${Date.now().toString().slice(-6)}`;
    const timestamp = new Date().toLocaleString();
    
    return {
      transactionId,
      timestamp,
      type: data.type,
      amount: data.amount,
      currency: data.currency,
      description: data.description,
      recipient: data.recipient,
      account: data.account,
      fee: data.fee || 0
    };
  };

  const receiptData = generateReceiptData();

  const renderSuccessIcon = () => {
    if (data.type === 'request') {
      return (
        <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <ArrowDownLeft className="w-12 h-12 text-green-600" />
        </div>
      );
    } else {
      return (
        <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse">
          <Check className="w-12 h-12 text-green-600" />
        </div>
      );
    }
  };

  const renderSuccessMessage = () => {
    if (data.type === 'request') {
      return {
        title: 'Payment Request Created! 🎉',
        subtitle: 'Your request is ready to share'
      };
    } else {
      return {
        title: 'Payment Sent! 🎉',
        subtitle: 'Your money is on its way'
      };
    }
  };

  const successMessage = renderSuccessMessage();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Success Animation */}
      <div className="bg-white px-4 py-8 text-center">
        {renderSuccessIcon()}
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {successMessage.title}
        </h1>
        <p className="text-gray-600">{successMessage.subtitle}</p>
      </div>

      {/* Transaction Details */}
      <div className="p-4 space-y-4">
        <Card className="border-0 shadow-lg">
          <CardContent className="p-6 space-y-4">
            <div className="text-center pb-4 border-b">
              <div className="text-3xl font-bold text-primary mb-1">
                {formatCurrency(data.amount, data.currency)}
              </div>
              <p className="text-gray-600">{data.description}</p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">Date & Time</span>
                </div>
                <span className="font-medium">{receiptData.timestamp}</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">
                    {data.type === 'request' ? 'Requesting from' : 'Sent to'}
                  </span>
                </div>
                <span className="font-medium">{data.recipient || 'Multiple recipients'}</span>
              </div>

              {data.account && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CreditCard className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-600">
                      {data.type === 'request' ? 'Request via' : 'Paid from'}
                    </span>
                  </div>
                  <span className="font-medium">{data.account}</span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-gray-600">Transaction ID</span>
                <span className="font-medium font-mono text-sm">{receiptData.transactionId}</span>
              </div>

              {data.fee && data.fee > 0 && (
                <>
                  <Separator />
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Processing fee</span>
                    <span>{formatCurrency(data.fee, data.currency)}</span>
                  </div>
                  <div className="flex items-center justify-between font-semibold">
                    <span>Total</span>
                    <span>{formatCurrency(data.amount + data.fee, data.currency)}</span>
                  </div>
                </>
              )}
            </div>

            <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg border border-green-200">
              <Check className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-700">
                {data.type === 'request' 
                  ? 'Request created and ready to share'
                  : 'Payment processed successfully'
                }
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Payment Link (for requests) */}
        {data.type === 'request' && data.link && (
          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">Payment Link</span>
                <Badge variant="secondary" className="bg-accent/10 text-accent">
                  Active
                </Badge>
              </div>
              <div className="flex gap-2">
                <div className="flex-1 p-3 bg-gray-50 rounded border text-sm text-gray-600 break-all">
                  {data.link}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyToClipboard}
                  className="shrink-0"
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recipients (for requests with multiple recipients) */}
        {data.type === 'request' && data.recipients && data.recipients.length > 0 && (
          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="text-sm font-medium text-gray-600 mb-2">
                Recipients ({data.recipients.length})
              </div>
              <div className="space-y-2">
                {data.recipients.map((recipient: string, index: number) => (
                  <div key={index} className="flex items-center gap-2 text-sm">
                    <User className="w-4 h-4 text-gray-400" />
                    <span>{recipient}</span>
                    <Badge variant="outline" className="ml-auto text-xs">
                      Pending
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="space-y-3 pt-4">
          <Button onClick={shareViaWhatsApp} className="w-full bg-green-600 hover:bg-green-700">
            <MessageSquare className="w-4 h-4 mr-2" />
            Share via WhatsApp
          </Button>

          <div className="grid grid-cols-2 gap-3">
            <Button variant="outline" className="flex-1">
              <Download className="w-4 h-4 mr-2" />
              Receipt
            </Button>
            <Button variant="outline" className="flex-1">
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
          </div>

          <Button onClick={onBack} className="w-full" variant="secondary">
            <Home className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </div>

        {/* Additional Info */}
        <Card className="border-0 bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <div className="text-center space-y-2">
              <p className="text-sm font-medium text-blue-800">
                {data.type === 'request' 
                  ? 'What happens next?'
                  : 'Need help?'
                }
              </p>
              <p className="text-sm text-blue-700">
                {data.type === 'request' 
                  ? 'Recipients will receive your request and can pay instantly using the link or QR code.'
                  : 'If you have any questions about this transaction, contact our support team.'
                }
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}