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
python scripts/generate_secret_key.py   # paste output into .env as SECRET_KEY
createdb zippie_db
uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/api/docs.

## Migrations

Alembic manages schema changes. `DATABASE_URL` from `.env` is picked up automatically.

```bash
alembic upgrade head                              # apply pending migrations
alembic revision --autogenerate -m "add X"        # diff models vs DB, write migration
alembic stamp 0001_baseline                       # mark an existing DB at the baseline
```

On a DB that predates Alembic (schema created by `Base.metadata.create_all`), run
`alembic stamp 0001_baseline` once to set the starting point, then use `upgrade head`
for every subsequent change.

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

## Observability

- `SENTRY_DSN` — optional. Empty string disables Sentry entirely; set the DSN to enable error capture. Wrapped in `try/except ImportError` so the app runs even if `sentry-sdk` is uninstalled.
- `APP_VERSION` — appears in `/health` responses and is sent as the `release` tag to Sentry.
- `LOG_FORMAT` — `json` (default, structured stdout for prod log aggregators) or `text` (plain formatter for local dev and tests). Set to `text` in `tests/conftest.py`.
- `/health` now returns `version`, `environment`, and an ISO 8601 UTC `timestamp` alongside the existing `status`, `database`, and `services` keys — useful for deploy verification and uptime probes.

## Secrets management

Secrets resolve via `app.core.secrets.get_provider()`, selected by `SECRETS_PROVIDER`:

- **`env`** (default) — reads `os.environ` / `.env`. Use for local dev and any
  environment where config is injected at deploy time (Docker, Render, Railway).
- **`aws`** — AWS Secrets Manager. Requires `pip install boto3` and IAM creds
  on the runtime. Keys follow `{AWS_SECRETS_PREFIX}/{ENVIRONMENT}/{name}`,
  e.g. `zippie/production/PAYNOW_INTEGRATION_KEY`. Set `AWS_REGION`
  (default `af-south-1`). Values cache in-memory for the process lifetime.

Generate `SECRET_KEY`:

```bash
python scripts/generate_secret_key.py
```

**Rotation.** Update the secret in AWS Secrets Manager, then restart the app
to pick up the new value. Full rotation tooling (signal-triggered cache
invalidation, key-overlap windows) is follow-up work.

**Never commit filled-in `.env` files.** The repo `.gitignore` excludes
`.env`, `.env.local`, `.env.test`, and the usual per-environment variants;
only `.env.example` should be checked in. `pydantic-settings` currently
reads env vars directly; the provider abstraction is the seam for future
code paths that resolve a rotating secret outside the pydantic pipeline.

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
ADMIN_EMAILS=founder@zippie.co.zw
```

## Admin access (RBAC)

Two paths grant admin, either works:

1. **Role column** (preferred): set `users.role = 'admin'` on the user row.
   Valid roles: `user`, `admin`, `support`, `ops`, `finance`. Checked with
   exact match — `require_role("admin")` does NOT implicitly allow `ops`.
2. **Email allowlist** (bootstrap): add the email to `ADMIN_EMAILS` in `.env`.
   Useful before any admin-granting API exists.

Bootstrap the first admin manually, because there is no API yet to grant the
role:

```sql
UPDATE users SET role='admin' WHERE email='founder@zippie.co.zw';
```

Once the first admin has `role='admin'`, drop their email from `ADMIN_EMAILS`
and redeploy. The endpoints keep working through the role path. No Alembic
revision is shipped in this commit — the `role` column will appear in the
next auto-generated revision.
