"""Buyer-specific shopping data backed by the authenticated account."""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_active_user
from app.database import get_db
from app.models import BuyerAddress, BuyerCartItem, Listing, Message, NotificationLog, SavedListing, SupportTicket, Transaction, User, UserRole

router = APIRouter(prefix="/buyer", tags=["buyer"])


def require_buyer(user: User = Depends(get_current_active_user)) -> User:
    if user.role != UserRole.BUYER:
        raise HTTPException(status_code=403, detail="This feature is available to buyers")
    return user


class CartItemInput(BaseModel):
    listing_id: int
    quantity_quintals: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class CartQuantityInput(BaseModel):
    quantity_quintals: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class BuyerAddressInput(BaseModel):
    label: str = Field(default="Home", min_length=1, max_length=80)
    recipient_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=7, max_length=20)
    address_line1: str = Field(min_length=3, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=4, max_length=20)
    delivery_instructions: str | None = Field(default=None, max_length=2000)
    is_default: bool = False


class BuyerAddressUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=80)
    recipient_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    address_line1: str | None = Field(default=None, min_length=3, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, min_length=4, max_length=20)
    delivery_instructions: str | None = Field(default=None, max_length=2000)
    is_default: bool | None = None


class SupportTicketInput(BaseModel):
    transaction_id: int | None = None
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=10, max_length=5000)


def listing_payload(listing: Listing) -> dict:
    return {
        "id": listing.id,
        "crop_name": listing.crop_name,
        "quantity_quintals": listing.quantity_quintals,
        "price_per_quintal": listing.price_per_quintal,
        "unit": listing.unit,
        "location": listing.location,
        "description": listing.description,
        "photo_path": listing.photo_path,
        "status": listing.status,
        "created_at": listing.created_at,
        "seller_id": listing.seller_id,
        "seller_name": listing.seller.full_name if listing.seller else None,
    }


