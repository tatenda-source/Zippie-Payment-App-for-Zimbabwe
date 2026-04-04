"""
Pydantic schemas for request/response validation
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


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


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
