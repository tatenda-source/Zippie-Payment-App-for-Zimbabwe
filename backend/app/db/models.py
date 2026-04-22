"""
Database models for Zippie Payment Platform
"""

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class User(Base):
    """User model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    accounts = relationship(
        "Account", back_populates="owner", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )


class Account(Base):
    """Account model for P2P payments"""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    currency = Column(String, default="USD", nullable=False)  # USD, ZWL
    account_type = Column(String, default="primary")  # primary, savings, investment
    color = Column(String, default="#10b981")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    """Transaction model for P2P payments"""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    transaction_type = Column(String, nullable=False)  # sent, received, request
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    recipient = Column(String, nullable=False, index=True)
    sender = Column(String, nullable=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(
        String, default="pending", nullable=False
    )  # completed, pending, failed
    payment_method = Column(String, nullable=True)
    fee = Column(Float, default=0.0)
    transaction_metadata = Column(JSON, nullable=True)  # Additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    ledger_entries = relationship(
        "LedgerEntry", back_populates="transaction", cascade="all, delete-orphan"
    )


class LedgerEntry(Base):
    """Double-entry ledger entry.

    Every financial movement is recorded as one or more LedgerEntry rows.
    Internal P2P transfers create a balanced pair (1 debit, 1 credit).
    External transfers (via Paynow) create a single debit (credit side
    is external to the system).

    Invariants enforced at the DB level:
      - amount is always positive
      - direction is 'debit' or 'credit'
      - A transaction cannot have two entries with the same (account, direction)
    """

    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(
        Integer, ForeignKey("transactions.id"), nullable=False, index=True
    )
    account_id = Column(
        Integer, ForeignKey("accounts.id"), nullable=False, index=True
    )
    amount = Column(Float, nullable=False)
    direction = Column(String, nullable=False)  # 'debit' or 'credit'
    balance_after = Column(Float, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    transaction = relationship("Transaction", back_populates="ledger_entries")

    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            "account_id",
            "direction",
            name="uq_ledger_tx_account_direction",
        ),
        CheckConstraint("amount > 0", name="ck_ledger_amount_positive"),
        CheckConstraint(
            "direction IN ('debit', 'credit')", name="ck_ledger_direction_valid"
        ),
    )


class WebhookEvent(Base):
    """Append-only log of inbound webhooks, with dedup on (source, reference).

    Paynow retries webhooks on network errors — without dedup, a retried "paid"
    webhook would credit a wallet twice. We insert a row atomically before
    processing; the UNIQUE index makes duplicate inserts raise IntegrityError,
    which the caller turns into a short-circuit "already processed" return.
    """

    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)  # 'paynow'
    reference = Column(String, nullable=False)
    raw_payload = Column(JSON, nullable=False)
    received_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("source", "reference", name="uq_webhook_source_reference"),
        Index("ix_webhook_received_at", "received_at"),
    )

