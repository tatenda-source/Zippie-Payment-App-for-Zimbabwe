"""Payments API.

Post-pivot semantics: P2P transfers are routed through a Paynow rails
adapter — Paynow Connect never holds float. Transaction + LedgerEntry
rows are written as audit records, not as balance authority.
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.core.features import require_feature
from app.core.idempotency import check_idempotency, store_idempotency
from app.core.rate_limit import limiter
from app.db import models
from app.db.database import get_db
from app.db.schemas import (
    AccountCreate,
    AccountResponse,
    PaynowInitiateRequest,
    PaynowInitiateResponse,
    ResolveRecipientResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionStatusResponse,
)
from app.services.audit_log import record_event
from app.services.paynow_rails import TenantCredentials, get_rails_adapter
from app.services.paynow_service import paynow_service

logger = logging.getLogger(__name__)

router = APIRouter()

PAYNOW_ID_REGEX = re.compile(r"^[A-Za-z0-9._-]{4,32}$")
_REFERENCE_PREFIXES = ("PNC-", "ZIPPIE-")


# ---------- Accounts (legacy — kept for audit ledger writes; balance is not authoritative) ----------


@router.get("/accounts", response_model=List[AccountResponse])
async def get_accounts(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    accounts = (
        db.query(models.Account)
        .filter(models.Account.user_id == current_user.id, models.Account.is_active)
        .all()
    )
    return accounts


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    idempotency_key = request.headers.get("X-Idempotency-Key")
    cached = check_idempotency(db, current_user, idempotency_key, request.url.path)
    if cached is not None:
        return JSONResponse(status_code=cached[0], content=cached[1])

    valid_currencies = ["USD", "ZWL"]
    if account_data.currency not in valid_currencies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid currency. Must be one of: {', '.join(valid_currencies)}",
        )

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
        db.flush()
        db.refresh(db_account)

        response_body = jsonable_encoder(AccountResponse.model_validate(db_account))
        store_idempotency(db, current_user, idempotency_key, request.url.path, 200, response_body)
        db.commit()

        logger.info(f"Account created: user_id={current_user.id}, account_id={db_account.id}")
        return db_account
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account",
        )


# ---------- Transactions ----------


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


@router.post("/transactions", response_model=TransactionResponse)
@limiter.limit("30/minute")
async def create_transaction(
    request: Request,
    transaction_data: TransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a transaction. For 'sent', routes through the Paynow rails adapter."""
    idempotency_key = request.headers.get("X-Idempotency-Key")
    cached = check_idempotency(db, current_user, idempotency_key, request.url.path)
    if cached is not None:
        return JSONResponse(status_code=cached[0], content=cached[1])

    valid_types = ["sent", "received", "request"]
    if transaction_data.transaction_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transaction type. Must be one of: {', '.join(valid_types)}",
        )

    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0",
        )

    if transaction_data.transaction_type == "sent":
        _enforce_velocity_limit(db, current_user, transaction_data.amount)
        tx = _rails_transfer(
            db=db,
            sender_user=current_user,
            recipient_identifier=transaction_data.recipient,
            recipient_paynow_id=transaction_data.recipient_paynow_id,
            amount=transaction_data.amount,
            currency=transaction_data.currency,
            description=transaction_data.description,
            account_id=transaction_data.account_id,
        )
        if idempotency_key:
            store_idempotency(
                db,
                current_user,
                idempotency_key,
                request.url.path,
                200,
                jsonable_encoder(TransactionResponse.model_validate(tx)),
            )
            db.commit()
        return tx

    # "received" / "request" stay as pending records; no rails call.
    try:
        db_transaction = models.Transaction(
            user_id=current_user.id,
            account_id=transaction_data.account_id,
            tenant_id=current_user.tenant_id,
            transaction_type=transaction_data.transaction_type,
            amount=transaction_data.amount,
            currency=transaction_data.currency,
            recipient=transaction_data.recipient,
            sender=None,
            description=transaction_data.description,
            payment_method=transaction_data.payment_method,
            status="pending",
        )
        db.add(db_transaction)
        db.flush()
        db.refresh(db_transaction)

        response_body = jsonable_encoder(TransactionResponse.model_validate(db_transaction))
        store_idempotency(db, current_user, idempotency_key, request.url.path, 200, response_body)
        db.commit()
        logger.info(
            f"Transaction created: id={db_transaction.id}, "
            f"user_id={current_user.id}, type={transaction_data.transaction_type}"
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


# ---------- Recipient resolution ----------


@router.get("/resolve-recipient", response_model=ResolveRecipientResponse)
async def resolve_recipient(
    paynow_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resolve a Paynow ID to a display name.

    DB-first: if the Paynow ID belongs to a registered user we return their
    display name (and tenant context). Falls back to asking the rails adapter
    (when the adapter supports it). Returns is_known_user=False if the ID
    can't be resolved locally.
    """
    paynow_id = (paynow_id or "").strip()
    if not PAYNOW_ID_REGEX.match(paynow_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Paynow ID format"
        )

    local = (
        db.query(models.User)
        .filter(models.User.paynow_id == paynow_id, models.User.id != current_user.id)
        .first()
    )
    if local:
        return ResolveRecipientResponse(
            paynow_id=paynow_id,
            is_known_user=True,
            display_name=local.full_name,
            tenant_id=local.tenant_id,
        )

    creds = TenantCredentials.for_tenant(_tenant_for(current_user, db))
    try:
        info = get_rails_adapter().lookup_paynow_id(paynow_id, creds)
        return ResolveRecipientResponse(
            paynow_id=paynow_id,
            is_known_user=False,
            display_name=info.get("display_name"),
            tenant_id=None,
        )
    except NotImplementedError:
        return ResolveRecipientResponse(paynow_id=paynow_id, is_known_user=False)


# ---------- Balance (deprecated) ----------


@router.get("/balance")
async def get_balance(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Deprecated. Paynow Connect no longer holds float.

    Use GET /paynow/balance for the user's Paynow account balance, when the
    configured rails adapter supports it.
    """
    return JSONResponse(
        status_code=status.HTTP_410_GONE,
        content={
            "error": "deprecated",
            "message": "Paynow Connect no longer holds float. Query /paynow/balance instead.",
        },
    )


@router.get("/paynow/balance")
async def get_paynow_balance(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Return Paynow's reported balance for the current user's Paynow ID."""
    if not current_user.paynow_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Paynow ID linked on this account",
        )
    creds = TenantCredentials.for_tenant(_tenant_for(current_user, db))
    try:
        return get_rails_adapter().get_balance(current_user.paynow_id, creds)
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e)
        )


# ---------- Paynow webhook + status ----------


@router.post("/paynow/webhook")
@limiter.limit("60/minute")
async def paynow_webhook(request: Request, db: Session = Depends(get_db)):
    """Paynow result webhook. Marks transactions completed/failed; no balance writes."""
    form_data = await request.form()
    data = dict(form_data)

    if not paynow_service.validate_webhook(data):
        logger.warning("Paynow webhook received with invalid hash")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid hash")

    reference = data.get("reference", "")
    paynow_status = data.get("status", "").lower()
    logger.info(f"Paynow webhook received: reference={reference}, status={paynow_status}")

    event_key = f"{reference}:{paynow_status}" if reference else ""
    if event_key:
        try:
            with db.begin_nested():
                db.add(
                    models.WebhookEvent(
                        source="paynow", reference=event_key, raw_payload=data
                    )
                )
        except IntegrityError:
            logger.info(f"Paynow webhook already processed (dedup): {event_key}")
            return {"status": "ok", "deduped": True}

    tx_id = _parse_tx_id_from_reference(reference)
    if tx_id is None:
        logger.error(f"Invalid Paynow reference format: {reference}")
        db.commit()
        return {"status": "ok"}

    transaction = db.query(models.Transaction).get(tx_id)
    if not transaction:
        logger.error(f"Transaction not found for Paynow reference: {reference}")
        db.commit()
        return {"status": "ok"}

    if paynow_status == "paid":
        _complete_transaction(db, transaction)
    elif paynow_status in ("cancelled", "failed", "disputed"):
        _fail_transaction(db, transaction)

    if event_key:
        db.execute(
            update(models.WebhookEvent)
            .where(
                models.WebhookEvent.source == "paynow",
                models.WebhookEvent.reference == event_key,
            )
            .values(processed_at=datetime.now(timezone.utc))
        )
        db.commit()

    return {"status": "ok"}


@router.get("/paynow/status/{transaction_id}", response_model=TransactionStatusResponse)
async def check_paynow_status(
    transaction_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll Paynow status for a transaction (frontend polling)."""
    transaction = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == transaction_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    metadata = transaction.transaction_metadata or {}
    paynow_reference = metadata.get("paynow_reference") or transaction.paynow_transfer_ref

    if transaction.status in ("completed", "failed"):
        return TransactionStatusResponse(
            transaction_id=transaction.id,
            status=transaction.status,
            paid=transaction.status == "completed",
            paynow_reference=paynow_reference,
        )

    poll_url = metadata.get("poll_url")
    if poll_url and paynow_service.is_configured:
        try:
            result = await asyncio.to_thread(paynow_service.check_status, poll_url)
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


# ---------- Paynow initiate (kept for the merchant_collect_payout adapter's collect leg) ----------


@router.post(
    "/paynow/initiate",
    response_model=PaynowInitiateResponse,
    dependencies=[Depends(require_feature("paynow_checkout"))],
)
async def initiate_paynow_payment(
    request: PaynowInitiateRequest,
    http_request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initiate the collect leg of a pending rails transfer.

    Used by the MerchantCollectPayoutAdapter — the API call that created the
    transaction returned a pending record; this endpoint kicks the USSD
    prompt to the sender's mobile money. Webhook then triggers the payout
    leg to the recipient's Paynow ID.
    """
    idempotency_key = http_request.headers.get("X-Idempotency-Key")
    cached = check_idempotency(db, current_user, idempotency_key, http_request.url.path)
    if cached is not None:
        return JSONResponse(status_code=cached[0], content=cached[1])

    if not paynow_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway is not configured",
        )

    transaction = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == request.transaction_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if transaction.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction is already {transaction.status}",
        )

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

    reference = transaction.paynow_transfer_ref or _build_paynow_reference(transaction.id)

    try:
        if request.payment_channel == "web":
            result = await asyncio.to_thread(
                paynow_service.initiate_web_checkout,
                reference,
                current_user.email,
                transaction.description or "Paynow Connect Payment",
                float(transaction.amount),
            )
        else:
            result = await asyncio.to_thread(
                paynow_service.initiate_mobile_checkout,
                reference,
                current_user.email,
                transaction.description or "Paynow Connect Payment",
                float(transaction.amount),
                request.phone_number,
                request.payment_channel,
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    transaction.transaction_metadata = {
        **(transaction.transaction_metadata or {}),
        "paynow_reference": reference,
        "poll_url": result.get("poll_url"),
        "redirect_url": result.get("redirect_url"),
        "instructions": result.get("instructions"),
        "payment_channel": request.payment_channel,
        "phone_number": request.phone_number,
    }
    transaction.payment_method = request.payment_channel

    response_obj = PaynowInitiateResponse(
        transaction_id=transaction.id,
        status="pending",
        poll_url=result.get("poll_url"),
        redirect_url=result.get("redirect_url"),
        instructions=result.get("instructions"),
        paynow_reference=reference,
    )
    store_idempotency(
        db, current_user, idempotency_key, http_request.url.path, 200, jsonable_encoder(response_obj)
    )
    db.commit()
    return response_obj


# ---------- helpers ----------


def _to_decimal(amount) -> Decimal:
    if isinstance(amount, Decimal):
        return amount
    return Decimal(str(amount))


def _build_paynow_reference(tx_id: int) -> str:
    """Build an unenumerable Paynow reference: PNC-{uuid12}-{tx_id}."""
    return f"PNC-{uuid.uuid4().hex[:12]}-{tx_id}"


def _parse_tx_id_from_reference(reference: str) -> Optional[int]:
    """Extract transaction ID from PNC- or legacy ZIPPIE- reference."""
    if not reference or not any(reference.startswith(p) for p in _REFERENCE_PREFIXES):
        return None
    try:
        return int(reference.rsplit("-", 1)[-1])
    except (ValueError, AttributeError):
        return None


def _enforce_velocity_limit(db: Session, user: models.User, amount):
    """Reject if user's rolling-24h outgoing total + amount exceeds their tier cap."""
    cap = _to_decimal(
        settings.DAILY_LIMIT_VERIFIED if user.is_verified else settings.DAILY_LIMIT_UNVERIFIED
    )
    amount_dec = _to_decimal(amount)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    rows = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user.id,
            models.Transaction.transaction_type == "sent",
            models.Transaction.status.in_(("pending", "completed")),
            models.Transaction.created_at >= since,
        )
        .with_entities(models.Transaction.amount)
        .all()
    )
    used = sum((row[0] for row in rows), Decimal(0))
    if used + amount_dec > cap:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily send limit exceeded. Used ${used:.2f} of ${cap:.2f} in the last 24h.",
        )


def _tenant_for(user: models.User, db: Session) -> Optional[models.Tenant]:
    if not user.tenant_id:
        return None
    return db.query(models.Tenant).get(user.tenant_id)


def _resolve_recipient_paynow_id(
    db: Session,
    sender: models.User,
    explicit_paynow_id: Optional[str],
    recipient_identifier: str,
) -> str:
    """Pick the Paynow ID to push to.

    Order:
      1. Explicit recipient_paynow_id on the request (validated).
      2. Local user lookup by recipient_identifier as email/phone, returning
         that user's paynow_id if one is linked.

    Raises 400 if neither path yields a valid Paynow ID.
    """
    if explicit_paynow_id:
        candidate = explicit_paynow_id.strip()
        if not PAYNOW_ID_REGEX.match(candidate):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid recipient_paynow_id format",
            )
        return candidate

    if recipient_identifier:
        cleaned = recipient_identifier.strip()
        local = (
            db.query(models.User)
            .filter(
                (models.User.email == cleaned) | (models.User.phone == cleaned)
            )
            .first()
        )
        if local and local.paynow_id:
            return local.paynow_id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Cannot resolve recipient Paynow ID. Provide recipient_paynow_id "
            "explicitly or use a recipient that maps to a registered user."
        ),
    )


