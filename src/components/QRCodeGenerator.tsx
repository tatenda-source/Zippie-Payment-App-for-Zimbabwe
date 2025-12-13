/**
 * QR Code Generator Component
 * Generates QR codes for payment requests and links
 */

import { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Copy, Check, Download } from 'lucide-react';
import { logger } from '../utils/logger';

interface QRCodeGeneratorProps {
    data: string;
    title?: string;
    description?: string;
    size?: number;
}

export function QRCodeGenerator({
    data,
    title = 'Payment Request',
    description,
    size = 200,
}: QRCodeGeneratorProps) {
    const [copied, setCopied] = useState(false);

    // Generate QR code using a simple SVG-based approach
    // In production, you might use a library like qrcode.react or qrcode
    const generateQRCodeSVG = (text: string, size: number) => {
        // This is a simplified placeholder
        // In a real implementation, use a proper QR code library


        return `
      <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <rect width="${size}" height="${size}" fill="white"/>
        <text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="12" fill="black">
          QR Code
        </text>
        <text x="50%" y="60%" text-anchor="middle" dy=".3em" font-size="8" fill="gray">
          ${text.substring(0, 20)}...
        </text>
      </svg>
    `;
    };

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(data);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            logger.error('Failed to copy', error);
        }
    };

    const handleDownload = () => {
        const svg = generateQRCodeSVG(data, size);
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'payment-qr-code.svg';
        link.click();
        URL.revokeObjectURL(url);
    };

    return (
        <Card className='border-0 shadow-sm'>
            <CardContent className='p-6 space-y-4'>
                <div className='text-center'>
                    <h3 className='font-semibold text-gray-900 mb-1'>{title}</h3>
                    {description && <p className='text-sm text-gray-600'>{description}</p>}
                </div>

                {/* QR Code Display */}
                <div className='flex justify-center'>
                    <div
                        className='bg-white p-4 rounded-lg border-2 border-gray-200'
                        dangerouslySetInnerHTML={{ __html: generateQRCodeSVG(data, size) }}
                    />
                </div>

                {/* Payment Link */}
                <div className='space-y-2'>
                    <label className='text-sm font-medium text-gray-700'>Payment Link</label>
                    <div className='flex gap-2'>
                        <input
                            type='text'
                            value={data}
                            readOnly
                            className='flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md bg-gray-50'
                        />
                        <Button variant='outline' size='sm' onClick={handleCopy}>
                            {copied ? <Check className='w-4 h-4' /> : <Copy className='w-4 h-4' />}
                        </Button>
                    </div>
                </div>

                {/* Actions */}
                <div className='flex gap-2'>
                    <Button variant='outline' className='flex-1' onClick={handleDownload}>
                        <Download className='w-4 h-4 mr-2' />
                        Download QR
                    </Button>
                    <Button className='flex-1' onClick={handleCopy}>
                        {copied ? 'Copied!' : 'Copy Link'}
                    </Button>
                </div>

                <p className='text-xs text-center text-gray-500'>
                    Share this QR code or link to receive payment
                </p>
            </CardContent>
        </Card>
    );
}
