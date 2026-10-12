import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base, get_db
from app.main import app
from app.config import settings

# Test database URL
TEST_DATABASE_URL = "mysql+pymysql://root:root123@localhost:3306/agriassist_test"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Lightweight database session for unit tests (no table recreation)."""
    # Create tables if not exists
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data for registration."""
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "phone": "+919876543216",
        "role": "farmer"
    }


@pytest.fixture
def admin_user_data():
    """Admin user data for registration."""
    return {
        "email": "admin@example.com",
        "password": "adminpass123",
        "full_name": "Admin User",
        "phone": "+919876543217",
        "role": "admin"
    }


@pytest.fixture
def officer_user_data():
    """Officer user data for registration."""
    return {
        "email": "officer@example.com",
        "password": "officerpass123",
        "full_name": "Officer User",
        "phone": "+919876543218",
        "role": "officer"
    }


@pytest.fixture
def auth_headers(client, test_user_data):
    """Create authentication headers for a test user."""
    # Register user
    client.post("/auth/register", json=test_user_data)
    
    # Login to get token
    response = client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