def _rails_transfer(
    db: Session,
    sender_user: models.User,
    recipient_identifier: str,
    recipient_paynow_id: Optional[str],
    amount,
    currency: str,
    description: Optional[str],
    account_id: Optional[int] = None,
) -> models.Transaction:
    """Execute a P2P transfer via the configured Paynow rails adapter.

    Writes a Transaction row + an audit LedgerEntry (no balance mutation).
    The status reflects what the adapter reports: 'completed' for adapters
    that finalize synchronously (mock, a2a_push); 'pending' for adapters
    that need a follow-up webhook to confirm (merchant_collect_payout).
    """
    if not sender_user.paynow_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sender has no Paynow ID linked",
        )

    amount_dec = _to_decimal(amount)
    if amount_dec <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0",
        )

    resolved_recipient = _resolve_recipient_paynow_id(
        db, sender_user, recipient_paynow_id, recipient_identifier
    )
    if resolved_recipient == sender_user.paynow_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send to your own Paynow ID",
        )

    # Create the transaction record first so we have an id for the reference.
    tx = models.Transaction(
        user_id=sender_user.id,
        account_id=account_id,
        tenant_id=sender_user.tenant_id,
        transaction_type="sent",
        amount=amount_dec,
        currency=currency,
        recipient=recipient_identifier,
        sender=sender_user.email,
        sender_paynow_id=sender_user.paynow_id,
        recipient_paynow_id=resolved_recipient,
        description=description,
        status="pending",
        payment_method="paynow_rails",
    )
    db.add(tx)
    db.flush()  # assign tx.id

    reference = _build_paynow_reference(tx.id)
    tx.paynow_transfer_ref = reference

    tenant = _tenant_for(sender_user, db)
    creds = TenantCredentials.for_tenant(tenant)
    adapter = get_rails_adapter()

    try:
        result = adapter.transfer_p2p(
            sender_paynow_id=sender_user.paynow_id,
            recipient_paynow_id=resolved_recipient,
            amount=amount_dec,
            reference=reference,
            creds=creds,
            description=description,
        )
    except NotImplementedError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if result.get("paynow_transfer_ref"):
        tx.paynow_transfer_ref = result["paynow_transfer_ref"]
    tx.status = result.get("status", "pending")
    tx.transaction_metadata = {
        "adapter": adapter.name,
        "rails_raw": result.get("raw", {}),
    }

    # Audit-only ledger entry. balance_after is set to 0 — the column exists
    # for the legacy float model and is preserved for receipt history, but
    # carries no semantic meaning post-pivot.
    if account_id:
        db.add(
            models.LedgerEntry(
                transaction_id=tx.id,
                account_id=account_id,
                amount=amount_dec,
                direction="debit",
                balance_after=Decimal(0),
            )
        )

    record_event(
        db,
        source="system",
        event_type="transaction.rails_transfer_initiated",
        subject_type="transaction",
        subject_id=tx.id,
        actor_user_id=sender_user.id,
        payload={
            "adapter": adapter.name,
            "amount": str(amount_dec),
            "currency": currency,
            "sender_paynow_id": sender_user.paynow_id,
            "recipient_paynow_id": resolved_recipient,
            "reference": tx.paynow_transfer_ref,
            "status": tx.status,
        },
    )

    db.commit()
    db.refresh(tx)
    logger.info(
        f"Rails transfer initiated: tx_id={tx.id} adapter={adapter.name} "
        f"sender={sender_user.paynow_id} recipient={resolved_recipient} "
        f"amount={amount_dec} {currency} status={tx.status}"
    )
    return tx


