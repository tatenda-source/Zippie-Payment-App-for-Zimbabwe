"""
P2P Payment API endpoints
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, update
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

        # Hot path: if this is a "sent" transaction AND the recipient is a Zippie
        # user, execute an atomic internal transfer (no Paynow, <50ms).
        if transaction_data.transaction_type == "sent" and account:
            recipient_user = _find_zippie_recipient(db, transaction_data.recipient)
            if recipient_user and recipient_user.id != current_user.id:
                return _internal_transfer(
                    db=db,
                    sender_user=current_user,
                    sender_account=account,
                    recipient_user=recipient_user,
                    recipient_identifier=transaction_data.recipient,
                    amount=transaction_data.amount,
                    description=transaction_data.description,
                )

        # Slow path: "sent" to non-Zippie user → validate balance and mark pending.
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


@router.get("/resolve-recipient")
async def resolve_recipient(
    query: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check whether a recipient identifier (phone/email) is a Zippie user.

    Used by the frontend to show the ⚡ instant badge and skip the Paynow flow.
    Does not leak private info — only returns is_zippie_user + display name if found.
    """
    recipient = _find_zippie_recipient(db, query)
    if not recipient or recipient.id == current_user.id:
        return {
            "is_zippie_user": False,
            "query": query,
        }

    return {
        "is_zippie_user": True,
        "query": query,
        "display_name": recipient.full_name,
    }


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
    """Mark transaction completed and deduct balance with row-level locking.

    Correctness guarantees:
      1. Atomic status flip (UPDATE WHERE status='pending') — prevents webhook/poll
         from both processing the same transaction.
      2. Row-level lock on the sender account (SELECT FOR UPDATE) — prevents two
         concurrent completions for the same sender from reading stale balance.
      3. Ledger entry for the debit is written in the same DB transaction.

    External-side (Paynow payout) is single-entry because credit occurs outside
    the system. A full double-entry implementation would model a "Paynow payout
    suspense" system account as the credit counterparty.
    """
    # Step 1: atomic status flip. If rowcount=0, another process already handled it.
    result = db.execute(
        update(models.Transaction)
        .where(
            models.Transaction.id == transaction.id,
            models.Transaction.status == "pending",
        )
        .values(status="completed")
    )

    if result.rowcount == 0:
        db.commit()
        return False

    # Step 2: lock sender account and apply debit inside same DB transaction.
    # populate_existing() refreshes cached ORM attributes after acquiring the lock.
    if transaction.account_id:
        account = (
            db.query(models.Account)
            .filter(models.Account.id == transaction.account_id)
            .with_for_update()
            .populate_existing()
            .first()
        )

        if account:
            account.balance -= transaction.amount

            # Step 3: write ledger entry
            debit = models.LedgerEntry(
                transaction_id=transaction.id,
                account_id=account.id,
                amount=transaction.amount,
                direction="debit",
                balance_after=account.balance,
            )
            db.add(debit)

    db.commit()
    logger.info(f"Transaction {transaction.id} completed via Paynow")
    return True


def _fail_transaction(db: Session, transaction: models.Transaction):
    """Mark transaction as failed (atomic, no balance change)."""
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


def _find_zippie_recipient(
    db: Session, recipient_identifier: str
) -> Optional[models.User]:
    """Look up a Zippie user by email or phone.

    Returns the User or None if the identifier doesn't match any Zippie user.
    """
    if not recipient_identifier:
        return None
    cleaned = recipient_identifier.strip()
    return (
        db.query(models.User)
        .filter(
            or_(
                models.User.email == cleaned,
                models.User.phone == cleaned,
            )
        )
        .first()
    )


