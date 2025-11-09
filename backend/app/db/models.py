"""
Database models for Hippie Fintech Platform
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint
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
    accounts = relationship("Account", back_populates="owner", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")


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
    status = Column(String, default="pending", nullable=False)  # completed, pending, failed
    payment_method = Column(String, nullable=True)
    fee = Column(Float, default=0.0)
    metadata = Column(JSON, nullable=True)  # Additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")


class Watchlist(Base):
    """Watchlist model for stock tracking"""
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=True)  # NASDAQ, NYSE, ZSE, etc.
    target_price = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    
    # Unique constraint: one symbol per user
    __table_args__ = (
        UniqueConstraint('user_id', 'symbol', name='uq_user_symbol'),
    )

