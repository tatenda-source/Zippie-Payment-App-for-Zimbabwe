# Zippie Backend — FastAPI + PostgreSQL

P2P payment backend: auth, accounts, internal ledger, Paynow gateway.

## Tech Stack

- **FastAPI** — web framework
- **PostgreSQL** — relational DB with `SELECT FOR UPDATE` row locking for ledger correctness
- **SQLAlchemy** — ORM (with `populate_existing()` to bypass identity-map caching under locks)
- **JWT** — auth via `python-jose` + `passlib[bcrypt]`
- **Paynow Python SDK** — Zimbabwe payment gateway

## Setup

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in credentials
createdb zippie_db
uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/api/docs.

## Project layout

```
backend/app/
├── api/v1/          # routes: auth.py, payments.py
├── core/            # config.py, security.py
├── db/              # database.py, models.py, schemas.py
├── services/        # paynow_service.py
└── main.py
```

## Tests

```bash
pytest                                    # all
pytest tests/integration/test_concurrency.py  # 50-thread ledger invariant test
pytest tests/unit/test_security.py
```

## Key design notes

- **Internal P2P is atomic** — `_internal_transfer` in `api/v1/payments.py` locks sender + recipient accounts in ID order (deadlock-safe), re-reads balance under the lock, writes a balanced DR/CR pair, commits.
- **Paynow webhooks** — `/payments/paynow/webhook` validates SHA512 hash before processing. Reference format: `ZIPPIE-{tx_id}`.
- **Float model** — see `../docs/ARCHITECTURE.md`. TL;DR: Paynow only at edges (top-up, cash-out); everything else hits the ledger.

## Environment

```
DATABASE_URL=postgresql://user:password@localhost:5432/zippie_db
SECRET_KEY=<generate via: python -c "import secrets; print(secrets.token_hex(32))">
PAYNOW_INTEGRATION_ID=
PAYNOW_INTEGRATION_KEY=
PAYNOW_RETURN_URL=http://localhost:3000/payment-success
PAYNOW_RESULT_URL=http://localhost:8000/api/v1/payments/paynow/webhook
CORS_ORIGINS=http://localhost:3000
DEBUG=true
```