def _get_or_create_recipient_account(
    db: Session, recipient_user: models.User, currency: str
) -> models.Account:
    """Find the recipient's primary account in the given currency, or create one."""
    account = (
        db.query(models.Account)
        .filter(
            models.Account.user_id == recipient_user.id,
            models.Account.currency == currency,
            models.Account.is_active,
        )
        .first()
    )

    if account is None:
        # Auto-create a matching-currency account so internal P2P always succeeds
        account = models.Account(
            user_id=recipient_user.id,
            name=f"{currency} Wallet",
            currency=currency,
            account_type="primary",
            color="#10b981",
        )
        db.add(account)
        db.flush()  # Get the ID without committing yet

    return account


def _internal_transfer(
    db: Session,
    sender_user: models.User,
    sender_account: models.Account,
    recipient_user: models.User,
    recipient_identifier: str,
    amount: float,
    description: Optional[str],
) -> models.Transaction:
    """Execute an atomic internal P2P transfer with double-entry ledger.

    This is the hot path for instant Zippie-to-Zippie transfers. It:
      1. Locks both sender and recipient accounts (ordered by ID to prevent deadlocks)
      2. Validates sender balance under the lock
      3. Applies debit + credit
      4. Writes the transaction record with status='completed'
      5. Writes the balanced DR/CR ledger pair
      6. Commits atomically

    Raises HTTPException(400) on insufficient balance.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0",
        )

    # Resolve recipient account (may create a new one if no matching currency exists)
    recipient_account = _get_or_create_recipient_account(
        db, recipient_user, sender_account.currency
    )

    if recipient_account.id == sender_account.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send to your own account",
        )

    # Lock both accounts in a deterministic order (smallest ID first) to prevent
    # deadlocks when two users transfer to each other simultaneously.
    #
    # populate_existing() is CRITICAL here: without it, SQLAlchemy sees the accounts
    # are already in the session's identity map and returns the cached Python objects
    # with stale attribute values — even though the DB lock was successfully acquired.
    # This would cause lost updates under concurrency.
    lock_ids = sorted([sender_account.id, recipient_account.id])
    locked_accounts = (
        db.query(models.Account)
        .filter(models.Account.id.in_(lock_ids))
        .with_for_update()
        .populate_existing()
        .all()
    )
    locked_by_id = {a.id: a for a in locked_accounts}
    sender = locked_by_id[sender_account.id]
    recipient = locked_by_id[recipient_account.id]

    # Re-check balance under the lock (the value read before locking could be stale)
    if sender.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance",
        )

    # Apply the transfer
    sender.balance -= amount
    recipient.balance += amount

    # Create the transaction record (sender's perspective)
    tx = models.Transaction(
        user_id=sender_user.id,
        account_id=sender.id,
        transaction_type="sent",
        amount=amount,
        currency=sender.currency,
        recipient=recipient_identifier,
        sender=sender_user.email,
        description=description,
        status="completed",
        payment_method="zippie_internal",
    )
    db.add(tx)
    db.flush()  # Get tx.id for ledger entries

    # Also create the mirror "received" transaction on the recipient's side
    mirror_tx = models.Transaction(
        user_id=recipient_user.id,
        account_id=recipient.id,
        transaction_type="received",
        amount=amount,
        currency=sender.currency,
        recipient=recipient_user.email,
        sender=sender_user.email,
        description=description,
        status="completed",
        payment_method="zippie_internal",
    )
    db.add(mirror_tx)
    db.flush()

    # Double-entry ledger — both sides of the transfer
    debit = models.LedgerEntry(
        transaction_id=tx.id,
        account_id=sender.id,
        amount=amount,
        direction="debit",
        balance_after=sender.balance,
    )
    credit = models.LedgerEntry(
        transaction_id=tx.id,
        account_id=recipient.id,
        amount=amount,
        direction="credit",
        balance_after=recipient.balance,
    )
    db.add(debit)
    db.add(credit)

    db.commit()
    db.refresh(tx)
    logger.info(
        f"Internal transfer completed: tx_id={tx.id} "
        f"sender={sender_user.email} recipient={recipient_user.email} "
        f"amount={amount} {sender.currency}"
    )
    return tx


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
