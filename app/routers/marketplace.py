"""
Marketplace router - listings and messaging (REQ-35 to REQ-38).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, or_
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models import User, Listing, Message, MarketPrice, NotificationLog, UserRole
from app.schemas import (
    ListingCreate, ListingUpdate, ListingResponse,
    MessageCreate, MessageResponse
)
from app.auth import get_current_active_user
from app.utils import haversine_distance

router = APIRouter(prefix="/listings", tags=["marketplace"])


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing_data: ListingCreate = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new listing (farmer only)."""
    if current_user.role != UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only farmers can create listings"
        )

    listing = Listing(
        seller_id=current_user.id,
        crop_name=listing_data.crop_name,
        quantity_quintals=listing_data.quantity_quintals,
        price_per_quintal=listing_data.price_per_quintal,
        unit=listing_data.unit,
        location=listing_data.location,
        latitude=listing_data.latitude,
        longitude=listing_data.longitude,
        description=listing_data.description,
        status="open"
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    # Add market price benchmark (REQ-37)
    market_price = db.query(MarketPrice).filter(
        MarketPrice.crop_name == listing_data.crop_name
    ).order_by(desc(MarketPrice.date_recorded)).first()

    if market_price:
        listing.market_price_benchmark = market_price.price_per_quintal
        listing.market_price_updated = market_price.date_recorded

        # Determine price label
        if listing_data.price_per_quintal < market_price.price_per_quintal * Decimal("0.9"):
            listing.price_label = "below"
        elif listing_data.price_per_quintal > market_price.price_per_quintal * Decimal("1.1"):
            listing.price_label = "above"
        else:
            listing.price_label = "near"

    db.commit()
    db.refresh(listing)

    return listing


@router.get("/", response_model=List[ListingResponse])
def get_listings(
    crop: Optional[str] = Query(None, description="Filter by crop name"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price per quintal"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price per quintal"),
    min_quantity: Optional[Decimal] = Query(None, ge=0, description="Minimum available quantity in quintals"),
    seller: Optional[str] = Query(None, description="Search seller display name"),
    lat: Optional[float] = Query(None, description="Latitude for distance filtering"),
    lon: Optional[float] = Query(None, description="Longitude for distance filtering"),
    max_distance_km: Optional[float] = Query(None, description="Maximum distance in km"),
    sort_by: Optional[str] = Query("newest", description="Sort by: newest, price, distance"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get listings with filters and sorting."""
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="Minimum price cannot exceed maximum price")
    query = db.query(Listing).options(joinedload(Listing.seller)).filter(
        Listing.status == "open", Listing.quantity_quintals > 0
    )
    if current_user.role == UserRole.BUYER:
        query = query.filter(Listing.seller_id != current_user.id)

    # Apply filters
    if crop:
        query = query.filter(or_(Listing.crop_name.ilike(f"%{crop.strip()}%"), Listing.location.ilike(f"%{crop.strip()}%")))
    if min_price is not None:
        query = query.filter(Listing.price_per_quintal >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price_per_quintal <= max_price)
    if min_quantity is not None:
        query = query.filter(Listing.quantity_quintals >= min_quantity)
    if seller:
        query = query.filter(Listing.seller.has(User.full_name.ilike(f"%{seller.strip()}%")))

    listings = query.all()

    # Distance filtering
    if lat is not None and lon is not None:
        if max_distance_km is None:
            max_distance_km = 100.0  # Default 100km

        filtered_listings = []
        for listing in listings:
            if listing.latitude and listing.longitude:
                distance = haversine_distance(
                    lat, lon,
                    float(listing.latitude), float(listing.longitude)
                )
                if distance <= max_distance_km:
                    # Add distance as a temporary attribute
                    listing._distance = distance
                    filtered_listings.append(listing)
        listings = filtered_listings

    # Sorting
    if sort_by in {"price", "price_asc"}:
        listings.sort(key=lambda x: x.price_per_quintal)
    elif sort_by == "price_desc":
        listings.sort(key=lambda x: x.price_per_quintal, reverse=True)
    elif sort_by == "quantity":
        listings.sort(key=lambda x: x.quantity_quintals, reverse=True)
    elif sort_by == "distance" and lat is not None and lon is not None:
        listings.sort(key=lambda x: getattr(x, '_distance', float('inf')))
    else:  # newest
        listings.sort(key=lambda x: x.created_at, reverse=True)

    # Add market price benchmarks to all listings (REQ-37)
    for listing in listings:
        if not getattr(listing, 'market_price_benchmark', None):
            market_price = db.query(MarketPrice).filter(
                MarketPrice.crop_name == listing.crop_name
            ).order_by(desc(MarketPrice.date_recorded)).first()

            if market_price:
                listing.market_price_benchmark = market_price.price_per_quintal
                listing.market_price_updated = market_price.date_recorded

                if listing.price_per_quintal < market_price.price_per_quintal * Decimal("0.9"):
                    listing.price_label = "below"
                elif listing.price_per_quintal > market_price.price_per_quintal * Decimal("1.1"):
                    listing.price_label = "above"
                else:
                    listing.price_label = "near"

    return listings[offset:offset + limit]


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(
    listing_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific listing."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    # Add market price benchmark if not present
    if not getattr(listing, 'market_price_benchmark', None):
        market_price = db.query(MarketPrice).filter(
            MarketPrice.crop_name == listing.crop_name
        ).order_by(desc(MarketPrice.date_recorded)).first()

        if market_price:
            listing.market_price_benchmark = market_price.price_per_quintal
            listing.market_price_updated = market_price.date_recorded

            if listing.price_per_quintal < market_price.price_per_quintal * Decimal("0.9"):
                listing.price_label = "below"
            elif listing.price_per_quintal > market_price.price_per_quintal * Decimal("1.1"):
                listing.price_label = "above"
            else:
                listing.price_label = "near"

    return listing


@router.patch("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    listing_update: ListingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a listing (seller only)."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    if listing.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own listings"
        )

    # Update fields
    if listing_update.status is not None:
        listing.status = listing_update.status
    if listing_update.price_per_quintal is not None:
        listing.price_per_quintal = listing_update.price_per_quintal
    if listing_update.quantity_quintals is not None:
        listing.quantity_quintals = listing_update.quantity_quintals
    if listing_update.description is not None:
        listing.description = listing_update.description

    db.commit()
    db.refresh(listing)

    return listing


@router.post("/{listing_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    listing_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Persist a listing conversation scoped to the buyer and seller."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if current_user.role == UserRole.BUYER:
        buyer_id = current_user.id
        if current_user.id == listing.seller_id:
            raise HTTPException(status_code=400, detail="A seller cannot start a buyer conversation with themselves")
    elif current_user.role == UserRole.FARMER and current_user.id == listing.seller_id:
        buyer_id = message_data.recipient_buyer_id
        if not buyer_id:
            buyer_id = db.query(Message.buyer_id).filter(Message.listing_id == listing_id, Message.buyer_id.isnot(None)).order_by(Message.created_at.desc()).scalar()
        buyer = db.query(User).filter(User.id == buyer_id, User.role == UserRole.BUYER).first() if buyer_id else None
        started_thread = db.query(Message.id).filter(Message.listing_id == listing_id, Message.sender_id == buyer_id).first() if buyer_id else None
        if not buyer or not started_thread:
            raise HTTPException(status_code=400, detail="Select a buyer who has started a conversation on this listing")
    else:
        raise HTTPException(status_code=403, detail="Only the listing farmer and buyers can message about this listing")

    message = Message(listing_id=listing_id, buyer_id=buyer_id, sender_id=current_user.id, content=message_data.content.strip())
    if not message.content:
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    db.add(message)
    recipient_id = listing.seller_id if current_user.role == UserRole.BUYER else buyer_id
    db.add(NotificationLog(user_id=recipient_id, channel="in_app", subject="New marketplace message", content=f"{current_user.full_name} sent a message about {listing.crop_name}.", related_type="listing", related_id=listing.id, status="sent"))
    db.commit()
    db.refresh(message)
    return message


@router.get("/{listing_id}/messages", response_model=List[MessageResponse])
def get_messages(
    listing_id: int,
    buyer_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Return only the requesting buyer's thread, or the seller's selected thread."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    query = db.query(Message).filter(Message.listing_id == listing_id)
    if current_user.role == UserRole.BUYER:
        if current_user.id == listing.seller_id:
            raise HTTPException(status_code=403, detail="Listing sellers must use their farmer account")
        query = query.filter(Message.buyer_id == current_user.id)
    elif current_user.role == UserRole.FARMER and current_user.id == listing.seller_id:
        if buyer_id is not None:
            query = query.filter(Message.buyer_id == buyer_id)
    else:
        raise HTTPException(status_code=403, detail="Only the listing farmer and participating buyers can view messages")
    messages = query.order_by(Message.created_at.asc(), Message.id.asc()).all()
    if current_user.role == UserRole.BUYER:
        unread = [message for message in messages if message.sender_id != current_user.id and message.read_at is None]
        for message in unread:
            message.read_at = datetime.utcnow()
        if unread:
            db.commit()
    return messages
