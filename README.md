# Paynow Connect

**White-label payments platform on Paynow rails.** Paynow Connect is the B2B SaaS layer that lets businesses (SACCOs, schools, merchants) ship branded P2P / payouts apps powered by Paynow. Every transfer is a Paynow account-to-account operation between Paynow IDs — the platform holds no float, taking the regulatory and reconciliation burden off the tenant.

> See [`docs/PIVOT_PLAN.md`](docs/PIVOT_PLAN.md) for the current architecture direction (Phase 1 in flight).
> Historical: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) documents the original Zippie float model, now being phased out.

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

- **Backend** (`backend/`) — FastAPI + PostgreSQL. Auth (JWT), multi-tenant model, transactions routed through a pluggable Paynow rails adapter, audit-only ledger.
- **Frontend** (`src/`) — React 18 + TypeScript + Tailwind. Home, SendMoney, RequestPayment, TransactionHistory, PaymentSuccess. Full multi-tenant rebrand lands in Phase 2.

## Quick start

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, SECRET_KEY, PAYNOW_*
createdb paynow_connect_db
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

Concurrency test: `backend/tests/integration/test_concurrency.py` — 50 parallel rails-adapter pushes verify idempotency on `paynow_transfer_ref` UNIQUE.

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
DATABASE_URL=postgresql://user:password@localhost:5432/paynow_connect_db
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
PAYNOW_INTEGRATION_ID=
PAYNOW_INTEGRATION_KEY=
PAYNOW_RETURN_URL=http://localhost:3000/payment-success
PAYNOW_RESULT_URL=http://localhost:8000/api/v1/payments/paynow/webhook
PAYNOW_RAILS_ADAPTER=merchant_collect_payout  # merchant_collect_payout | a2a_push | mock
CORS_ORIGINS=http://localhost:3000
DEBUG=true
```

**Frontend `.env`:**

```
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Status

Phase 1 (Zippie → Paynow Connect pivot) in flight. Phase plan + scope: [`docs/PIVOT_PLAN.md`](docs/PIVOT_PLAN.md).

## License

MIT.
