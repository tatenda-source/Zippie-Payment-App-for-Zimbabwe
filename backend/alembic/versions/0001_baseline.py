"""baseline

Revision ID: 0001_baseline
Revises:
Create Date: 2026-04-22

No-op baseline. The schema was created historically via
Base.metadata.create_all; this revision exists so future
`alembic revision --autogenerate` diffs have a parent to descend from.
On an already-deployed DB, apply with: `alembic stamp 0001_baseline`.
"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
