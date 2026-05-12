"""Property-based tests for the float-era double-entry ledger invariants.

Skipped post-pivot: the ledger is audit-only and there is no balance
authority to invariant-check. Phase 4 rewrites or deletes this suite
alongside removing accounts.balance.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="Float-era invariants — pivot moved P2P off the internal ledger."
)
