"""
Admin router - dashboard, config management, user management, audit logs (Features H & I).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from decimal import Decimal

from app.database import get_db
from app.models import (
    User, Diagnosis, OutbreakAlert, Listing, Transaction, Farm,
    SystemConfig, AuditLog, UserRole
)
from app.schemas import (
    AdminDashboardResponse, SystemConfigUpdate, SystemConfigResponse,
    UserResponse, AuditLogResponse
)
from app.auth import get_current_active_user, require_role
from app.utils import set_config_value

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get admin dashboard summary (admin only)."""
    # Total users by role
    users_by_role = {}
    for role in UserRole:
        count = db.query(func.count(User.id)).filter(User.role == role).scalar()
        users_by_role[role.value] = count

    total_users = sum(users_by_role.values())

    # Total diagnoses and low confidence count
    total_diagnoses = db.query(func.count(Diagnosis.id)).scalar() or 0
    low_confidence_diagnoses = db.query(func.count(Diagnosis.id)).filter(
        Diagnosis.confidence_score < 0.6
    ).scalar() or 0

    # Top 5 diseases
    top_diseases = db.query(
        Diagnosis.disease_name,
        func.count(Diagnosis.id).label("count")
    ).group_by(Diagnosis.disease_name).order_by(
        desc(func.count(Diagnosis.id))
    ).limit(5).all()

    top_diseases_list = [{"disease": d[0], "count": d[1]} for d in top_diseases]

    # Active alerts
    active_alerts = db.query(func.count(OutbreakAlert.id)).filter(
        OutbreakAlert.is_active == 1
    ).scalar() or 0

    # Total listings (open vs closed)
    total_listings = db.query(func.count(Listing.id)).scalar() or 0
    open_listings = db.query(func.count(Listing.id)).filter(
        Listing.status == "open"
    ).scalar() or 0
    closed_listings = db.query(func.count(Listing.id)).filter(
        Listing.status == "closed"
    ).scalar() or 0

    # Total transaction volume (completed transactions)
    total_transaction_volume = db.query(func.sum(Transaction.total_amount)).filter(
        Transaction.status == "completed"
    ).scalar() or Decimal("0")

    # Total farms
    total_farms = db.query(func.count(Farm.id)).scalar() or 0

    return AdminDashboardResponse(
        total_users=total_users,
        users_by_role=users_by_role,
        total_diagnoses=total_diagnoses,
        low_confidence_diagnoses=low_confidence_diagnoses,
        top_diseases=top_diseases_list,
        active_alerts=active_alerts,
        total_listings=total_listings,
        open_listings=open_listings,
        closed_listings=closed_listings,
        total_transaction_volume=total_transaction_volume,
        total_farms=total_farms
    )


@router.get("/config", response_model=List[SystemConfigResponse])
def get_system_config(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all system configuration values (admin only)."""
    configs = db.query(SystemConfig).all()
    return configs


@router.patch("/config/{config_key}", response_model=SystemConfigResponse)
def update_system_config(
    config_key: str,
    config_update: SystemConfigUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update a system configuration value (admin only)."""
    success = set_config_value(
        db,
        config_key,
        config_update.config_value,
        config_update.description
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration"
        )

    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == config_key
    ).first()

    return config


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all users with optional search/filter (admin only)."""
    query = db.query(User)

    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )

    if role:
        query = query.filter(User.role == role)

    users = query.order_by(User.created_at.desc()).all()
    return users


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(50, description="Number of logs to return"),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get recent audit logs (admin only)."""
    logs = db.query(AuditLog).order_by(
        desc(AuditLog.created_at)
    ).limit(limit).all()
    return logs
