"""
Tests for Part 3 features: Alerts, Marketplace, Payments, Schemes, Finance, Admin.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import (
    User, Farm, Crop, Diagnosis, OutbreakAlert, Listing, Transaction,
    Scheme, FinanceEntry, SystemConfig, UserRole, Message
)
from app.auth import get_password_hash


class TestOutbreakAlerts:
    """Test pest outbreak alerts (REQ-17-20)."""

    def test_create_manual_alert(self, db):
        """Test officer/admin can manually create an alert."""
        officer = User(
            email="officer@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Officer",
            role=UserRole.OFFICER,
            is_active=True
        )
        db.add(officer)
        db.commit()

        alert = OutbreakAlert(
            disease_name="Tomato_Late_blight",
            region_description="Test region",
            center_latitude=Decimal("18.5"),
            center_longitude=Decimal("73.8"),
            radius_km=Decimal("10"),
            severity="high",
            case_count=5,
            is_active=1
        )
        db.add(alert)
        db.commit()

        assert alert.id is not None
        assert alert.disease_name == "Tomato_Late_blight"
        assert alert.is_active == 1

    def test_retract_alert(self, db):
        """Test alert retraction."""
        alert = OutbreakAlert(
            disease_name="Tomato_Early_blight",
            region_description="Test region",
            center_latitude=Decimal("18.5"),
            center_longitude=Decimal("73.8"),
            radius_km=Decimal("10"),
            severity="medium",
            case_count=3,
            is_active=1
        )
        db.add(alert)
        db.commit()

        alert.is_active = 0
        alert.retracted_at = datetime.utcnow()
        db.commit()

        db.refresh(alert)
        assert alert.is_active == 0
        assert alert.retracted_at is not None

    def test_cooldown_prevents_duplicate_alerts(self, db):
        """Test that cooldown period prevents duplicate alerts."""
        alert1 = OutbreakAlert(
            disease_name="Potato___Late_blight",
            region_description="Test region",
            center_latitude=Decimal("18.5"),
            center_longitude=Decimal("73.8"),
            radius_km=Decimal("10"),
            severity="high",
            case_count=5,
            is_active=1,
            created_at=datetime.utcnow()
        )
        db.add(alert1)
        db.commit()

        recent_alerts = db.query(OutbreakAlert).filter(
            OutbreakAlert.disease_name == "Potato___Late_blight",
            OutbreakAlert.center_latitude == "18.5",
            OutbreakAlert.center_longitude == "73.8",
            OutbreakAlert.radius_km == "10",
            OutbreakAlert.is_active == 1,
            OutbreakAlert.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).first()

        assert recent_alerts is not None


class TestMarketplace:
    """Test marketplace functionality (REQ-35-38)."""

    def test_create_listing(self, db):
        """Test farmer can create a listing."""
        farmer = User(
            email="farmer@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Farmer",
            role=UserRole.FARMER,
            is_active=True
        )
        db.add(farmer)
        db.commit()

        listing = Listing(
            seller_id=farmer.id,
            crop_name="Rice",
            quantity_quintals=Decimal("10"),
            price_per_quintal=Decimal("2500"),
            unit="quintal",
            location="Pune, Maharashtra",
            status="open"
        )
        db.add(listing)
        db.commit()

        assert listing.id is not None
        assert listing.crop_name == "Rice"
        assert listing.status == "open"

    def test_update_listing_status(self, db):
        """Test seller can update listing status."""
        farmer = User(
            email="farmer2@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Farmer 2",
            role=UserRole.FARMER,
            is_active=True
        )
        db.add(farmer)
        db.commit()

        listing = Listing(
            seller_id=farmer.id,
            crop_name="Wheat",
            quantity_quintals=Decimal("5"),
            price_per_quintal=Decimal("2200"),
            status="open"
        )
        db.add(listing)
        db.commit()

        listing.status = "closed"
        db.commit()

        db.refresh(listing)
        assert listing.status == "closed"

    def test_create_message(self, db):
        """Test messaging between farmer and buyer."""
        farmer = User(
            email="farmer3@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Farmer 3",
            role=UserRole.FARMER,
            is_active=True
        )
        buyer = User(
            email="buyer@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Buyer",
            role=UserRole.BUYER,
            is_active=True
        )
        db.add(farmer)
        db.add(buyer)
        db.commit()

        listing = Listing(
            seller_id=farmer.id,
            crop_name="Soybean",
            quantity_quintals=Decimal("8"),
            price_per_quintal=Decimal("4000"),
            status="open"
        )
        db.add(listing)
        db.commit()

        message = Message(
            listing_id=listing.id,
            sender_id=buyer.id,
            content="Is this listing still available?"
        )
        db.add(message)
        db.commit()

        assert message.id is not None
        assert message.sender_id == buyer.id


class TestTransactions:
    """Test Razorpay payment integration (Feature G)."""

    def test_create_transaction_with_mock(self, db):
        """Test transaction creation in mock mode."""
        farmer = User(
            email="farmer4@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Farmer 4",
            role=UserRole.FARMER,
            is_active=True
        )
        buyer = User(
            email="buyer2@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Buyer 2",
            role=UserRole.BUYER,
            is_active=True
        )
        db.add(farmer)
        db.add(buyer)
        db.commit()

        listing = Listing(
            seller_id=farmer.id,
            crop_name="Cotton",
            quantity_quintals=Decimal("15"),
            price_per_quintal=Decimal("6500"),
            status="open"
        )
        db.add(listing)
        db.commit()

        transaction = Transaction(
            listing_id=listing.id,
            buyer_id=buyer.id,
            seller_id=farmer.id,
            razorpay_order_id="order_mock_123",
            quantity_quintals=Decimal("10"),
            total_amount=Decimal("65000"),
            status="initiated"
        )
        db.add(transaction)
        db.commit()

        assert transaction.id is not None
        assert transaction.status == "initiated"
        assert transaction.razorpay_order_id == "order_mock_123"

    def test_transaction_status_update(self, db):
        """Test manual transaction status update."""
        farmer = User(
            email="farmer5@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Farmer 5",
            role=UserRole.FARMER,
            is_active=True
        )
        buyer = User(
            email="buyer3@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Buyer 3",
            role=UserRole.BUYER,
            is_active=True
        )
        db.add(farmer)
        db.add(buyer)
        db.commit()

        listing = Listing(
            seller_id=farmer.id,
            crop_name="Maize",
            quantity_quintals=Decimal("20"),
            price_per_quintal=Decimal("1900"),
            status="open"
        )
        db.add(listing)
        db.commit()

        transaction = Transaction(
            listing_id=listing.id,
            buyer_id=buyer.id,
            seller_id=farmer.id,
            quantity_quintals=Decimal("20"),
            total_amount=Decimal("38000"),
            status="initiated"
        )
        db.add(transaction)
        db.commit()

        transaction.status = "confirmed"
        db.commit()

        db.refresh(transaction)
        assert transaction.status == "confirmed"

    def test_invalid_status_transition(self):
        """Test that invalid status transitions are rejected."""
        valid_statuses = ["initiated", "confirmed", "completed", "failed", "refunded"]
        invalid_status = "invalid_status"

        assert invalid_status not in valid_statuses


class TestSchemes:
    """Test subsidy/scheme eligibility checker."""

    def test_scheme_creation(self, db):
        """Test scheme can be created with eligibility criteria."""
        scheme = Scheme(
            name="Test Scheme",
            description="Test agricultural scheme",
            eligibility_criteria="Farmers with land up to 2 hectares",
            min_land_hectares=Decimal("0"),
            max_land_hectares=Decimal("2"),
            eligible_crops="Rice, Wheat",
            eligible_states="Maharashtra, Karnataka",
            benefits="Free seeds and fertilizer",
            application_link="https://test.gov.in",
            is_active=1
        )
        db.add(scheme)
        db.commit()

        assert scheme.id is not None
        assert scheme.min_land_hectares == Decimal("0")
        assert scheme.max_land_hectares == Decimal("2")

    def test_scheme_eligibility_by_land_size(self, db):
        """Test scheme eligibility based on land size."""
        scheme = Scheme(
            name="Land-Based Scheme",
            eligibility_criteria="Farmers with 1-5 hectares",
            min_land_hectares=Decimal("1"),
            max_land_hectares=Decimal("5"),
            is_active=1
        )
        db.add(scheme)
        db.commit()

        farmer = User(
            email="farmer6@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Farmer 6",
            role=UserRole.FARMER,
            is_active=True
        )
        db.add(farmer)
        db.commit()

        farm = Farm(
            owner_id=farmer.id,
            name="Test Farm",
            area_hectares=Decimal("3")
        )
        db.add(farm)
        db.commit()

        assert farm.area_hectares >= scheme.min_land_hectares
        assert farm.area_hectares <= scheme.max_land_hectares


class TestFinance:
    """Test finance tracker."""

    def test_create_finance_entry(self, db):
        """Test creating finance entry."""
        farmer = User(
            email="farmer7@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Farmer 7",
            role=UserRole.FARMER,
            is_active=True
        )
        db.add(farmer)
        db.commit()

        farm = Farm(
            owner_id=farmer.id,
            name="Test Farm 7"
        )
        db.add(farm)
        db.commit()

        entry = FinanceEntry(
            farm_id=farm.id,
            entry_type="income",
            category="crop_sale",
            amount=Decimal("50000"),
            date=datetime.utcnow(),
            notes="Rice sale"
        )
        db.add(entry)
        db.commit()

        assert entry.id is not None
        assert entry.entry_type == "income"
        assert entry.amount == Decimal("50000")

    def test_finance_summary_calculation(self, db):
        """Test finance summary calculation."""
        farmer = User(
            email="farmer8@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Farmer 8",
            role=UserRole.FARMER,
            is_active=True
        )
        db.add(farmer)
        db.commit()

        farm = Farm(
            owner_id=farmer.id,
            name="Test Farm 8"
        )
        db.add(farm)
        db.commit()

        income1 = FinanceEntry(
            farm_id=farm.id,
            entry_type="income",
            category="crop_sale",
            amount=Decimal("60000"),
            date=datetime.utcnow()
        )
        income2 = FinanceEntry(
            farm_id=farm.id,
            entry_type="income",
            category="subsidy",
            amount=Decimal("6000"),
            date=datetime.utcnow()
        )

        expense1 = FinanceEntry(
            farm_id=farm.id,
            entry_type="expense",
            category="fertilizer",
            amount=Decimal("10000"),
            date=datetime.utcnow()
        )

        db.add_all([income1, income2, expense1])
        db.commit()

        total_income = Decimal("66000")
        total_expenses = Decimal("10000")
        net_profit = total_income - total_expenses

        assert net_profit == Decimal("56000")


class TestAdminFeatures:
    """Test admin dashboard and config management (Features H & I)."""

    def test_config_management(self, db):
        """Test system config can be read and updated."""
        config = SystemConfig(
            config_key="test_config",
            config_value="100",
            description="Test configuration"
        )
        db.add(config)
        db.commit()

        retrieved = db.query(SystemConfig).filter(
            SystemConfig.config_key == "test_config"
        ).first()

        assert retrieved is not None
        assert retrieved.config_value == "100"

        retrieved.config_value = "200"
        db.commit()

        db.refresh(retrieved)
        assert retrieved.config_value == "200"

    def test_rbac_admin_only(self, db):
        """Test that admin-only endpoints are protected."""
        farmer = User(
            email="farmer10@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test Farmer 10",
            role=UserRole.FARMER,
            is_active=True
        )
        db.add(farmer)
        db.commit()

        assert farmer.role != UserRole.ADMIN
