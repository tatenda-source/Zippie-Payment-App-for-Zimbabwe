"""Migrate money columns from DOUBLE PRECISION (Float) to NUMERIC(18, 2).

Why: Python/Postgres floats are binary and lose precision on decimal values
(e.g. 0.1 + 0.2 = 0.30000000000000004). In a ledger, that error compounds
across millions of transactions into silent drift between balance and the
sum of ledger entries. NUMERIC(18, 2) is exact decimal arithmetic with
enough headroom for any plausible USD or ZiG amount.

Tables / columns touched:
  accounts.balance              float8 -> numeric(18,2)
  transactions.amount           float8 -> numeric(18,2)
  transactions.fee              float8 -> numeric(18,2)
  ledger_entries.amount         float8 -> numeric(18,2)
  ledger_entries.balance_after  float8 -> numeric(18,2)

This is a one-shot Postgres migration script — run once per environment.
For fresh deploys the model definitions (models.py) already produce the
correct schema, so this is only needed on environments that were created
before the switch.

Safety:
  - Wrapped in a single transaction; either everything migrates or nothing.
  - Uses ALTER COLUMN ... USING col::numeric(18,2) — Postgres does the cast
    per row with full precision of the source float. The (18,2) scale
    rounds half-to-even. For existing ledger data this is safe because
    balances were intended to be cents-precise anyway; any fractional
    precision past 2dp was already noise.
  - Reads sum-of-balances before and after for a quick sanity check.
  - Does NOT rebuild indexes (not needed — column swap preserves them).

Usage:
    cd backend
    source venv/bin/activate
    python scripts/migrate_money_columns_to_numeric.py
"""

import logging
import sys
from decimal import Decimal

from sqlalchemy import text

from app.db.database import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("migrate_numeric")

COLUMNS = [
    ("accounts", "balance"),
    ("transactions", "amount"),
    ("transactions", "fee"),
    ("ledger_entries", "amount"),
    ("ledger_entries", "balance_after"),
]


def column_type(conn, table: str, column: str) -> str:
    row = conn.execute(
        text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).first()
    return row[0] if row else ""


def sum_column(conn, table: str, column: str) -> Decimal:
    row = conn.execute(text(f"SELECT COALESCE(SUM({column}), 0) FROM {table}")).first()
    return Decimal(str(row[0]))


def main():
    with engine.begin() as conn:
        # 1. Pre-flight check — capture sums as Decimals for later comparison
        before = {}
        for table, column in COLUMNS:
            dtype = column_type(conn, table, column)
            if not dtype:
                logger.error(
                    f"Column {table}.{column} not found. Aborting."
                )
                sys.exit(1)
            total = sum_column(conn, table, column)
            before[(table, column)] = (dtype, total)
            logger.info(
                f"  {table}.{column}: type={dtype} sum={total}"
            )

        # 2. Skip entirely if nothing needs migrating
        still_float = [
            (t, c) for (t, c), (dt, _) in before.items()
            if dt in ("double precision", "real")
        ]
        if not still_float:
            logger.info("All columns already NUMERIC. Nothing to do.")
            return

        logger.info(f"Migrating {len(still_float)} columns to NUMERIC(18, 2)...")

        # 3. Alter each column in place
        for table, column in still_float:
            logger.info(f"  ALTER {table}.{column}...")
            conn.execute(
                text(
                    f"ALTER TABLE {table} "
                    f"ALTER COLUMN {column} "
                    f"TYPE NUMERIC(18, 2) "
                    f"USING {column}::numeric(18, 2)"
                )
            )

        # 4. Post-flight — compare sums. Allow tolerance of 0.01 per row
        #    because the rounding to 2dp can shift things slightly.
        row_counts = {}
        for table, _ in COLUMNS:
            rc = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            row_counts[table] = rc

        for table, column in still_float:
            after = sum_column(conn, table, column)
            _, before_total = before[(table, column)]
            drift = abs(after - before_total)
            tolerance = Decimal("0.01") * row_counts[table]
            logger.info(
                f"  {table}.{column}: before={before_total} after={after} "
                f"drift={drift} tolerance={tolerance}"
            )
            if drift > tolerance:
                logger.error(
                    f"DRIFT EXCEEDS TOLERANCE on {table}.{column}. "
                    "Transaction will be rolled back."
                )
                raise SystemExit(1)

    logger.info("Migration complete.")


if __name__ == "__main__":
    main()
