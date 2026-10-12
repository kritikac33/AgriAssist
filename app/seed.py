"""
Seed script for AgriAssist database.
Creates demo accounts, farms, and crops for testing.
"""
import sys
import os
from decimal import Decimal
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models import (
    User, Farm, Crop, UserRole, Treatment, ProhibitedSubstance, CropNutrientRequirement,
    Scheme, SystemConfig, MarketPrice
)
from app.auth import get_password_hash


def seed_database():
    """Seed the database with demo data."""
    print("Starting database seeding...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - comment out if you want to preserve data)
        print("Clearing existing data...")
        db.query(CropNutrientRequirement).delete()
        db.query(ProhibitedSubstance).delete()
        db.query(Treatment).delete()
        db.query(Crop).delete()
        db.query(Farm).delete()
        db.query(User).delete()
        db.commit()
        
        # Create demo users
        print("Creating demo users...")
        
        # Admin
        admin = User(
            email="admin@agriassist.com",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            phone="+919876543210",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        
        # Officer
        officer = User(
            email="officer@agriassist.com",
            hashed_password=get_password_hash("officer123"),
            full_name="Agricultural Officer",
            phone="+919876543211",
            role=UserRole.OFFICER,
            is_active=True
        )
        db.add(officer)
        
        # Farmers
        farmer1 = User(
            email="farmer1@agriassist.com",
            hashed_password=get_password_hash("farmer123"),
            full_name="Ramesh Patil",
            phone="+919876543212",
            role=UserRole.FARMER,
            is_active=True
        )
        db.add(farmer1)
        
        farmer2 = User(
            email="farmer2@agriassist.com",
            hashed_password=get_password_hash("farmer123"),
            full_name="Suresh Jadhav",
            phone="+919876543213",
            role=UserRole.FARMER,
            is_active=True
        )
        db.add(farmer2)
        
        # Buyers
        buyer1 = User(
            email="buyer1@agriassist.com",
            hashed_password=get_password_hash("buyer123"),
            full_name="AgriCorp Trading",
            phone="+919876543214",
            role=UserRole.BUYER,
            is_active=True
        )
        db.add(buyer1)
        
        buyer2 = User(
            email="buyer2@agriassist.com",
            hashed_password=get_password_hash("buyer123"),
            full_name="FreshMart Foods",
            phone="+919876543215",
            role=UserRole.BUYER,
            is_active=True
        )
        db.add(buyer2)
        
        db.commit()
        db.refresh(admin)
        db.refresh(officer)
        db.refresh(farmer1)
        db.refresh(farmer2)
        db.refresh(buyer1)
        db.refresh(buyer2)
        
        # Create farms for farmers
        print("Creating farms...")
        
        # Farm 1: Near Pimpri-Chinchwad, Maharashtra
        farm1 = Farm(
            owner_id=farmer1.id,
            name="Green Valley Farm",
            location="Pimpri-Chinchwad, Pune District, Maharashtra",
            latitude=Decimal("18.6298"),
            longitude=Decimal("73.7997"),
            area_hectares=Decimal("5.5"),
            soil_type="Black Cotton Soil"
        )
        db.add(farm1)
        
        # Farm 2: Near Nashik, Maharashtra
        farm2 = Farm(
            owner_id=farmer2.id,
            name="Sahyadri Farms",
            location="Nashik, Maharashtra",
            latitude=Decimal("19.9975"),
            longitude=Decimal("73.7898"),
            area_hectares=Decimal("8.0"),
            soil_type="Red Soil"
        )
        db.add(farm2)
        
        db.commit()
        db.refresh(farm1)
        db.refresh(farm2)
        
        # Create crops
        print("Creating crops...")
        
        # Indian crops list
        indian_crops = [
            ("Rice", "Basmati", Decimal("2.5")),
            ("Wheat", "Sharbati", Decimal("3.0")),
            ("Cotton", "Bt Cotton", Decimal("4.0")),
            ("Tomato", "Hybrid", Decimal("0.5")),
            ("Sugarcane", "Co 86032", Decimal("2.0")),
            ("Soybean", "JS 9560", Decimal("3.5")),
            ("Onion", "Nasik Red", Decimal("1.0")),
            ("Grape", "Thompson Seedless", Decimal("1.5")),
            ("Maize", "Hybrid", Decimal("2.0")),
            ("Groundnut", "Bold", Decimal("1.5")),
            ("Chilli", "Guntur", Decimal("0.3")),
            ("Potato", "Kufri Jyoti", Decimal("0.8")),
            ("Banana", "Grand Naine", Decimal("1.2")),
            ("Mango", "Alphonso", Decimal("2.0")),
            ("Turmeric", "Salem", Decimal("0.5"))
        ]
        
        # Assign crops to farms
        for i, (name, variety, area) in enumerate(indian_crops):
            if i < 8:
                farm_id = farm1.id
            else:
                farm_id = farm2.id
            
            crop = Crop(
                farm_id=farm_id,
                name=name,
                variety=variety,
                planting_date=datetime(2024, 1, 1),
                expected_harvest_date=datetime(2024, 6, 30),
                area_hectares=area,
                status="active"
            )
            db.add(crop)
        
        db.commit()
        
        # Seed treatments for disease classes (matching trained model classes)
        print("Seeding treatments...")
        
        # Disease classes from trained model
        disease_classes = [
            "Tomato_healthy",
            "Tomato_Late_blight",
            "Tomato_Early_blight",
            "Potato___healthy",
            "Potato___Late_blight",
            "Potato___Early_blight",
            "Tomato_Leaf_Mold",
            "Tomato_Septoria_leaf_spot",
            "Pepper__bell___healthy",
            "Pepper__bell___Bacterial_spot"
        ]
        
        treatments_data = [
            # Tomato Late Blight
            ("Tomato_Late_blight", "chemical", "Mancozeb 75% WP", "2g per liter of water", "Spray every 7-10 days", "Wear protective gear; avoid inhalation", False),
            ("Tomato_Late_blight", "organic", "Copper oxychloride", "3g per liter of water", "Spray as preventive measure", "Safe for organic farming", True),
            # Tomato Early Blight
            ("Tomato_Early_blight", "chemical", "Chlorothalonil", "2ml per liter of water", "Spray at first sign of disease", "Avoid skin contact", False),
            ("Tomato_Early_blight", "organic", "Neem oil", "5ml per liter of water", "Spray weekly", "Safe and eco-friendly", True),
            # Tomato Leaf Mold
            ("Tomato_Leaf_Mold", "chemical", "Tebuconazole", "1ml per liter", "Spray at 7-day intervals", "Use protective equipment", False),
            ("Tomato_Leaf_Mold", "organic", "Sulphur", "2kg per hectare", "Dust or spray", "Traditional organic method", True),
            # Tomato Septoria Leaf Spot
            ("Tomato_Septoria_leaf_spot", "chemical", "Azoxystrobin", "1g per liter", "Spray every 10-14 days", "Follow label instructions", False),
            ("Tomato_Septoria_leaf_spot", "organic", "Bacillus subtilis", "10ml per liter", "Spray preventively", "Biological control agent", True),
            # Potato Late Blight
            ("Potato___Late_blight", "chemical", "Metalaxyl", "2g per kg seed", "Seed treatment before planting", "Handle with gloves", False),
            ("Potato___Late_blight", "organic", "Trichoderma", "5g per kg seed", "Seed treatment", "Biological control agent", True),
            # Potato Early Blight
            ("Potato___Early_blight", "chemical", "Iprodione", "1g per liter", "Foliar spray", "Use protective equipment", False),
            ("Potato___Early_blight", "organic", "Pseudomonas", "10ml per liter", "Soil drench", "Beneficial bacteria", True),
            # Pepper Bacterial Spot
            ("Pepper__bell___Bacterial_spot", "chemical", "Copper hydroxide", "3g per liter", "Spray every 5 days", "Copper-based fungicide", False),
            ("Pepper__bell___Bacterial_spot", "organic", "Bordeaux mixture", "1% solution", "Spray preventively", "Classic organic treatment", True),
        ]
        
        for disease_class, t_type, name, dosage, method, warning, organic in treatments_data:
            treatment = Treatment(
                disease_class=disease_class,
                treatment_type=t_type,
                treatment_name=name,
                dosage=dosage,
                application_method=method,
                safety_warning=warning,
                organic=1 if organic else 0
            )
            db.add(treatment)
        
        db.commit()
        
        # Seed prohibited substances (commonly banned agrochemicals in India)
        print("Seeding prohibited substances...")
        
        prohibited_substances = [
            ("DDT", "Organochlorine pesticide, persistent environmental pollutant", "Central Insecticides Board"),
            ("Endosulfan", "Highly toxic to humans and environment, banned in 2011", "Central Insecticides Board"),
            ("Monocrotophos", "Acute toxicity to birds and mammals", "Central Insecticides Board"),
            ("Phorate", "Highly toxic, restricted use", "Central Insecticides Board"),
            ("Carbofuran", "Toxic to birds and aquatic life", "Central Insecticides Board")
        ]
        
        for name, reason, body in prohibited_substances:
            substance = ProhibitedSubstance(
                substance_name=name,
                prohibited_reason=reason,
                regulatory_body=body
            )
            db.add(substance)
        
        db.commit()
        
        # Seed crop nutrient requirements
        print("Seeding crop nutrient requirements...")
        
        nutrient_requirements = [
            ("rice", Decimal("5.5"), Decimal("6.5"), Decimal("40"), Decimal("80"), Decimal("20"), Decimal("40"), Decimal("30"), Decimal("60")),
            ("wheat", Decimal("6.0"), Decimal("7.5"), Decimal("50"), Decimal("90"), Decimal("25"), Decimal("45"), Decimal("35"), Decimal("65")),
            ("cotton", Decimal("6.0"), Decimal("7.0"), Decimal("60"), Decimal("100"), Decimal("30"), Decimal("50"), Decimal("40"), Decimal("70")),
            ("tomato", Decimal("6.0"), Decimal("7.0"), Decimal("40"), Decimal("80"), Decimal("30"), Decimal("50"), Decimal("40"), Decimal("60")),
            ("sugarcane", Decimal("6.5"), Decimal("7.5"), Decimal("50"), Decimal("100"), Decimal("25"), Decimal("50"), Decimal("40"), Decimal("80")),
            ("soybean", Decimal("6.0"), Decimal("7.0"), Decimal("30"), Decimal("60"), Decimal("20"), Decimal("40"), Decimal("30"), Decimal("50")),
            ("onion", Decimal("6.0"), Decimal("7.0"), Decimal("50"), Decimal("80"), Decimal("30"), Decimal("50"), Decimal("40"), Decimal("60")),
            ("grape", Decimal("6.5"), Decimal("7.5"), Decimal("40"), Decimal("70"), Decimal("25"), Decimal("45"), Decimal("40"), Decimal("65")),
            ("maize", Decimal("5.8"), Decimal("7.0"), Decimal("50"), Decimal("90"), Decimal("25"), Decimal("45"), Decimal("35"), Decimal("65")),
            ("groundnut", Decimal("5.5"), Decimal("6.5"), Decimal("30"), Decimal("60"), Decimal("20"), Decimal("40"), Decimal("30"), Decimal("50")),
            ("chilli", Decimal("6.0"), Decimal("7.0"), Decimal("40"), Decimal("70"), Decimal("25"), Decimal("45"), Decimal("35"), Decimal("55")),
            ("potato", Decimal("5.0"), Decimal("6.0"), Decimal("60"), Decimal("100"), Decimal("30"), Decimal("50"), Decimal("40"), Decimal("70")),
            ("banana", Decimal("6.0"), Decimal("7.0"), Decimal("40"), Decimal("80"), Decimal("25"), Decimal("45"), Decimal("50"), Decimal("90")),
            ("mango", Decimal("5.5"), Decimal("7.5"), Decimal("30"), Decimal("60"), Decimal("20"), Decimal("40"), Decimal("40"), Decimal("70")),
            ("turmeric", Decimal("5.5"), Decimal("7.0"), Decimal("40"), Decimal("70"), Decimal("25"), Decimal("45"), Decimal("35"), Decimal("60"))
        ]
        
        for crop, ph_min, ph_max, n_min, n_max, p_min, p_max, k_min, k_max in nutrient_requirements:
            req = CropNutrientRequirement(
                crop_name=crop,
                ph_min=ph_min,
                ph_max=ph_max,
                nitrogen_min=n_min,
                nitrogen_max=n_max,
                phosphorus_min=p_min,
                phosphorus_max=p_max,
                potassium_min=k_min,
                potassium_max=k_max
            )
            db.add(req)
        
        db.commit()

        # Seed Indian government agricultural schemes
        print("Seeding government schemes...")

        schemes_data = [
            (
                "PM-KISAN",
                "Pradhan Mantri Kisan Samman Nidhi - Income support of ₹6,000 per year to farmers",
                "All landholding farmer families with cultivable land",
                Decimal("0"),
                Decimal("2"),
                None,
                None,
                "₹6,000 per year in three installments",
                "https://pmkisan.gov.in",
                None
            ),
            (
                "PMFBY",
                "Pradhan Mantri Fasal Bima Yojana - Crop insurance scheme",
                "Farmers growing notified crops in notified areas",
                Decimal("0.5"),
                None,
                "Rice, Wheat, Maize, Cotton, Sugarcane, etc.",
                None,
                "Premium subsidy up to 50% for Kharif crops, 40% for Rabi crops",
                "https://pmfby.gov.in",
                None
            ),
            (
                "Soil Health Card",
                "Soil Health Card Scheme - Testing soil health and providing nutrient recommendations",
                "All farmers with land holdings",
                Decimal("0"),
                None,
                None,
                None,
                "Free soil testing and nutrient management recommendations",
                "https://soilhealth.dac.gov.in",
                None
            ),
            (
                "KCC",
                "Kisan Credit Card - Credit facility for farmers",
                "Farmers including tenant farmers, sharecroppers, oral lessees",
                Decimal("0"),
                None,
                None,
                None,
                "Credit limit up to ₹3 lakh at interest rate of 7% (subsidized)",
                "https://kisancreditcard.in",
                None
            ),
            (
                "PM-Kisan Samridhi",
                "PM-Kisan Samridhi Kendra - One-stop centers for farmers",
                "Farmers with land holdings up to 2 hectares",
                Decimal("0"),
                Decimal("2"),
                None,
                None,
                "Access to credit, insurance, inputs, and market linkages",
                "https://pmksk.gov.in",
                None
            ),
            (
                "National Food Security Mission",
                "National Food Security Mission - Increasing production of rice, wheat, pulses, and coarse cereals",
                "Farmers in identified districts",
                Decimal("1"),
                None,
                "Rice, Wheat, Pulses, Coarse Cereals",
                None,
                "Subsidy on seeds, fertilizers, and machinery",
                "https://nfsm.gov.in",
                None
            ),
            (
                "Micro Irrigation Scheme",
                "Micro Irrigation Scheme - Subsidy for drip and sprinkler irrigation",
                "Farmers with land holdings",
                Decimal("0.5"),
                None,
                None,
                None,
                "Up to 55% subsidy on micro irrigation systems",
                "https://microrirrigation.gov.in",
                None
            ),
            (
                "RKVY",
                "Rashtriya Krishi Vikas Yojana - Agriculture development scheme",
                "Farmers and farmer groups",
                Decimal("0"),
                None,
                None,
                None,
                "Financial assistance for agriculture infrastructure and development",
                "https://rkvy.gov.in",
                None
            )
        ]

        for name, description, criteria, min_land, max_land, crops, states, benefits, link, deadline in schemes_data:
            scheme = Scheme(
                name=name,
                description=description,
                eligibility_criteria=criteria,
                min_land_hectares=min_land,
                max_land_hectares=max_land,
                eligible_crops=crops,
                eligible_states=states,
                benefits=benefits,
                application_link=link,
                deadline=deadline,
                is_active=1
            )
            db.add(scheme)

        db.commit()

        # Seed system configuration
        print("Seeding system configuration...")

        config_data = [
            ("outbreak_radius_km", "10", "Radius in km for outbreak detection"),
            ("outbreak_days_window", "7", "Time window in days for counting outbreak cases"),
            ("outbreak_threshold_count", "3", "Minimum case count to trigger outbreak alert"),
            ("outbreak_cooldown_hours", "24", "Cooldown period in hours before creating duplicate alert"),
            ("disease_confidence_threshold", "0.6", "Minimum confidence score for disease diagnosis")
        ]

        for key, value, description in config_data:
            config = SystemConfig(
                config_key=key,
                config_value=value,
                description=description
            )
            db.add(config)

        db.commit()

        # Seed market prices
        print("Seeding market prices...")

        market_prices_data = [
            ("Rice", "Maharashtra", Decimal("2500"), "APMC"),
            ("Wheat", "Maharashtra", Decimal("2200"), "APMC"),
            ("Cotton", "Maharashtra", Decimal("6500"), "APMC"),
            ("Tomato", "Maharashtra", Decimal("1500"), "APMC"),
            ("Sugarcane", "Maharashtra", Decimal("2800"), "APMC"),
            ("Soybean", "Maharashtra", Decimal("4000"), "APMC"),
            ("Onion", "Maharashtra", Decimal("1800"), "APMC"),
            ("Potato", "Maharashtra", Decimal("1200"), "APMC"),
            ("Maize", "Maharashtra", Decimal("1900"), "APMC"),
            ("Groundnut", "Maharashtra", Decimal("5500"), "APMC")
        ]

        for crop, region, price, source in market_prices_data:
            market_price = MarketPrice(
                crop_name=crop,
                market_region=region,
                price_per_quintal=price,
                source=source
            )
            db.add(market_price)

        db.commit()

        # Print credentials
        print("\n" + "="*60)
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nDemo Account Credentials:")
        print("-" * 60)
        
        print("\nADMIN:")
        print(f"  Email: {admin.email}")
        print(f"  Password: admin123")
        
        print("\nOFFICER:")
        print(f"  Email: {officer.email}")
        print(f"  Password: officer123")
        
        print("\nFARMERS:")
        print(f"  Farmer 1 - {farmer1.full_name}")
        print(f"    Email: {farmer1.email}")
        print(f"    Password: farmer123")
        print(f"    Farm: {farm1.name} ({farm1.location})")
        
        print(f"\n  Farmer 2 - {farmer2.full_name}")
        print(f"    Email: {farmer2.email}")
        print(f"    Password: farmer123")
        print(f"    Farm: {farm2.name} ({farm2.location})")
        
        print("\nBUYERS:")
        print(f"  Buyer 1 - {buyer1.full_name}")
        print(f"    Email: {buyer1.email}")
        print(f"    Password: buyer123")
        
        print(f"\n  Buyer 2 - {buyer2.full_name}")
        print(f"    Email: {buyer2.email}")
        print(f"    Password: buyer123")
        
        print("\n" + "-" * 60)
        print(f"Total Users Created: 6")
        print(f"Total Farms Created: 2")
        print(f"Total Crops Created: {len(indian_crops)}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