def cart_payload(item: BuyerCartItem) -> dict:
    listing = item.listing
    available = bool(listing and listing.status == "open" and listing.quantity_quintals > 0)
    price = listing.price_per_quintal if listing else Decimal("0")
    return {
        "id": item.id,
        "listing_id": item.listing_id,
        "quantity_quintals": item.quantity_quintals,
        "available": available,
        "listing": listing_payload(listing) if listing else None,
        "subtotal": (item.quantity_quintals * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    }


@router.get("/dashboard")
def get_buyer_dashboard(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.buyer_id == user.id).all()
    messages = db.query(Message).filter(Message.buyer_id == user.id).count()
    unread_messages = db.query(Message).filter(Message.buyer_id == user.id, Message.sender_id != user.id, Message.read_at.is_(None)).count()
    cart_count = db.query(BuyerCartItem).filter(BuyerCartItem.buyer_id == user.id).count()
    saved_count = db.query(SavedListing).filter(SavedListing.buyer_id == user.id).count()
    return {
        "buyer_name": user.full_name,
        "active_orders": sum(1 for order in transactions if order.status in {"initiated", "confirmed", "processing", "shipped", "ready_for_pickup"}),
        "awaiting_payment": sum(1 for order in transactions if order.status == "initiated"),
        "in_fulfillment": sum(1 for order in transactions if order.status in {"processing", "shipped", "ready_for_pickup"}),
        "delivered_orders": sum(1 for order in transactions if order.status == "delivered"),
        "paid_purchase_value": sum((order.total_amount for order in transactions if order.status in {"confirmed", "processing", "shipped", "ready_for_pickup", "delivered"}), Decimal("0")),
        "order_count": len(transactions),
        "message_count": messages,
        "cart_item_count": cart_count,
        "saved_listing_count": saved_count,
        "unread_message_count": unread_messages,
        "unread_tracking_available": True,
    }


@router.get("/cart")
def get_cart(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    items = db.query(BuyerCartItem).options(joinedload(BuyerCartItem.listing).joinedload(Listing.seller)).filter(BuyerCartItem.buyer_id == user.id).order_by(BuyerCartItem.created_at.desc()).all()
    payload = [cart_payload(item) for item in items]
    return {"items": payload, "subtotal": sum((item["subtotal"] for item in payload), Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)}


@router.post("/cart", status_code=status.HTTP_201_CREATED)
def add_to_cart(payload: CartItemInput, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == payload.listing_id).first()
    if not listing or listing.status != "open" or listing.quantity_quintals <= 0:
        raise HTTPException(status_code=404, detail="This listing is no longer available")
    if listing.seller_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot add your own listing to your cart")
    item = db.query(BuyerCartItem).filter(BuyerCartItem.buyer_id == user.id, BuyerCartItem.listing_id == listing.id).first()
    requested = payload.quantity_quintals + (item.quantity_quintals if item else Decimal("0"))
    if requested > listing.quantity_quintals:
        raise HTTPException(status_code=409, detail=f"Only {listing.quantity_quintals} quintals are currently available")
    if item:
        item.quantity_quintals = requested
    else:
        item = BuyerCartItem(buyer_id=user.id, listing_id=listing.id, quantity_quintals=payload.quantity_quintals)
        db.add(item)
    db.commit()
    db.refresh(item)
    return cart_payload(item)


@router.patch("/cart/{item_id}")
def update_cart_item(item_id: int, payload: CartQuantityInput, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    item = db.query(BuyerCartItem).options(joinedload(BuyerCartItem.listing).joinedload(Listing.seller)).filter(BuyerCartItem.id == item_id, BuyerCartItem.buyer_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    listing = item.listing
    if listing.status != "open" or payload.quantity_quintals > listing.quantity_quintals:
        raise HTTPException(status_code=409, detail=f"Listing availability changed. Current available quantity: {listing.quantity_quintals}")
    item.quantity_quintals = payload.quantity_quintals
    db.commit()
    db.refresh(item)
    return cart_payload(item)


@router.delete("/cart/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(item_id: int, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    item = db.query(BuyerCartItem).filter(BuyerCartItem.id == item_id, BuyerCartItem.buyer_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()


@router.delete("/cart", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    db.query(BuyerCartItem).filter(BuyerCartItem.buyer_id == user.id).delete(synchronize_session=False)
    db.commit()


@router.get("/saved")
def get_saved_listings(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    saved = db.query(SavedListing).options(joinedload(SavedListing.listing).joinedload(Listing.seller)).filter(SavedListing.buyer_id == user.id).order_by(SavedListing.created_at.desc()).all()
    return [{"id": row.id, "saved_at": row.created_at, "available": bool(row.listing and row.listing.status == "open" and row.listing.quantity_quintals > 0), "listing": listing_payload(row.listing) if row.listing else None} for row in saved]


@router.put("/saved/{listing_id}", status_code=status.HTTP_201_CREATED)
def save_listing(listing_id: int, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing or listing.seller_id == user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
    saved = db.query(SavedListing).filter(SavedListing.buyer_id == user.id, SavedListing.listing_id == listing_id).first()
    if not saved:
        saved = SavedListing(buyer_id=user.id, listing_id=listing_id)
        db.add(saved)
        db.commit()
        db.refresh(saved)
    return {"id": saved.id, "listing_id": listing_id, "saved": True}


@router.delete("/saved/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_listing(listing_id: int, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    db.query(SavedListing).filter(SavedListing.buyer_id == user.id, SavedListing.listing_id == listing_id).delete(synchronize_session=False)
    db.commit()


@router.get("/orders")
def get_buyer_orders(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    orders = db.query(Transaction).options(joinedload(Transaction.listing), joinedload(Transaction.seller)).filter(Transaction.buyer_id == user.id).order_by(Transaction.created_at.desc()).all()
    return [{
        "id": order.id,
        "order_number": f"AA-{order.id:06d}",
        "listing_id": order.listing_id,
        "crop_name": order.crop_name_snapshot or (order.listing.crop_name if order.listing else "Listing no longer available"),
        "seller_name": order.seller_name_snapshot or (order.seller.full_name if order.seller else "Farmer account unavailable"),
        "quantity_quintals": order.quantity_quintals,
        "total_amount": order.total_amount,
        "unit_price_snapshot": order.unit_price_snapshot or ((order.total_amount / order.quantity_quintals) if order.quantity_quintals else Decimal("0")),
        "status": order.status,
        "fulfillment_status": order.fulfillment_status,
        "delivery_method": order.delivery_method,
        "delivery_address_snapshot": order.delivery_address_snapshot,
        "delivery_instructions": order.delivery_instructions,
        "cancellation_requested_at": order.cancellation_requested_at,
        "cancellation_reason": order.cancellation_reason,
        "status_history": [{"event_type": event.event_type, "note": event.note, "created_at": event.created_at} for event in order.status_history],
        "payment_reference": order.razorpay_payment_id,
        "created_at": order.created_at,
    } for order in orders]


@router.get("/conversations")
def get_buyer_conversations(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    messages = db.query(Message).options(joinedload(Message.listing).joinedload(Listing.seller)).filter(Message.buyer_id == user.id).order_by(Message.created_at.desc(), Message.id.desc()).all()
    latest_by_listing = {}
    counts = {}
    unread = {}
    for message in messages:
        latest_by_listing.setdefault(message.listing_id, message)
        counts[message.listing_id] = counts.get(message.listing_id, 0) + 1
        if message.sender_id != user.id and message.read_at is None:
            unread[message.listing_id] = unread.get(message.listing_id, 0) + 1
    return [{
        "listing_id": listing_id,
        "crop_name": msg.listing.crop_name if msg.listing else "Listing unavailable",
        "seller_name": msg.listing.seller.full_name if msg.listing and msg.listing.seller else "Farmer account unavailable",
        "last_message": msg.content,
        "last_message_at": msg.created_at,
        "message_count": counts[listing_id],
        "unread_count": unread.get(listing_id, 0),
    } for listing_id, msg in latest_by_listing.items()]


@router.get("/addresses")
def get_addresses(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    return db.query(BuyerAddress).filter(BuyerAddress.buyer_id == user.id).order_by(BuyerAddress.is_default.desc(), BuyerAddress.created_at.desc()).all()


@router.post("/addresses", status_code=status.HTTP_201_CREATED)
def create_address(payload: BuyerAddressInput, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    if payload.is_default:
        db.query(BuyerAddress).filter(BuyerAddress.buyer_id == user.id).update({BuyerAddress.is_default: 0}, synchronize_session=False)
    address = BuyerAddress(buyer_id=user.id, **payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.patch("/addresses/{address_id}")
def update_address(address_id: int, payload: BuyerAddressUpdate, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    address = db.query(BuyerAddress).filter(BuyerAddress.id == address_id, BuyerAddress.buyer_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Delivery address not found")
    values = payload.model_dump(exclude_unset=True)
    if values.get("is_default"):
        db.query(BuyerAddress).filter(BuyerAddress.buyer_id == user.id, BuyerAddress.id != address_id).update({BuyerAddress.is_default: 0}, synchronize_session=False)
    for key, value in values.items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    address = db.query(BuyerAddress).filter(BuyerAddress.id == address_id, BuyerAddress.buyer_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Delivery address not found")
    db.delete(address)
    db.commit()


@router.get("/notifications")
def get_notifications(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    return db.query(NotificationLog).filter(NotificationLog.user_id == user.id).order_by(NotificationLog.created_at.desc()).limit(100).all()


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    notification = db.query(NotificationLog).filter(NotificationLog.id == notification_id, NotificationLog.user_id == user.id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = 1
    db.commit()
    return {"id": notification.id, "is_read": True}


@router.post("/support", status_code=status.HTTP_201_CREATED)
def create_support_ticket(payload: SupportTicketInput, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    if payload.transaction_id is not None and not db.query(Transaction.id).filter(Transaction.id == payload.transaction_id, Transaction.buyer_id == user.id).first():
        raise HTTPException(status_code=404, detail="Order not found")
    ticket = SupportTicket(buyer_id=user.id, **payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/support")
def get_support_tickets(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    return db.query(SupportTicket).filter(SupportTicket.buyer_id == user.id).order_by(SupportTicket.created_at.desc()).all()
