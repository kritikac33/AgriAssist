#!/usr/bin/env python
"""Test finance summary bug fix."""
import requests
import time

BASE_URL = "http://localhost:8000"

# Start backend
import subprocess
import sys

print("Starting backend server...")
backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
time.sleep(3)

try:
    # Register farmer
    email = f"testfinance{int(time.time())}@example.com"
    data = {
        "email": email,
        "password": "TestPass123!",
        "full_name": "Test Finance",
        "phone": "9876543299",
        "role": "farmer"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"\n[REGISTER] Status: {response.status_code}")

    # Login
    login_data = {"email": email, "password": "TestPass123!"}
    login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    token = login_resp.json()["access_token"]
    print(f"[LOGIN] Token obtained")

    # Create farm
    farm_data = {
        "name": "Test Farm",
        "location": "Pune",
        "latitude": 18.52,
        "longitude": 73.85,
        "area_hectares": 5.0
    }
    headers = {"Authorization": f"Bearer {token}"}
    farm_resp = requests.post(f"{BASE_URL}/farms", json=farm_data, headers=headers)
    farm_id = farm_resp.json()["id"]
    print(f"[CREATE FARM] Farm ID: {farm_id}")

    # Create income entry
    income_data = {
        "farm_id": farm_id,
        "entry_type": "income",
        "category": "crop_sale",
        "amount": 50000.0,
        "date": "2024-01-15",
        "notes": "Tomato sale"
    }
    income_resp = requests.post(f"{BASE_URL}/finance-entries", json=income_data, headers=headers)
    print(f"\n[INCOME ENTRY] Status: {income_resp.status_code}")
    print(f"  Response: {income_resp.json()}")

    # Create expense entry 1
    expense1_data = {
        "farm_id": farm_id,
        "entry_type": "expense",
        "category": "fertilizer",
        "amount": 15000.0,
        "date": "2024-01-10",
        "notes": "Fertilizer purchase"
    }
    expense1_resp = requests.post(f"{BASE_URL}/finance-entries", json=expense1_data, headers=headers)
    print(f"\n[EXPENSE ENTRY 1] Status: {expense1_resp.status_code}")
    print(f"  Response: {expense1_resp.json()}")

    # Create expense entry 2
    expense2_data = {
        "farm_id": farm_id,
        "entry_type": "expense",
        "category": "seeds",
        "amount": 5000.0,
        "date": "2024-01-12",
        "notes": "Seed purchase"
    }
    expense2_resp = requests.post(f"{BASE_URL}/finance-entries", json=expense2_data, headers=headers)
    print(f"\n[EXPENSE ENTRY 2] Status: {expense2_resp.status_code}")
    print(f"  Response: {expense2_resp.json()}")

    # Get summary
    summary_resp = requests.get(f"{BASE_URL}/finance-entries/summary?farm_id={farm_id}", headers=headers)
    print(f"\n[SUMMARY] Status: {summary_resp.status_code}")
    print(f"  FULL RESPONSE JSON:")
    print(f"  {summary_resp.json()}")

    if summary_resp.status_code == 200:
        summary = summary_resp.json()
        print(f"\n  PARSED VALUES:")
        print(f"  total_income: {summary.get('total_income')}")
        print(f"  total_expenses: {summary.get('total_expenses')}")
        print(f"  net_profit: {summary.get('net_profit')}")
        print(f"  category_breakdown: {summary.get('category_breakdown')}")

        # Calculate expected
        expected_income = 50000.0
        expected_expenses = 15000.0 + 5000.0
        expected_net = expected_income - expected_expenses

        print(f"\n  EXPECTED vs ACTUAL:")
        print(f"  Income: expected {expected_income}, got {summary.get('total_income')}")
        print(f"  Expenses: expected {expected_expenses}, got {summary.get('total_expenses')}")
        print(f"  Net: expected {expected_net}, got {summary.get('net_profit')}")

finally:
    backend.terminate()
    backend.wait()
    print("\nBackend server stopped")
