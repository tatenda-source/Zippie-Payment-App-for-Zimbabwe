# Zippie — P2P Payment App for Zimbabwe

**Instant P2P payments on top of Paynow's rails.** Zippie is the consumer wallet layer that sits above mobile money (EcoCash / OneMoney) — you top up once, send to other Zippie users at <50ms against an internal double-entry ledger, and cash out when you need to.

> See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the float model, correctness guarantees, and risk controls.
> See [`docs/VC_ANALYSIS.md`](docs/VC_ANALYSIS.md) for the strategic / GTM deep-dive.

## CI

![backend-ci](https://github.com/OWNER/REPO/actions/workflows/backend-ci.yml/badge.svg)
![frontend-ci](https://github.com/OWNER/REPO/actions/workflows/frontend-ci.yml/badge.svg)

Every push and PR against `main` runs lint, type-check, and test jobs. Backend: black / isort / flake8 / mypy (advisory) / pytest with coverage. Frontend: eslint / tsc / jest / build. Weekly dependency audit via `pip-audit` and `npm audit`.

Install local hooks to catch issues before they hit CI:

```bash
pip install pre-commit && pre-commit install
```

Workflow source of truth: [`.github/workflows/`](.github/workflows/).

## What's in the repo

- **Backend** (`backend/`) — FastAPI + PostgreSQL. Auth (JWT), accounts, transactions, internal P2P ledger, Paynow gateway integration. Concurrency-tested under 50 parallel transfers.
- **Frontend** (`src/`) — React 18 + TypeScript + Tailwind. Home, SendMoney, RequestPayment, TransactionHistory, PaymentSuccess.

## Quick start

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, SECRET_KEY, PAYNOW_*
createdb zippie_db
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000 — docs at `/api/docs`.

### Frontend

```bash
npm install
echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env
npm start
```

App: http://localhost:3000.

## Tests

```bash
# Backend
cd backend && pytest

# Frontend
npm test
```

Concurrency test: `backend/tests/integration/test_concurrency.py` — 50 threads × $10 on a $500 wallet verifies ledger invariant (`sum(debits) == sum(credits)`, sender → $0, recipient → $500).

## Core endpoints

| Area | Endpoint |
|---|---|
| Auth | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Accounts | `GET /api/v1/payments/accounts`, `POST /api/v1/payments/accounts`, `GET /api/v1/payments/balance` |
| Transactions | `GET /api/v1/payments/transactions`, `POST /api/v1/payments/transactions` |
| Recipient lookup | `GET /api/v1/payments/resolve-recipient?query=…` |
| Paynow | `POST /api/v1/payments/paynow/initiate`, `POST /api/v1/payments/paynow/webhook`, `GET /api/v1/payments/paynow/status/{id}` |
| Top-up | `POST /api/v1/payments/paynow/topup/initiate` |

## Environment

**Backend `.env`:**

```
DATABASE_URL=postgresql://user:password@localhost:5432/zippie_db
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
PAYNOW_INTEGRATION_ID=
PAYNOW_INTEGRATION_KEY=
PAYNOW_RETURN_URL=http://localhost:3000/payment-success
PAYNOW_RESULT_URL=http://localhost:8000/api/v1/payments/paynow/webhook
CORS_ORIGINS=http://localhost:3000
DEBUG=true
```

**Frontend `.env`:**

```
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Status

Current sprint: top-up + cash-out (Sprint 1 in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)).

Priority tracker lives in the architecture doc — P0/P1/P2 split, shipped vs. open.

## License

MIT.
