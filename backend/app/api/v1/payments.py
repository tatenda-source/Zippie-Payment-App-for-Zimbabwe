"""
P2P Payment API endpoints
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db import models
from app.db.database import get_db
from app.db.schemas import (
    AccountCreate,
    AccountResponse,
    TransactionCreate,
    TransactionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/accounts", response_model=List[AccountResponse])
async def get_accounts(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get user accounts"""
    accounts = (
        db.query(models.Account)
        .filter(
            models.Account.user_id == current_user.id, models.Account.is_active
        )
        .all()
    )

    return accounts


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new account"""
    # Validate currency
    valid_currencies = ["USD", "ZWL"]
    if account_data.currency not in valid_currencies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid currency. Must be one of: {', '.join(valid_currencies)}",
        )

    # Validate account type
    valid_types = ["primary", "savings", "investment"]
    if account_data.account_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid account type. Must be one of: {', '.join(valid_types)}",
        )

    try:
        db_account = models.Account(
            user_id=current_user.id,
            name=account_data.name,
            currency=account_data.currency,
            account_type=account_data.account_type,
            color=account_data.color,
        )

        db.add(db_account)
        db.commit()
        db.refresh(db_account)

        logger.info(
            f"Account created: user_id={current_user.id}, account_id={db_account.id}"
        )
        return db_account
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account",
        )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user transactions"""
    transactions = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.created_at.desc())
        .limit(limit)
        .all()
    )

    return transactions


@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new transaction"""
    # Validate transaction type
    valid_types = ["sent", "received", "request"]
    if transaction_data.transaction_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid transaction type. "
                f"Must be one of: {', '.join(valid_types)}"
            ),
        )

    # Validate amount
    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0",
        )

    try:
        # Verify account belongs to user if account_id is provided
        account = None
        if transaction_data.account_id:
            account = (
                db.query(models.Account)
                .filter(
                    models.Account.id == transaction_data.account_id,
                    models.Account.user_id == current_user.id,
                    models.Account.is_active,
                )
                .first()
            )

            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
                )

        # For "sent" transactions, validate and deduct from sender's account
        if transaction_data.transaction_type == "sent":
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Account is required for sending money",
                )

            if account.balance < transaction_data.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance",
                )

            # Deduct from sender's account
            account.balance -= transaction_data.amount
            transaction_status = "completed"
        else:
            # For "received" and "request" transactions, mark as pending
            transaction_status = "pending"

        # Create transaction record
        db_transaction = models.Transaction(
            user_id=current_user.id,
            account_id=transaction_data.account_id,
            transaction_type=transaction_data.transaction_type,
            amount=transaction_data.amount,
            currency=transaction_data.currency,
            recipient=transaction_data.recipient,
            sender=current_user.email
            if transaction_data.transaction_type == "sent"
            else None,
            description=transaction_data.description,
            payment_method=transaction_data.payment_method,
            status=transaction_status,
        )

        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)

        logger.info(
            f"Transaction created: id={db_transaction.id}, "
            f"user_id={current_user.id}, "
            f"type={transaction_data.transaction_type}, "
            f"amount={transaction_data.amount}"
        )

        return db_transaction
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transaction",
        )


@router.get("/balance")
async def get_balance(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get total balance across all accounts"""
    accounts = (
        db.query(models.Account)
        .filter(
            models.Account.user_id == current_user.id, models.Account.is_active
        )
        .all()
    )

    balance_usd = sum(acc.balance for acc in accounts if acc.currency == "USD")
    balance_zwl = sum(acc.balance for acc in accounts if acc.currency == "ZWL")

    return {
        "USD": balance_usd,
        "ZWL": balance_zwl,
        "accounts": [AccountResponse.model_validate(acc) for acc in accounts],
    }
