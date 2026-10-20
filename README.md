# AgriAssist

## Abstract

AgriAssist is a web application that helps farmers manage farms and crops, access agricultural advisory features, and sell produce. Buyers can browse available produce, place orders, and communicate with farmers through the marketplace.

## Features

- Farmer registration, login, and role-based access
- Farm and crop management
- Crop disease diagnosis and treatment recommendations
- Soil health records and analysis
- Irrigation scheduling and water estimates
- Yield estimates and prediction history
- Alerts, finance tracking, and government scheme matching
- Marketplace listings, search, messaging, cart, saved listings, and order tracking
- Buyer checkout and Razorpay payment integration when configured

## Users

- **Farmer:** Manages farm and crop information, uses advisory features, creates produce listings, and manages orders.
- **Buyer:** Browses produce, saves listings, manages a cart, places and tracks orders, and communicates with farmers.

## Tech Stack

- **Frontend:** React, TypeScript, Vite, React Router, Axios
- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic
- **Database and migrations:** MySQL, Alembic
- **Testing:** Pytest
- **Payment integration:** Razorpay

## Demo Credentials

These seeded accounts are available after running the project’s database seed script.

### Farmers

| Email | Password |
|---|---|
| farmer1@agriassist.com | farmer123 |
| farmer2@agriassist.com | farmer123 |

### Buyers

| Email | Password |
|---|---|
| buyer1@agriassist.com | buyer123 |
| buyer2@agriassist.com | buyer123 |
