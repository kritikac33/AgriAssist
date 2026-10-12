"""
Marketplace router - listings and messaging (REQ-35 to REQ-38).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models import User, Listing, Message, MarketPrice, UserRole
from app.schemas import (
    ListingCreate, ListingUpdate, ListingResponse,
    MessageCreate, MessageResponse
)
from app.auth import get_current_active_user
from app.utils import haversine_distance

router = APIRouter(prefix="/listings", tags=["marketplace"])


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    crop_name: str,
    quantity_quintals: Decimal,
    price_per_quintal: Decimal,
    unit: str = "quintal",
    location: Optional[str] = None,
    latitude: Optional[Decimal] = None,
    longitude: Optional[Decimal] = None,
    description: Optional[str] = None,
    file: Optional[UploadFile] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new listing (farmer only)."""
    if current_user.role != UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only farmers can create listings"
        )

    # Handle photo upload if provided
    photo_path = None
    if file:
        import os
        import uuid
        UPLOAD_DIR = "app/static/uploads/listings"
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        contents = file.file.read()
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_extension}"
        photo_path = os.path.join(UPLOAD_DIR, filename)

        with open(photo_path, 'wb') as f:
            f.write(contents)

    listing = Listing(
        seller_id=current_user.id,
        crop_name=crop_name,
        quantity_quintals=quantity_quintals,
        price_per_quintal=price_per_quintal,
        unit=unit,
        location=location,
        latitude=latitude,
        longitude=longitude,
        photo_path=photo_path,
        description=description,
        status="open"
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    # Add market price benchmark (REQ-37)
    market_price = db.query(MarketPrice).filter(
        MarketPrice.crop_name == crop_name
    ).order_by(desc(MarketPrice.date_recorded)).first()

    if market_price:
        listing.market_price_benchmark = market_price.price_per_quintal
        listing.market_price_updated = market_price.date_recorded

        # Determine price label
        if price_per_quintal < market_price.price_per_quintal * Decimal("0.9"):
            listing.price_label = "below"
        elif price_per_quintal > market_price.price_per_quintal * Decimal("1.1"):
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
    lat: Optional[float] = Query(None, description="Latitude for distance filtering"),
    lon: Optional[float] = Query(None, description="Longitude for distance filtering"),
    max_distance_km: Optional[float] = Query(None, description="Maximum distance in km"),
    sort_by: Optional[str] = Query("newest", description="Sort by: newest, price, distance"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get listings with filters and sorting."""
    query = db.query(Listing).filter(Listing.status == "open")

    # Apply filters
    if crop:
        query = query.filter(Listing.crop_name.ilike(f"%{crop}%"))
    if min_price:
        query = query.filter(Listing.price_per_quintal >= min_price)
    if max_price:
        query = query.filter(Listing.price_per_quintal <= max_price)

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
    if sort_by == "price":
        listings.sort(key=lambda x: x.price_per_quintal)
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

    return listings


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
    """Send a message about a listing (farmer <-> buyer)."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    # Validate that user is either seller or buyer
    if current_user.role not in [UserRole.FARMER, UserRole.BUYER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only farmers and buyers can send messages"
        )

    message = Message(
        listing_id=listing_id,
        sender_id=current_user.id,
        content=message_data.content
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.get("/{listing_id}/messages", response_model=List[MessageResponse])
def get_messages(
    listing_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all messages for a listing."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    # Only seller and involved buyers can view messages
    if current_user.id != listing.seller_id and current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller and buyers can view messages"
        )

    messages = db.query(Message).filter(
        Message.listing_id == listing_id
    ).order_by(Message.created_at.asc()).all()

    return messages
