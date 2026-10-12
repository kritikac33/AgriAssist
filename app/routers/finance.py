"""
Finance router - finance tracker for farms.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from app.database import get_db
from app.models import User, Farm, FinanceEntry, UserRole
from app.schemas import FinanceEntryCreate, FinanceEntryResponse, FinanceSummaryResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/finance-entries", tags=["finance"])


@router.post("/", response_model=FinanceEntryResponse, status_code=status.HTTP_201_CREATED)
def create_finance_entry(
    entry_data: FinanceEntryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a finance entry for a farm."""
    # Verify farm ownership
    farm = db.query(Farm).filter(Farm.id == entry_data.farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )

    if farm.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add finance entries to your own farms"
        )

    entry = FinanceEntry(
        farm_id=entry_data.farm_id,
        entry_type=entry_data.entry_type,
        category=entry_data.category,
        amount=entry_data.amount,
        date=entry_data.date,
        notes=entry_data.notes
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry


@router.get("/", response_model=List[FinanceEntryResponse])
def get_finance_entries(
    farm_id: Optional[int] = Query(None, description="Filter by farm ID"),
    entry_type: Optional[str] = Query(None, description="Filter by entry type (income/expense)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get finance entries for the current user's farms."""
    query = db.query(FinanceEntry).join(Farm).filter(Farm.owner_id == current_user.id)

    if farm_id:
        query = query.filter(FinanceEntry.farm_id == farm_id)
    if entry_type:
        query = query.filter(FinanceEntry.entry_type == entry_type)

    entries = query.order_by(FinanceEntry.date.desc()).all()
    return entries


@router.get("/summary", response_model=FinanceSummaryResponse)
def get_finance_summary(
    farm_id: int = Query(..., description="Farm ID to get summary for"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get finance summary for a farm."""
    # Verify farm ownership
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )

    if farm.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view summaries for your own farms"
        )

    # Calculate totals
    total_income = db.query(func.sum(FinanceEntry.amount)).filter(
        and_(
            FinanceEntry.farm_id == farm_id,
            FinanceEntry.entry_type == "income"
        )
    ).scalar() or Decimal("0")

    total_expenses = db.query(func.sum(FinanceEntry.amount)).filter(
        and_(
            FinanceEntry.farm_id == farm_id,
            FinanceEntry.entry_type == "expense"
        )
    ).scalar() or Decimal("0")

    net_profit = total_income - total_expenses

    # Category breakdown
    category_query = db.query(
        FinanceEntry.category,
        FinanceEntry.entry_type,
        func.sum(FinanceEntry.amount).label("total")
    ).filter(FinanceEntry.farm_id == farm_id).group_by(
        FinanceEntry.category,
        FinanceEntry.entry_type
    ).all()

    category_breakdown = {}
    for cat, entry_type, total in category_query:
        key = f"{entry_type}_{cat}"
        category_breakdown[key] = float(total)

    # Monthly breakdown
    monthly_query = db.query(
        extract('year', FinanceEntry.date).label('year'),
        extract('month', FinanceEntry.date).label('month'),
        FinanceEntry.entry_type,
        func.sum(FinanceEntry.amount).label("total")
    ).filter(FinanceEntry.farm_id == farm_id).group_by(
        extract('year', FinanceEntry.date),
        extract('month', FinanceEntry.date),
        FinanceEntry.entry_type
    ).order_by(
        extract('year', FinanceEntry.date),
        extract('month', FinanceEntry.date)
    ).all()

    monthly_breakdown = {}
    for year, month, entry_type, total in monthly_query:
        key = f"{int(year)}-{int(month):02d}_{entry_type}"
        monthly_breakdown[key] = float(total)

    return FinanceSummaryResponse(
        farm_id=farm_id,
        total_income=total_income,
        total_expenses=total_expenses,
        net_profit=net_profit,
        category_breakdown=category_breakdown,
        monthly_breakdown=monthly_breakdown
    )


@router.get("/{entry_id}", response_model=FinanceEntryResponse)
def get_finance_entry(
    entry_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific finance entry."""
    entry = db.query(FinanceEntry).join(Farm).filter(
        and_(
            FinanceEntry.id == entry_id,
            Farm.owner_id == current_user.id
        )
    ).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finance entry not found"
        )

    return entry
