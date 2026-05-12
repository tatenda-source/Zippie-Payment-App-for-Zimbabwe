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
    paynow_id: str  # required: every user must link a Paynow ID at registration
    tenant_slug: Optional[str] = None  # optional during pivot; required once Phase 3 ships


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    paynow_id: Optional[str] = None
    tenant_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Tenant Schemas
class TenantBase(BaseModel):
    slug: str
    name: str
    brand_config: Optional[dict] = None


class TenantCreate(TenantBase):
    paynow_integration_id: Optional[str] = None
    paynow_integration_key: Optional[str] = None


class TenantResponse(TenantBase):
    id: int
    is_active: bool
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
    recipient_paynow_id: Optional[str] = None  # required for "sent"; resolved via /resolve-recipient otherwise


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    account_id: Optional[int]
    sender: Optional[str]
    sender_paynow_id: Optional[str] = None
    recipient_paynow_id: Optional[str] = None
    paynow_transfer_ref: Optional[str] = None
    status: str
    fee: float
    transaction_metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Paynow Schemas
class PaynowInitiateRequest(BaseModel):
    transaction_id: int
    payment_channel: str  # "ecocash", "onemoney", or "web"
    phone_number: Optional[str] = None  # Required for ecocash/onemoney


class PaynowInitiateResponse(BaseModel):
    transaction_id: int
    status: str
    poll_url: Optional[str] = None
    redirect_url: Optional[str] = None
    instructions: Optional[str] = None
    paynow_reference: Optional[str] = None


class TransactionStatusResponse(BaseModel):
    transaction_id: int
    status: str
    paid: bool
    paynow_reference: Optional[str] = None


# Recipient resolution
class ResolveRecipientResponse(BaseModel):
    paynow_id: str
    is_known_user: bool  # true if recipient is registered in our local DB
    display_name: Optional[str] = None
    tenant_id: Optional[int] = None


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
