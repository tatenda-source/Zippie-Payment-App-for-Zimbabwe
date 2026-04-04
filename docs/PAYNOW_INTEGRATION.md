# Paynow Zimbabwe Integration Plan

## Overview

Paynow Zimbabwe is integrated as the payment gateway middleware for all P2P transactions in Zippie. When a user sends money, the payment flows through Paynow (EcoCash, OneMoney, or web checkout) before the balance is updated.

## Architecture

```
BEFORE:  User confirms -> Backend deducts balance -> "completed" immediately
AFTER:   User confirms -> Pending tx created -> Paynow initiated -> User approves on phone -> Webhook/poll confirms -> Backend deducts balance -> "completed"
```

## Payment Flow

### Mobile Money (EcoCash/OneMoney)

1. User selects account, enters recipient + amount
2. User chooses EcoCash or OneMoney, enters phone number
3. User confirms payment
4. Frontend: `POST /payments/transactions` (creates pending transaction)
5. Frontend: `POST /payments/paynow/initiate` (initiates Paynow mobile checkout)
6. Paynow sends USSD prompt to user's phone
7. Frontend shows "Waiting for approval" screen with instructions
8. Frontend polls `GET /payments/paynow/status/{id}` every 5s (2min timeout)
9. User approves on phone -> Paynow confirms
10. Backend deducts balance, marks transaction "completed"
11. Frontend navigates to success screen

### Web Checkout (Visa/Mastercard/ZimSwitch)

1. Steps 1-4 same as above
2. Frontend: `POST /payments/paynow/initiate` with `payment_channel: "web"`
3. User is redirected to Paynow hosted payment page
4. User completes payment on Paynow
5. Paynow redirects back + sends webhook
6. Backend processes webhook, deducts balance

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/payments/transactions` | POST | Yes | Create pending transaction |
| `/payments/paynow/initiate` | POST | Yes | Initiate Paynow payment |
| `/payments/paynow/webhook` | POST | No | Paynow callback handler |
| `/payments/paynow/status/{id}` | GET | Yes | Poll transaction status |

### POST /payments/paynow/initiate

Request:
```json
{
  "transaction_id": 42,
  "payment_channel": "ecocash",
  "phone_number": "0771234567"
}
```

Response:
```json
{
  "transaction_id": 42,
  "status": "pending",
  "poll_url": "https://www.paynow.co.zw/Interface/CheckPayment/?guid=...",
  "instructions": "Check your phone to approve the payment",
  "paynow_reference": "ZIPPIE-42"
}
```

### GET /payments/paynow/status/{transaction_id}

Response:
```json
{
  "transaction_id": 42,
  "status": "completed",
  "paid": true,
  "paynow_reference": "ZIPPIE-42"
}
```

## Configuration

Add to `.env`:

```env
PAYNOW_INTEGRATION_ID=your_integration_id
PAYNOW_INTEGRATION_KEY=your_integration_key
PAYNOW_RETURN_URL=http://localhost:3000/payment/return
PAYNOW_RESULT_URL=http://localhost:8000/api/v1/payments/paynow/webhook
```

## Test Mode

Paynow starts in test mode by default. Use these test numbers:

| Phone Number | Behavior |
|-------------|----------|
| `0771111111` | Payment succeeds |
| `0772222222` | Payment succeeds (delayed) |
| `0773333333` | Payment cancelled |
| `0774444444` | Insufficient balance |

## Files Modified/Created

| File | Change |
|------|--------|
| `backend/requirements.txt` | Added `paynow==2.1.2` |
| `backend/app/core/config.py` | Added 4 Paynow config fields |
| `backend/app/services/paynow_service.py` | **NEW** - Paynow SDK wrapper |
| `backend/app/db/schemas.py` | Added Paynow request/response schemas |
| `backend/app/api/v1/payments.py` | Changed create_transaction + 3 new endpoints |
| `src/types/transaction.ts` | Added PaymentChannel type, processing status |
| `src/services/api.ts` | Added initiatePaynowPayment + pollTransactionStatus |
| `src/components/SendMoney.tsx` | Payment method step + processing screen |
| `src/contexts/AppContext.tsx` | Adjusted handlePaymentSuccess |

## Key Design Decisions

- **No DB migration needed**: Existing `transaction_metadata` JSON field stores all Paynow data (poll_url, reference, instructions)
- **Polling as primary**: Webhook requires public URL (won't work in dev). Frontend polls every 5s as fallback.
- **Atomic deduction**: `UPDATE WHERE status='pending'` prevents double-charge from webhook+poll race condition
- **`asyncio.to_thread()`**: Paynow SDK is synchronous; run in thread pool to avoid blocking FastAPI
- **EcoCash default**: Most popular mobile money provider in Zimbabwe

## Security

- Webhook validates SHA512 hash using integration key (prevents spoofed callbacks)
- All user-facing endpoints require JWT authentication
- Transaction ownership verified before any status check
- Balance validated before creating transaction (prevents overdraft)
