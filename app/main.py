from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db, engine
from app.models import Base, User, UserRole
from app.schemas import UserCreate, UserResponse, Token, LoginRequest, RefreshTokenRequest
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_active_user,
    require_role
)
from app.config import settings
from app.routers import diagnoses, soil, irrigation, yield_predictions, alerts, marketplace, transactions, schemes, finance, admin, farms, crops, buyer

# Create database tables (for development - in production use Alembic migrations)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgriAssist API",
    description="AI-Powered Crop Advisory & Farm Support Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(diagnoses.router)
app.include_router(soil.router)
app.include_router(irrigation.router)
app.include_router(yield_predictions.router)
app.include_router(alerts.router)
app.include_router(marketplace.router)
app.include_router(transactions.router)
app.include_router(buyer.router)
app.include_router(schemes.router)
app.include_router(finance.router)
app.include_router(admin.router)
app.include_router(farms.router)
app.include_router(crops.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "AgriAssist API - Part 1 Backend Foundation", "status": "operational"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with hashed password
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@app.post("/auth/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and return JWT tokens."""
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@app.post("/auth/refresh", response_model=Token)
def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(refresh_data.refresh_token, credentials_exception)
    
    access_token = create_access_token(
        data={"sub": token_data.email, "role": token_data.role.value},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    new_refresh_token = create_refresh_token(
        data={"sub": token_data.email, "role": token_data.role.value}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@app.get("/admin/users")
def get_all_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Admin-only endpoint to get all users."""
    return {"message": "Admin access granted", "user_count": 0}
