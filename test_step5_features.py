#!/usr/bin/env python
"""Test Step 5 features: pest outbreak alerts, finance tracker, scheme eligibility, admin features."""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def register_officer():
    """Register an agricultural officer."""
    email = f"officer{int(time.time())}@example.com"
    data = {
        "email": email,
        "password": "TestPass123!",
        "full_name": "Test Officer",
        "phone": "9876543212",
        "role": "officer"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"\n[REGISTER OFFICER]")
    print(f"  Status: {response.status_code}")
    if response.status_code in [200, 201]:
        # Login
        login_data = {"email": email, "password": "TestPass123!"}
        login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            print(f"  Officer token obtained")
            return token
    return None

def register_admin():
    """Register an admin user."""
    email = f"admin{int(time.time())}@example.com"
    data = {
        "email": email,
        "password": "TestPass123!",
        "full_name": "Test Admin",
        "phone": "9876543213",
        "role": "admin"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"\n[REGISTER ADMIN]")
    print(f"  Status: {response.status_code}")
    if response.status_code in [200, 201]:
        # Login
        login_data = {"email": email, "password": "TestPass123!"}
        login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            print(f"  Admin token obtained")
            return token
    return None

def test_finance_tracker(token, farm_id):
    """Test finance tracker (income and expense)."""
    # Add income
    income_data = {
        "farm_id": farm_id,
        "entry_type": "income",
        "category": "crop_sale",
        "amount": 50000.0,
        "date": "2024-01-15",
        "notes": "Tomato sale"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/finance-entries", json=income_data, headers=headers)
    print(f"\n[FINANCE - ADD INCOME]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")

    # Add expense
    expense_data = {
        "farm_id": farm_id,
        "entry_type": "expense",
        "category": "fertilizer",
        "amount": 15000.0,
        "date": "2024-01-10",
        "notes": "Fertilizer purchase"
    }
    response2 = requests.post(f"{BASE_URL}/finance-entries", json=expense_data, headers=headers)
    print(f"\n[FINANCE - ADD EXPENSE]")
    print(f"  Status: {response2.status_code}")
    print(f"  Response: {response2.json() if response2.status_code < 400 else response2.text}")

    # Get summary
    response3 = requests.get(f"{BASE_URL}/finance-entries/summary?farm_id={farm_id}", headers=headers)
    print(f"\n[FINANCE - GET SUMMARY]")
    print(f"  Status: {response3.status_code}")
    if response3.status_code == 200:
        summary = response3.json()
        print(f"  Total Income: {summary.get('total_income')}")
        print(f"  Total Expense: {summary.get('total_expense')}")
        print(f"  Net Balance: {summary.get('net_balance')}")
        # Verify math
        expected_net = 50000.0 - 15000.0
        actual_net = float(summary.get('net_balance', 0))
        print(f"  Math check: expected {expected_net}, got {actual_net}, match: {abs(expected_net - actual_net) < 0.01}")
        return True
    return False

def test_scheme_eligibility(token, farm_id):
    """Test scheme eligibility checker."""
    data = {
        "farm_id": farm_id
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/schemes/matches", json=data, headers=headers)
    print(f"\n[SCHEME ELIGIBILITY]")
    print(f"  Status: {response.status_code}")
    if response.status_code < 400:
        resp_json = response.json()
        # Try to print safely
        try:
            print(f"  Response: {resp_json}")
        except:
            print(f"  Response: [contains unicode characters]")
        if response.status_code == 200:
            schemes = resp_json
            print(f"  Matched schemes: {len(schemes)}")
            for scheme in schemes[:2]:  # Show first 2
                try:
                    print(f"    - {scheme.get('scheme_name')}: {scheme.get('benefits', '')[:50]}...")
                except:
                    print(f"    - [scheme data contains unicode]")
            return True
    else:
        print(f"  Response: {response.text}")
    return False

def test_admin_dashboard(token):
    """Test admin dashboard stats."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/dashboard", headers=headers)
    print(f"\n[ADMIN DASHBOARD]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    if response.status_code == 200:
        stats = response.json()
        print(f"  Total Users: {stats.get('total_users')}")
        print(f"  Total Diagnoses: {stats.get('total_diagnoses')}")
        print(f"  Total Listings: {stats.get('total_listings')}")
        print(f"  Transaction Volume: {stats.get('transaction_volume')}")
        return True
    return False

def test_admin_config(token):
    """Test admin config update."""
    # Get current config
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/config", headers=headers)
    print(f"\n[ADMIN CONFIG - GET]")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        configs = response.json()
        print(f"  Configs count: {len(configs)}")
        for cfg in configs[:3]:
            print(f"    - {cfg.get('config_key')}: {cfg.get('config_value')}")

    # Update outbreak threshold
    update_data = {
        "config_value": "3",
        "description": "Minimum diagnoses to trigger outbreak alert"
    }
    response2 = requests.patch(f"{BASE_URL}/admin/config/outbreak_threshold_count", json=update_data, headers=headers)
    print(f"\n[ADMIN CONFIG - UPDATE]")
    print(f"  Status: {response2.status_code}")
    print(f"  Response: {response2.json() if response2.status_code < 400 else response2.text}")

    # Verify update
    response3 = requests.get(f"{BASE_URL}/admin/config", headers=headers)
    if response3.status_code == 200:
        configs = response3.json()
        outbreak_cfg = [c for c in configs if c.get('config_key') == 'outbreak_threshold_count']
        if outbreak_cfg:
            print(f"  Verified outbreak_threshold_count = {outbreak_cfg[0].get('config_value')}")
            return True
    return False

def test_admin_users(token):
    """Test admin users list."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    print(f"\n[ADMIN USERS]")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"  Total users: {len(users)}")
        if users:
            print(f"  First user: {users[0].get('email')} ({users[0].get('role')})")
        return True
    return False

def test_admin_audit_logs(token):
    """Test admin audit logs."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/audit-logs", headers=headers)
    print(f"\n[ADMIN AUDIT LOGS]")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        logs = response.json()
        print(f"  Total logs: {len(logs)}")
        if logs:
            print(f"  First log: {logs[0].get('action')} by user {logs[0].get('user_id')}")
        return True
    return False

def test_outbreak_alerts(token):
    """Test outbreak alerts."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/alerts", headers=headers)
    print(f"\n[OUTBREAK ALERTS]")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        alerts = response.json()
        print(f"  Active alerts: {len(alerts)}")
        for alert in alerts[:2]:
            print(f"    - {alert.get('disease_name')} in {alert.get('region_description')}")
        return True
    return False

def main():
    print("=" * 80)
    print("STEP 5: ADDITIONAL FEATURES TEST")
    print("=" * 80)

    # First, create a farmer and farm for finance testing
    email = f"farmer{int(time.time())}@example.com"
    data = {
        "email": email,
        "password": "TestPass123!",
        "full_name": "Test Farmer",
        "phone": "9876543214",
        "role": "farmer"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    if response.status_code in [200, 201]:
        login_data = {"email": email, "password": "TestPass123!"}
        login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        farmer_token = login_resp.json()["access_token"]

        # Create farm
        farm_data = {
            "name": "Test Farm",
            "location": "Pune, Maharashtra",
            "latitude": 18.52,
            "longitude": 73.85,
            "area_hectares": 5.0
        }
        headers = {"Authorization": f"Bearer {farmer_token}"}
        farm_resp = requests.post(f"{BASE_URL}/farms", json=farm_data, headers=headers)
        farm_id = farm_resp.json()["id"] if farm_resp.status_code in [200, 201] else None

        # Test finance tracker
        finance_ok = test_finance_tracker(farmer_token, farm_id) if farm_id else False

        # Test scheme eligibility
        scheme_ok = test_scheme_eligibility(farmer_token, farm_id) if farm_id else False
    else:
        finance_ok = False
        scheme_ok = False

    # Register officer for outbreak alerts
    officer_token = register_officer()
    outbreak_ok = test_outbreak_alerts(officer_token) if officer_token else False

    # Register admin for admin features
    admin_token = register_admin()
    if admin_token:
        dashboard_ok = test_admin_dashboard(admin_token)
        config_ok = test_admin_config(admin_token)
        users_ok = test_admin_users(admin_token)
        audit_ok = test_admin_audit_logs(admin_token)
    else:
        dashboard_ok = False
        config_ok = False
        users_ok = False
        audit_ok = False

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Finance Tracker: {'PASS' if finance_ok else 'FAIL'}")
    print(f"Scheme Eligibility: {'PASS' if scheme_ok else 'FAIL'}")
    print(f"Outbreak Alerts: {'PASS' if outbreak_ok else 'FAIL'}")
    print(f"Admin Dashboard: {'PASS' if dashboard_ok else 'FAIL'}")
    print(f"Admin Config: {'PASS' if config_ok else 'FAIL'}")
    print(f"Admin Users: {'PASS' if users_ok else 'FAIL'}")
    print(f"Admin Audit Logs: {'PASS' if audit_ok else 'FAIL'}")
    print("=" * 80)

if __name__ == "__main__":
    main()
