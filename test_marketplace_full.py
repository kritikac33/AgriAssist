#!/usr/bin/env python
"""Test marketplace functionality with seller and buyer accounts."""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# Store tokens and IDs
seller_token = None
buyer_token = None
listing_id = None
transaction_id = None

def register_seller():
    """Register a seller (farmer)."""
    global seller_token
    email = f"seller{int(time.time())}@example.com"
    data = {
        "email": email,
        "password": "TestPass123!",
        "full_name": "Test Seller",
        "phone": "9876543210",
        "role": "farmer"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"\n[REGISTER SELLER]")
    print(f"  Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"  Email: {email}")
        # Login
        login_data = {"email": email, "password": "TestPass123!"}
        login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if login_resp.status_code == 200:
            seller_token = login_resp.json()["access_token"]
            print(f"  Seller token obtained")
            return seller_token
    return None

def register_buyer():
    """Register a buyer."""
    global buyer_token
    email = f"buyer{int(time.time())}@example.com"
    data = {
        "email": email,
        "password": "TestPass123!",
        "full_name": "Test Buyer",
        "phone": "9876543211",
        "role": "buyer"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"\n[REGISTER BUYER]")
    print(f"  Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"  Email: {email}")
        # Login
        login_data = {"email": email, "password": "TestPass123!"}
        login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if login_resp.status_code == 200:
            buyer_token = login_resp.json()["access_token"]
            print(f"  Buyer token obtained")
            return buyer_token
    return None

def create_listing(token):
    """Create a marketplace listing."""
    global listing_id
    params = {
        "crop_name": "Tomato",
        "quantity_quintals": 10.0,
        "price_per_quintal": 1500.0,
        "unit": "quintal",
        "location": "Pune, Maharashtra",
        "latitude": 18.52,
        "longitude": 73.85,
        "description": "Fresh organic tomatoes"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/listings", params=params, headers=headers)
    print(f"\n[CREATE LISTING]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    if response.status_code in [200, 201]:
        listing_id = response.json()["id"]
        print(f"  Listing ID: {listing_id}")
        return listing_id
    return None

def get_listings(token):
    """Get all listings."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/listings", headers=headers)
    print(f"\n[GET ALL LISTINGS]")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        listings = response.json()
        print(f"  Total listings: {len(listings)}")
        if listings:
            listing = listings[0]
            print(f"  First listing:")
            print(f"    ID: {listing.get('id')}")
            print(f"    Crop: {listing.get('crop_name')}")
            print(f"    Price: {listing.get('price_per_quintal')}")
            print(f"    Market price benchmark: {listing.get('market_price_benchmark')}")
            print(f"    Price label: {listing.get('price_label')}")
        return listings
    return None

def get_listings_filtered(token):
    """Get listings with filters."""
    params = {
        "crop": "Tomato",
        "min_price": 1000,
        "max_price": 2000
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/listings", params=params, headers=headers)
    print(f"\n[GET LISTINGS FILTERED]")
    print(f"  Status: {response.status_code}")
    print(f"  Params: {params}")
    if response.status_code == 200:
        listings = response.json()
        print(f"  Filtered listings: {len(listings)}")
        for listing in listings:
            print(f"    - {listing.get('crop_name')}: {listing.get('price_per_quintal')}")
        return listings
    return None

def post_message(token, listing_id):
    """Post a message to a listing."""
    data = {
        "content": "Is this still available? I'm interested in buying."
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/listings/{listing_id}/messages", json=data, headers=headers)
    print(f"\n[POST MESSAGE]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    return response.status_code in [200, 201]

def get_messages(token, listing_id):
    """Get messages for a listing."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/listings/{listing_id}/messages", headers=headers)
    print(f"\n[GET MESSAGES]")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        messages = response.json()
        print(f"  Messages: {len(messages)}")
        for msg in messages:
            print(f"    - {msg.get('content')[:50]}...")
        return messages
    return None

def create_transaction(token, listing_id):
    """Create a transaction (buyer initiates purchase)."""
    global transaction_id
    data = {
        "listing_id": listing_id,
        "quantity_quintals": 5.0,
        "total_amount": 7500.0
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/transactions", json=data, headers=headers)
    print(f"\n[CREATE TRANSACTION]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    if response.status_code in [200, 201]:
        transaction_id = response.json()["id"]
        print(f"  Transaction ID: {transaction_id}")
        print(f"  Razorpay Order ID: {response.json().get('razorpay_order_id')}")
        print(f"  Status: {response.json().get('status')}")
        return transaction_id
    return None

def verify_transaction(token, transaction_id):
    """Verify transaction status."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/transactions/{transaction_id}/verify", headers=headers)
    print(f"\n[VERIFY TRANSACTION]")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code < 400 else response.text}")
    if response.status_code == 200:
        print(f"  Transaction status: {response.json().get('status')}")
        return response.json()
    return None

def main():
    print("=" * 80)
    print("STEP 4: MARKETPLACE FULL TEST")
    print("=" * 80)

    # Register seller
    seller_token = register_seller()
    if not seller_token:
        print("\n[FAILED] Could not register seller")
        return

    # Register buyer
    buyer_token = register_buyer()
    if not buyer_token:
        print("\n[FAILED] Could not register buyer")
        return

    # Create listing
    listing_id = create_listing(seller_token)
    if not listing_id:
        print("\n[FAILED] Could not create listing")
        return

    # Get all listings
    listings = get_listings(buyer_token)

    # Get filtered listings
    filtered = get_listings_filtered(buyer_token)

    # Buyer posts message
    msg_ok = post_message(buyer_token, listing_id)

    # Get messages
    messages = get_messages(seller_token, listing_id)

    # Create transaction
    transaction_id = create_transaction(buyer_token, listing_id)
    if not transaction_id:
        print("\n[FAILED] Could not create transaction")
        return

    # Verify transaction
    verify_result = verify_transaction(buyer_token, transaction_id)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Seller Registration: PASS")
    print(f"Buyer Registration: PASS")
    print(f"Create Listing: {'PASS' if listing_id else 'FAIL'}")
    print(f"Get All Listings: {'PASS' if listings else 'FAIL'}")
    print(f"Get Filtered Listings: {'PASS' if filtered else 'FAIL'}")
    print(f"Post Message: {'PASS' if msg_ok else 'FAIL'}")
    print(f"Get Messages: {'PASS' if messages else 'FAIL'}")
    print(f"Create Transaction: {'PASS' if transaction_id else 'FAIL'}")
    print(f"Verify Transaction: {'PASS' if verify_result else 'FAIL'}")
    print("=" * 80)

if __name__ == "__main__":
    main()
