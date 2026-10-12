"""
Transactions router - Razorpay payment integration (Feature G).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models import User, Listing, Transaction, UserRole
from app.schemas import TransactionCreate, TransactionUpdate, TransactionResponse
from app.auth import get_current_active_user
from app.integrations.payments import get_razorpay_client

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
    listing = db.query(Listing).filter(Listing.id == transaction_data.listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    if listing.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing is not open for transactions"
        )

    # Validate quantity
    if transaction_data.quantity_quintals > listing.quantity_quintals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available quantity"
        )

    # Calculate total amount
    total_amount = transaction_data.quantity_quintals * listing.price_per_quintal

    # Create Razorpay order if keys are configured
    razorpay_client = get_razorpay_client()
    razorpay_order_id = None

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
    else:
        # Mock order ID for testing
        razorpay_order_id = f"order_mock_{listing.id}_{current_user.id}"

    # Create transaction record
    transaction = Transaction(
        listing_id=listing.id,
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
        razorpay_order_id=razorpay_order_id,
        quantity_quintals=transaction_data.quantity_quintals,
        total_amount=total_amount,
        status="initiated"
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


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
    elif razorpay_client.is_mock:
        # Mock verification - assume success after initiated
        if transaction.status == "initiated":
            transaction.status = "confirmed"
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

    # Validate status transition
    valid_statuses = ["initiated", "confirmed", "completed", "failed", "refunded"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    transaction.status = status_update.status
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
