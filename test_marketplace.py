import requests
import json

BASE_URL = "http://localhost:8000"

# Login as Farmer A
farmer_a_login = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "ramesh.farmer@test.com",
    "password": "Test@1234"
})

if farmer_a_login.status_code == 200:
    farmer_a_token = farmer_a_login.json()["access_token"]
    farmer_a_headers = {"Authorization": f"Bearer {farmer_a_token}"}
    print("[OK] Farmer A login successful")

    # Create marketplace listing: crop=Tomato, quantity=50, unit=kg, price=25/kg
    listing_data = {
        "crop_name": "Tomato",
        "variety": "Roma",
        "quantity_quintals": 0.5,  # 50 kg = 0.5 quintals
        "price_per_quintal": 2500,  # 25/kg = 2500/quintal
        "location": "Pune, Maharashtra",
        "available_from": "2026-10-05",
        "expected_harvest_date": "2026-12-01"
    }

    listing_response = requests.post(f"{BASE_URL}/listings/", json=listing_data, headers=farmer_a_headers)

    if listing_response.status_code in [200, 201]:
        listing = listing_response.json()
        print(f"\n[OK] Marketplace listing created: ID {listing['id']}")
        print(f"[LISTING] {listing.get('crop_name')} - {listing.get('quantity_quintals')} quintals @ {listing.get('price_per_quintal')}/quintal")

        # Get all listings
        listings_response = requests.get(f"{BASE_URL}/listings/", headers=farmer_a_headers)
        if listings_response.status_code == 200:
            listings = listings_response.json()
            print(f"\n[LISTINGS] Total: {len(listings)}")
    else:
        print(f"[ERROR] Listing creation failed: {listing_response.status_code}")
        print(listing_response.text)

# Login as Buyer
buyer_login = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "anita.buyer@test.com",
    "password": "Test@1234"
})

if buyer_login.status_code == 200:
    buyer_token = buyer_login.json()["access_token"]
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
    print("\n[OK] Buyer login successful")

    # Browse listings
    listings_response = requests.get(f"{BASE_URL}/listings/", headers=buyer_headers)
    if listings_response.status_code == 200:
        listings = listings_response.json()
        print(f"\n[LISTINGS] Buyer can see {len(listings)} listings")

        if listings:
            listing_id = listings[0]["id"]
            print(f"[TEST] Creating transaction for listing {listing_id}")

            # Create transaction
            transaction_data = {
                "listing_id": listing_id,
                "buyer_id": 66,  # Buyer's user ID
                "quantity_quintals": 0.5,
                "total_amount": 1250.0
            }

            transaction_response = requests.post(f"{BASE_URL}/transactions/", json=transaction_data, headers=buyer_headers)

            if transaction_response.status_code in [200, 201]:
                transaction = transaction_response.json()
                print(f"\n[OK] Transaction created: ID {transaction['id']}")
                print(f"[TRANSACTION] Status: {transaction.get('status')}")
            else:
                print(f"[ERROR] Transaction creation failed: {transaction_response.status_code}")
                print(transaction_response.text)
