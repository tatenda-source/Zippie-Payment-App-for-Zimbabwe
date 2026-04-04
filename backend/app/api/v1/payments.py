"""
P2P Payment API endpoints
"""

import asyncio
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db import models
from app.db.database import get_db
from app.db.schemas import (
    AccountCreate,
    AccountResponse,
    PaynowInitiateRequest,
    PaynowInitiateResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionStatusResponse,
)
from app.services.paynow_service import paynow_service

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

        # For "sent" transactions, validate balance but do NOT deduct yet.
        # Balance deduction happens after Paynow confirms payment.
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

            # Pending until Paynow confirms
            transaction_status = "pending"
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


# --- Paynow Payment Gateway Endpoints ---


def _complete_transaction(db: Session, transaction: models.Transaction):
    """Mark transaction as completed and deduct balance atomically.

    Uses an atomic UPDATE WHERE status='pending' to prevent double-deduction
    from webhook + poll race conditions.
    """
    result = db.execute(
        update(models.Transaction)
        .where(
            models.Transaction.id == transaction.id,
            models.Transaction.status == "pending",
        )
        .values(status="completed")
    )

    if result.rowcount == 0:
        # Already processed by another path (webhook vs poll race)
        return False

    # Deduct balance from sender's account
    if transaction.account_id:
        account = db.query(models.Account).get(transaction.account_id)
        if account:
            account.balance -= transaction.amount

    db.commit()
    logger.info(f"Transaction {transaction.id} completed via Paynow")
    return True


def _fail_transaction(db: Session, transaction: models.Transaction):
    """Mark transaction as failed."""
    result = db.execute(
        update(models.Transaction)
        .where(
            models.Transaction.id == transaction.id,
            models.Transaction.status == "pending",
        )
        .values(status="failed")
    )
    db.commit()
    return result.rowcount > 0


@router.post("/paynow/initiate", response_model=PaynowInitiateResponse)
async def initiate_paynow_payment(
    request: PaynowInitiateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initiate a Paynow payment for a pending transaction."""
    if not paynow_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway is not configured",
        )

    # Look up transaction
    transaction = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == request.transaction_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    if transaction.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction is already {transaction.status}",
        )

    # Validate payment channel
    valid_channels = ["ecocash", "onemoney", "web"]
    if request.payment_channel not in valid_channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment channel. Must be one of: {valid_channels}",
        )

    if request.payment_channel != "web" and not request.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required for mobile payments",
        )

    reference = f"ZIPPIE-{transaction.id}"

    try:
        if request.payment_channel == "web":
            result = await asyncio.to_thread(
                paynow_service.initiate_web_checkout,
                reference,
                current_user.email,
                transaction.description or "Zippie Payment",
                transaction.amount,
            )
        else:
            result = await asyncio.to_thread(
                paynow_service.initiate_mobile_checkout,
                reference,
                current_user.email,
                transaction.description or "Zippie Payment",
                transaction.amount,
                request.phone_number,
                request.payment_channel,
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    # Store Paynow metadata on the transaction
    transaction.transaction_metadata = {
        "paynow_reference": reference,
        "poll_url": result.get("poll_url"),
        "redirect_url": result.get("redirect_url"),
        "instructions": result.get("instructions"),
        "payment_channel": request.payment_channel,
        "phone_number": request.phone_number,
    }
    transaction.payment_method = request.payment_channel
    db.commit()

    return PaynowInitiateResponse(
        transaction_id=transaction.id,
        status="pending",
        poll_url=result.get("poll_url"),
        redirect_url=result.get("redirect_url"),
        instructions=result.get("instructions"),
        paynow_reference=reference,
    )


@router.post("/paynow/webhook")
async def paynow_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paynow payment result webhook (unauthenticated).

    Paynow POSTs form data with transaction results to this endpoint.
    """
    form_data = await request.form()
    data = dict(form_data)

    # Validate hash
    if not paynow_service.validate_webhook(data):
        logger.warning("Paynow webhook received with invalid hash")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid hash"
        )

    reference = data.get("reference", "")
    paynow_status = data.get("status", "").lower()

    logger.info(
        f"Paynow webhook received: reference={reference}, status={paynow_status}"
    )

    # Extract transaction ID from reference (format: ZIPPIE-{id})
    try:
        tx_id = int(reference.replace("ZIPPIE-", ""))
    except (ValueError, AttributeError):
        logger.error(f"Invalid Paynow reference format: {reference}")
        return {"status": "ok"}

    transaction = db.query(models.Transaction).get(tx_id)
    if not transaction:
        logger.error(f"Transaction not found for Paynow reference: {reference}")
        return {"status": "ok"}

    if paynow_status == "paid":
        _complete_transaction(db, transaction)
    elif paynow_status in ("cancelled", "failed", "disputed"):
        _fail_transaction(db, transaction)

    return {"status": "ok"}


@router.get(
    "/paynow/status/{transaction_id}",
    response_model=TransactionStatusResponse,
)
async def check_paynow_status(
    transaction_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check Paynow payment status for a transaction (frontend polling)."""
    transaction = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == transaction_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    metadata = transaction.transaction_metadata or {}
    paynow_reference = metadata.get("paynow_reference")

    # If transaction is already resolved, return current status
    if transaction.status in ("completed", "failed"):
        return TransactionStatusResponse(
            transaction_id=transaction.id,
            status=transaction.status,
            paid=transaction.status == "completed",
            paynow_reference=paynow_reference,
        )

    # Poll Paynow for status update
    poll_url = metadata.get("poll_url")
    if poll_url and paynow_service.is_configured:
        try:
            result = await asyncio.to_thread(
                paynow_service.check_status, poll_url
            )

            if result["paid"]:
                _complete_transaction(db, transaction)
                db.refresh(transaction)
            elif result["status"] == "failed":
                _fail_transaction(db, transaction)
                db.refresh(transaction)
        except Exception as e:
            logger.error(f"Error polling Paynow status: {e}")

    return TransactionStatusResponse(
        transaction_id=transaction.id,
        status=transaction.status,
        paid=transaction.status == "completed",
        paynow_reference=paynow_reference,
    )
