"""
Transactions router - Razorpay payment integration (Feature G).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from app.database import get_db
from app.models import User, Listing, Transaction, TransactionStatusHistory, NotificationLog, BuyerAddress, UserRole
from app.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, PaymentVerificationRequest
from app.auth import get_current_active_user
from app.integrations.payments import get_razorpay_client
from app.config import settings

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a transaction and Razorpay order (buyer only)."""
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyers can create transactions"
        )

    # Get listing
    listing = db.query(Listing).filter(Listing.id == transaction_data.listing_id).with_for_update().first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    if listing.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot purchase your own listing")

    if listing.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing is not open for transactions"
        )

    # Omitted quantity means the full listed quantity.
    quantity = transaction_data.quantity_quintals if transaction_data.quantity_quintals is not None else listing.quantity_quintals
    if quantity > listing.quantity_quintals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available quantity"
        )

    address = None
    delivery_snapshot = None
    if transaction_data.delivery_method == "delivery":
        if not transaction_data.delivery_address_id:
            raise HTTPException(status_code=422, detail="Choose a saved delivery address")
        address = db.query(BuyerAddress).filter(BuyerAddress.id == transaction_data.delivery_address_id, BuyerAddress.buyer_id == current_user.id).first()
        if not address:
            raise HTTPException(status_code=404, detail="Delivery address not found")
        delivery_snapshot = {key: getattr(address, key) for key in ("label", "recipient_name", "phone", "address_line1", "address_line2", "city", "state", "postal_code")}

    # Calculate total amount
    total_amount = (quantity * listing.price_per_quintal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Create Razorpay order if keys are configured
    razorpay_client = get_razorpay_client()
    razorpay_order_id = None

    if razorpay_client.is_mock:
        raise HTTPException(status_code=503, detail="Online payments are unavailable until Razorpay credentials and SDK are configured")

    if not razorpay_client.is_mock:
        order_id, error = razorpay_client.create_order(
            amount=float(total_amount),
            currency="INR",
            notes={"listing_id": listing.id, "buyer_id": current_user.id}
        )
        if error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Razorpay order: {error}"
            )
        razorpay_order_id = order_id

    # Create transaction record
    transaction = Transaction(
        listing_id=listing.id,
        crop_name_snapshot=listing.crop_name,
        seller_name_snapshot=listing.seller.full_name if listing.seller else None,
        unit_price_snapshot=listing.price_per_quintal,
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
        razorpay_order_id=razorpay_order_id,
        quantity_quintals=quantity,
        total_amount=total_amount,
        status="initiated",
        delivery_method=transaction_data.delivery_method,
        delivery_address_snapshot=delivery_snapshot,
        delivery_instructions=transaction_data.delivery_instructions or (address.delivery_instructions if address else None),
        fulfillment_status="awaiting_payment",
        inventory_reserved=1,
    )
    listing.quantity_quintals -= quantity
    if listing.quantity_quintals <= 0:
        listing.status = "sold_out"
    db.add(transaction)
    db.flush()
    db.add(TransactionStatusHistory(transaction_id=transaction.id, actor_id=current_user.id, event_type="initiated", note="Payment order created; inventory reserved"))
    for user_id, subject in ((current_user.id, "Order awaiting payment"), (listing.seller_id, "New order awaiting payment")):
        db.add(NotificationLog(user_id=user_id, channel="in_app", subject=subject, content=f"Order for {listing.crop_name}, {quantity} quintals is awaiting payment.", related_type="transaction", related_id=transaction.id, status="sent"))
    db.commit()
    db.refresh(transaction)

    response = TransactionResponse.model_validate(transaction).model_dump()
    response["razorpay_key_id"] = settings.razorpay_key_id
    return response


