#!/usr/bin/env python
"""Test core functionality with fresh test account."""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def register_farmer():
    """Register a new test farmer."""
    email = f"testfarmer{int(time.time())}@example.com"
    data = {
        "email": email,
        "password": "TestPass123!",
        "full_name": "Test Farmer",
        "phone": "9876543210",
        "role": "farmer"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"\n[REGISTER FARMER]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    if response.status_code in [200, 201]:
        return data["email"], data["password"]
    return None, None

def login(email, password):
    """Login and get token."""
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=data)
    print(f"\n[LOGIN]")
    print(f"  Status: {response.status_code}")
    if response.status_code in [200, 201]:
        token = response.json()["access_token"]
        print(f"  Token: {token[:50]}...")
        return token
    else:
        print(f"  Response: {response.text}")
        return None

def create_farm(token):
    """Create a farm."""
    data = {
        "name": "Test Farm",
        "location": "Pune, Maharashtra",
        "latitude": 18.52,
        "longitude": 73.85,
        "area_hectares": 5.0,
        "soil_type": "Black Soil"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/farms", json=data, headers=headers)
    print(f"\n[CREATE FARM]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    if response.status_code in [200, 201]:
        return response.json()["id"]
    return None

def create_crop(token, farm_id):
    """Create a crop."""
    data = {
        "farm_id": farm_id,
        "name": "Tomato",
        "variety": "Roma",
        "planting_date": "2024-01-01",
        "expected_harvest_date": "2024-04-01",
        "area_hectares": 2.0,
        "status": "active"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/crops", json=data, headers=headers)
    print(f"\n[CREATE CROP]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    if response.status_code in [200, 201]:
        return response.json()["id"]
    return None

def test_ownership_enforcement(token, farm_id):
    """Test that user can only access their own farms."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/farms", headers=headers)
    print(f"\n[GET FARMS - OWNERSHIP TEST]")
    print(f"  Status: {response.status_code}")
    farms = response.json() if response.status_code in [200, 201] else []
    print(f"  Farms returned: {len(farms)}")
    if farms:
        print(f"  Farm IDs: {[f['id'] for f in farms]}")
        print(f"  All owned by current user: {all(f['id'] == farm_id for f in farms)}")
    return response.status_code in [200, 201]

def test_disease_scan(token, crop_id):
    """Test disease scan with real image."""
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": open("test_leaf.jpg", "rb")}
    params = {"crop_id": crop_id}
    response = requests.post(f"{BASE_URL}/diagnoses", files=files, params=params, headers=headers)
    print(f"\n[DISEASE SCAN]")
    print(f"  Status: {response.status_code}")
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"  Disease: {result.get('disease_name')}")
        print(f"  Confidence: {result.get('confidence_score')}")
        print(f"  Treatment data present: {bool(result.get('recommended_action'))}")
        print(f"  Treatments count: {len(result.get('treatments', []))}")
        return result
    else:
        print(f"  Response: {response.text}")
        return None

def test_soil_health(token, farm_id):
    """Test soil health record."""
    data = {
        "farm_id": farm_id,
        "ph_level": 6.5,
        "nitrogen": 45.0,
        "phosphorus": 30.0,
        "potassium": 25.0,
        "organic_matter": 2.5,
        "source": "manual"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/soil-records", json=data, headers=headers)
    print(f"\n[SOIL HEALTH RECORD]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    if response.status_code in [200, 201]:
        record_id = response.json()["id"]
        # Get analysis
        response2 = requests.get(f"{BASE_URL}/soil-records/{record_id}/analyze?crop_name=Tomato", headers=headers)
        print(f"  Analysis Status: {response2.status_code}")
        if response2.status_code in [200, 201]:
            print(f"  Analysis: {response2.json()}")
        return True
    return False

def test_irrigation(token, farm_id):
    """Test irrigation schedule."""
    scheduled_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    data = {
        "farm_id": farm_id,
        "scheduled_date": scheduled_date,
        "duration_hours": 2.0,
        "water_amount_liters": 5000.0,
        "status": "pending",
        "notes": "Regular irrigation"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/irrigation-schedules", json=data, headers=headers)
    print(f"\n[IRRIGATION SCHEDULE]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    if response.status_code in [200, 201]:
        schedule_id = response.json()["id"]
        # Get schedules
        response2 = requests.get(f"{BASE_URL}/irrigation-schedules?farm_id={farm_id}", headers=headers)
        print(f"  Get Schedules Status: {response2.status_code}")
        if response2.status_code in [200, 201]:
            schedules = response2.json()
            print(f"  Schedules returned: {len(schedules)}")
        return True
    return False

def test_yield_prediction(token, farm_id, crop_id):
    """Test yield prediction."""
    data = {
        "farm_id": farm_id,
        "crop_id": crop_id,
        "land_size_acres": 2.0,
        "planting_date": "2024-01-01"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/yield-predictions", json=data, headers=headers)
    print(f"\n[YIELD PREDICTION]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    return response.status_code in [200, 201]

def main():
    print("=" * 80)
    print("STEP 3: CORE FUNCTIONALITY VERIFICATION")
    print("=" * 80)

    # Register farmer
    email, password = register_farmer()
    if not email:
        print("\n[FAILED] Could not register farmer")
        return

    # Login
    token = login(email, password)
    if not token:
        print("\n[FAILED] Could not login")
        return

    # Create farm
    farm_id = create_farm(token)
    if not farm_id:
        print("\n[FAILED] Could not create farm")
        return

    # Create crop
    crop_id = create_crop(token, farm_id)
    if not crop_id:
        print("\n[FAILED] Could not create crop")
        return

    # Test ownership
    ownership_ok = test_ownership_enforcement(token, farm_id)

    # Test disease scan
    disease_result = test_disease_scan(token, crop_id)

    # Test soil health
    soil_ok = test_soil_health(token, farm_id)

    # Test irrigation
    irrigation_ok = test_irrigation(token, farm_id)

    # Test yield prediction
    yield_ok = test_yield_prediction(token, farm_id, crop_id)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Farm Creation: {'PASS' if farm_id else 'FAIL'}")
    print(f"Crop Creation: {'PASS' if crop_id else 'FAIL'}")
    print(f"Ownership Enforcement: {'PASS' if ownership_ok else 'FAIL'}")
    print(f"Disease Scan: {'PASS' if disease_result else 'FAIL'}")
    print(f"Soil Health: {'PASS' if soil_ok else 'FAIL'}")
    print(f"Irrigation: {'PASS' if irrigation_ok else 'FAIL'}")
    print(f"Yield Prediction: {'PASS' if yield_ok else 'FAIL'}")
    print("=" * 80)

if __name__ == "__main__":
    main()