def _complete_transaction(db: Session, transaction: models.Transaction) -> bool:
    """Mark transaction as completed atomically. No balance writes."""
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

    record_event(
        db,
        source="system",
        event_type="transaction.completed",
        subject_type="transaction",
        subject_id=transaction.id,
        actor_user_id=transaction.user_id,
        payload={
            "amount": str(transaction.amount),
            "currency": transaction.currency,
            "paynow_transfer_ref": transaction.paynow_transfer_ref,
        },
    )
    db.commit()
    logger.info(f"Transaction {transaction.id} completed")
    return True


def _fail_transaction(db: Session, transaction: models.Transaction) -> bool:
    """Mark transaction as failed atomically."""
    result = db.execute(
        update(models.Transaction)
        .where(
            models.Transaction.id == transaction.id,
            models.Transaction.status == "pending",
        )
        .values(status="failed")
    )
    if result.rowcount > 0:
        record_event(
            db,
            source="system",
            event_type="transaction.failed",
            subject_type="transaction",
            subject_id=transaction.id,
            actor_user_id=transaction.user_id,
            payload={
                "amount": str(transaction.amount),
                "currency": transaction.currency,
                "paynow_transfer_ref": transaction.paynow_transfer_ref,
            },
        )
    db.commit()
    return result.rowcount > 0