@router.post("/{transaction_id}/verify", response_model=TransactionResponse)
def verify_transaction_payment(
    transaction_id: int,
    payload: PaymentVerificationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify a signed Razorpay payment and persist its confirmed status."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).with_for_update().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if current_user.id not in [transaction.buyer_id, transaction.seller_id]:
        raise HTTPException(status_code=403, detail="Only the buyer or seller can verify this transaction")
    if transaction.status == "confirmed" and transaction.razorpay_payment_id == payload.razorpay_payment_id:
        return transaction
    if transaction.status != "initiated":
        raise HTTPException(status_code=409, detail="This order is no longer awaiting payment")
    if payload.razorpay_order_id != transaction.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Payment order does not match this transaction")
    client = get_razorpay_client()
    if client.is_mock:
        raise HTTPException(status_code=503, detail="Payment verification is unavailable in demo mode")
    if not client.verify_payment_signature(payload.razorpay_payment_id, payload.razorpay_order_id, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment signature could not be verified")
    payment = client.fetch_payment(payload.razorpay_payment_id)
    if not payment or payment.get("status") != "captured":
        raise HTTPException(status_code=409, detail="Payment has not been captured")
    if payment.get("order_id") != transaction.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Captured payment belongs to a different order")
    if int(payment.get("amount", 0)) != int(transaction.total_amount * 100) or payment.get("currency") != "INR":
        raise HTTPException(status_code=400, detail="Captured amount does not match this transaction")
    transaction.razorpay_payment_id = payload.razorpay_payment_id
    transaction.status = "confirmed"
    transaction.fulfillment_status = "confirmed"
    transaction.inventory_reserved = 0
    db.add(TransactionStatusHistory(transaction_id=transaction.id, actor_id=current_user.id, event_type="confirmed", note="Razorpay payment captured and verified"))
    for user_id, subject in ((transaction.buyer_id, "Payment confirmed"), (transaction.seller_id, "Order paid")):
        if user_id:
            db.add(NotificationLog(user_id=user_id, channel="in_app", subject=subject, content=f"Payment confirmed for order AA-{transaction.id:06d}.", related_type="transaction", related_id=transaction.id, status="sent"))
    db.commit()
    db.refresh(transaction)
    response = TransactionResponse.model_validate(transaction).model_dump()
    response["razorpay_key_id"] = settings.razorpay_key_id
    return response


@router.get("/{transaction_id}/verify", response_model=TransactionResponse)
def verify_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify payment status via Razorpay polling (no webhooks)."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Only buyer or seller can verify
    if current_user.id not in [transaction.buyer_id, transaction.seller_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the buyer or seller can verify this transaction"
        )

    razorpay_client = get_razorpay_client()

    if transaction.razorpay_payment_id and not razorpay_client.is_mock:
        # Fetch real payment status from Razorpay
        payment = razorpay_client.fetch_payment(transaction.razorpay_payment_id)

        if payment:
            payment_status = payment.get("status")
            if payment_status == "captured":
                transaction.status = "confirmed"
            elif payment_status == "failed":
                transaction.status = "failed"
            elif payment_status == "refunded":
                transaction.status = "refunded"

            db.commit()
            db.refresh(transaction)

    return transaction


@router.patch("/{transaction_id}/status", response_model=TransactionResponse)
def update_transaction_status(
    transaction_id: int,
    status_update: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually update transaction status (farmer/admin only).
    Useful for manual completion or refund alongside Razorpay verification.
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Only seller or admin can update status
    if current_user.role not in [UserRole.ADMIN, UserRole.FARMER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and farmers can update transaction status"
        )

    if current_user.role == UserRole.FARMER and transaction.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own transactions"
        )

    # A seller cannot mark a payment confirmed/completed by hand. Confirmation is only set by the signed gateway verification flow.
    if status_update.status != "failed":
        raise HTTPException(status_code=400, detail="Payment status can only be confirmed by verified Razorpay payment data")

    if transaction.status in {"confirmed", "completed", "processing", "shipped", "ready_for_pickup", "delivered"}:
        raise HTTPException(status_code=409, detail="Paid orders cannot be manually marked failed")
    if transaction.inventory_reserved and transaction.listing:
        transaction.listing.quantity_quintals += transaction.quantity_quintals
        if transaction.listing.status == "sold_out":
            transaction.listing.status = "open"
        transaction.inventory_reserved = 0
    transaction.status = "failed"
    transaction.fulfillment_status = "cancelled"
    db.add(TransactionStatusHistory(transaction_id=transaction.id, actor_id=current_user.id, event_type="failed", note="Seller marked unpaid transaction failed"))
    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get transactions for the current user (as buyer or seller)."""
    transactions = db.query(Transaction).filter(
        (Transaction.buyer_id == current_user.id) |
        (Transaction.seller_id == current_user.id)
    ).order_by(Transaction.created_at.desc()).all()

    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific transaction."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Only buyer or seller can view
    if current_user.id not in [transaction.buyer_id, transaction.seller_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the buyer or seller can view this transaction"
        )

    return transaction


@router.post("/{transaction_id}/cancel", response_model=TransactionResponse)
def cancel_unpaid_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cancel an unpaid checkout and release its reserved listing quantity."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).with_for_update().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Order not found")
    if transaction.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the buyer can cancel this checkout")
    if transaction.status == "cancelled":
        return transaction
    if transaction.status != "initiated" or transaction.razorpay_payment_id:
        raise HTTPException(status_code=409, detail="Paid or completed orders must use a cancellation request")
    if transaction.inventory_reserved and transaction.listing:
        transaction.listing.quantity_quintals += transaction.quantity_quintals
        if transaction.listing.status == "sold_out":
            transaction.listing.status = "open"
        transaction.inventory_reserved = 0
    transaction.status = "cancelled"
    transaction.fulfillment_status = "cancelled"
    transaction.cancellation_reason = "Buyer cancelled before payment"
    db.add(TransactionStatusHistory(transaction_id=transaction.id, actor_id=current_user.id, event_type="cancelled", note=transaction.cancellation_reason))
    db.add(NotificationLog(user_id=transaction.seller_id, channel="in_app", subject="Unpaid order cancelled", content=f"Buyer cancelled order AA-{transaction.id:06d}; reserved quantity was released.", related_type="transaction", related_id=transaction.id, status="sent"))
    db.commit()
    db.refresh(transaction)
    return transaction


@router.post("/{transaction_id}/cancellation-request", response_model=TransactionResponse)
def request_order_cancellation(
    transaction_id: int,
    payload: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).with_for_update().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Order not found")
    if transaction.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the buyer can request cancellation")
    if transaction.status not in {"confirmed", "processing", "shipped", "ready_for_pickup"}:
        raise HTTPException(status_code=409, detail="This order cannot receive a paid-order cancellation request")
    reason = str(payload.get("reason", "")).strip()
    if len(reason) < 5 or len(reason) > 2000:
        raise HTTPException(status_code=422, detail="Provide a cancellation reason between 5 and 2000 characters")
    transaction.cancellation_reason = reason
    transaction.cancellation_requested_at = datetime.utcnow()
    db.add(TransactionStatusHistory(transaction_id=transaction.id, actor_id=current_user.id, event_type="cancellation_requested", note=reason))
    db.add(NotificationLog(user_id=transaction.seller_id, channel="in_app", subject="Buyer requested order cancellation", content=f"Cancellation requested for AA-{transaction.id:06d}: {reason}", related_type="transaction", related_id=transaction.id, status="sent"))
    db.commit()
    db.refresh(transaction)
    return transaction


@router.patch("/{transaction_id}/fulfillment", response_model=TransactionResponse)
def update_fulfillment(
    transaction_id: int,
    payload: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).with_for_update().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role != UserRole.ADMIN and (current_user.role != UserRole.FARMER or transaction.seller_id != current_user.id):
        raise HTTPException(status_code=403, detail="Only the listing farmer can update fulfilment")
    if transaction.status not in {"confirmed", "processing", "shipped", "ready_for_pickup"}:
        raise HTTPException(status_code=409, detail="Only paid orders can be fulfilled")
    next_state = str(payload.get("fulfillment_status", ""))
    allowed = {
        "confirmed": {"processing", "ready_for_pickup"},
        "processing": {"shipped", "ready_for_pickup"},
        "shipped": {"delivered"},
        "ready_for_pickup": {"delivered"},
    }
    current_state = transaction.fulfillment_status
    if next_state not in allowed.get(current_state, set()):
        raise HTTPException(status_code=409, detail=f"Cannot move fulfilment from {current_state} to {next_state}")
    if next_state in {"shipped", "ready_for_pickup"}:
        if next_state == "shipped" and transaction.delivery_method != "delivery":
            raise HTTPException(status_code=409, detail="Only delivery orders can be marked shipped")
        if next_state == "ready_for_pickup" and transaction.delivery_method != "pickup":
            raise HTTPException(status_code=409, detail="Only pickup orders can be marked ready for pickup")
    transaction.fulfillment_status = next_state
    transaction.status = next_state
    db.add(TransactionStatusHistory(transaction_id=transaction.id, actor_id=current_user.id, event_type=next_state, note="Seller fulfilment update"))
    if transaction.buyer_id:
        db.add(NotificationLog(user_id=transaction.buyer_id, channel="in_app", subject="Order status updated", content=f"Order AA-{transaction.id:06d} is now {next_state.replace('_', ' ')}.", related_type="transaction", related_id=transaction.id, status="sent"))
    db.commit()
    db.refresh(transaction)
    return transaction
