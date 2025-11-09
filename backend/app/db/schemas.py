"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    phone: str
    full_name: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Account Schemas
class AccountBase(BaseModel):
    name: str
    currency: str = "USD"
    account_type: str = "primary"
    color: str = "#10b981"


class AccountCreate(AccountBase):
    pass


class AccountResponse(AccountBase):
    id: int
    user_id: int
    balance: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    transaction_type: str
    amount: float
    currency: str = "USD"
    recipient: str
    description: Optional[str] = None
    payment_method: Optional[str] = None


class TransactionCreate(TransactionBase):
    account_id: Optional[int] = None


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    account_id: Optional[int]
    sender: Optional[str]
    status: str
    fee: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# Watchlist Schemas
class WatchlistBase(BaseModel):
    symbol: str
    exchange: Optional[str] = None
    target_price: Optional[float] = None
    notes: Optional[str] = None


class WatchlistCreate(WatchlistBase):
    pass


class WatchlistResponse(WatchlistBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Stock Schemas
class StockQuote(BaseModel):
    symbol: str
    short_name: str
    long_name: Optional[str] = None
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    currency: str = "USD"
    exchange: str


class StockHistoricalData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockPrediction(BaseModel):
    symbol: str
    predicted_price: float
    confidence: float
    predicted_change: float
    predicted_change_percent: float
    timeframe: str  # 1d, 1w, 1m, 3m
    prediction_date: datetime


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None

