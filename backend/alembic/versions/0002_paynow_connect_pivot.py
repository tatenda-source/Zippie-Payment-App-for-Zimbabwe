"""paynow connect pivot — tenants + paynow_id + transaction rails fields

Revision ID: 0002_paynow_connect_pivot
Revises: 0001_baseline
Create Date: 2026-05-12

Additive migration. Adds:
  - tenants table
  - users.paynow_id (nullable, indexed)
  - users.tenant_id FK (nullable, indexed)
  - users (tenant_id, paynow_id) UNIQUE constraint
  - transactions.tenant_id FK
  - transactions.sender_paynow_id, recipient_paynow_id
  - transactions.paynow_transfer_ref (UNIQUE, indexed)

Nothing is dropped. accounts.balance is left intact in Phase 1 so the
audit-only ledger writes still resolve; Phase 4 removes balance + the
reconciliation service entirely once we've confirmed no live float exists.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_paynow_connect_pivot"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("paynow_integration_id", sa.String(), nullable=True),
        sa.Column("paynow_integration_key", sa.String(), nullable=True),
        sa.Column("brand_config", sa.JSON(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenants_id", "tenants", ["id"])
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.add_column("users", sa.Column("paynow_id", sa.String(), nullable=True))
    op.add_column("users", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_index("ix_users_paynow_id", "users", ["paynow_id"])
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_foreign_key(
        "fk_users_tenant_id_tenants",
        "users",
        "tenants",
        ["tenant_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_users_tenant_paynow_id", "users", ["tenant_id", "paynow_id"]
    )
    # Postgres treats NULLs as distinct in UNIQUE indexes, so the composite
    # constraint above doesn't actually enforce uniqueness when tenant_id
    # is NULL — multiple rows could share the same paynow_id under the
    # platform default tenant context. The partial unique index closes that
    # gap. Both Postgres and SQLite (≥3.8) support partial unique indexes.
    op.execute(
        "CREATE UNIQUE INDEX uq_users_paynow_id_global "
        "ON users (paynow_id) WHERE tenant_id IS NULL"
    )

    op.add_column("transactions", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.add_column(
        "transactions", sa.Column("sender_paynow_id", sa.String(), nullable=True)
    )
    op.add_column(
        "transactions", sa.Column("recipient_paynow_id", sa.String(), nullable=True)
    )
    op.add_column(
        "transactions", sa.Column("paynow_transfer_ref", sa.String(), nullable=True)
    )
    op.create_index("ix_transactions_tenant_id", "transactions", ["tenant_id"])
    op.create_index(
        "ix_transactions_sender_paynow_id", "transactions", ["sender_paynow_id"]
    )
    op.create_index(
        "ix_transactions_recipient_paynow_id",
        "transactions",
        ["recipient_paynow_id"],
    )
    op.create_index(
        "ix_transactions_paynow_transfer_ref",
        "transactions",
        ["paynow_transfer_ref"],
        unique=True,
    )
    op.create_foreign_key(
        "fk_transactions_tenant_id_tenants",
        "transactions",
        "tenants",
        ["tenant_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_transactions_tenant_id_tenants", "transactions", type_="foreignkey"
    )
    op.drop_index("ix_transactions_paynow_transfer_ref", table_name="transactions")
    op.drop_index("ix_transactions_recipient_paynow_id", table_name="transactions")
    op.drop_index("ix_transactions_sender_paynow_id", table_name="transactions")
    op.drop_index("ix_transactions_tenant_id", table_name="transactions")
    op.drop_column("transactions", "paynow_transfer_ref")
    op.drop_column("transactions", "recipient_paynow_id")
    op.drop_column("transactions", "sender_paynow_id")
    op.drop_column("transactions", "tenant_id")

    op.execute("DROP INDEX IF EXISTS uq_users_paynow_id_global")
    op.drop_constraint("uq_users_tenant_paynow_id", "users", type_="unique")
    op.drop_constraint("fk_users_tenant_id_tenants", "users", type_="foreignkey")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_index("ix_users_paynow_id", table_name="users")
    op.drop_column("users", "tenant_id")
    op.drop_column("users", "paynow_id")

    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_index("ix_tenants_id", table_name="tenants")
    op.drop_table("tenants")
