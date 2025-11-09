"""
P2P Payment API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db import models
from app.db.schemas import AccountResponse, TransactionCreate, TransactionResponse
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.get("/accounts", response_model=List[AccountResponse])
async def get_accounts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user accounts"""
    accounts = db.query(models.Account).filter(
        models.Account.user_id == current_user.id,
        models.Account.is_active == True
    ).all()
    
    return accounts


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    account_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new account"""
    db_account = models.Account(
        user_id=current_user.id,
        name=account_data.get("name"),
        currency=account_data.get("currency", "USD"),
        account_type=account_data.get("account_type", "primary"),
        color=account_data.get("color", "#10b981")
    )
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    return db_account


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user transactions"""
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).order_by(models.Transaction.created_at.desc()).limit(limit).all()
    
    return transactions


@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new transaction"""
    # Verify account belongs to user if account_id is provided
    if transaction_data.account_id:
        account = db.query(models.Account).filter(
            models.Account.id == transaction_data.account_id,
            models.Account.user_id == current_user.id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=404,
                detail="Account not found"
            )
        
        # Update account balance if transaction is sent
        if transaction_data.transaction_type == "sent":
            if account.balance < transaction_data.amount:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient balance"
                )
            account.balance -= transaction_data.amount
    
    db_transaction = models.Transaction(
        user_id=current_user.id,
        account_id=transaction_data.account_id,
        transaction_type=transaction_data.transaction_type,
        amount=transaction_data.amount,
        currency=transaction_data.currency,
        recipient=transaction_data.recipient,
        description=transaction_data.description,
        payment_method=transaction_data.payment_method,
        status="completed"
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction


@router.get("/balance")
async def get_balance(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get total balance across all accounts"""
    accounts = db.query(models.Account).filter(
        models.Account.user_id == current_user.id,
        models.Account.is_active == True
    ).all()
    
    balance_usd = sum(acc.balance for acc in accounts if acc.currency == "USD")
    balance_zwl = sum(acc.balance for acc in accounts if acc.currency == "ZWL")
    
    return {
        "USD": balance_usd,
        "ZWL": balance_zwl,
        "accounts": [AccountResponse.model_validate(acc) for acc in accounts]
    }

