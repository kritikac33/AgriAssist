# AgriAssist: AI-Powered Crop Advisory & Farm Support Platform

**Parts 1-4: Complete Full-Stack Implementation**

This is a complete implementation of the AgriAssist platform, including all 4 parts. The platform provides AI-powered crop advisory services, disease detection, marketplace functionality, and government scheme matching for Indian farmers.

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Modern, fast web framework for building APIs
- **MySQL 8** - Relational database
- **SQLAlchemy 2** - ORM for database operations
- **PyMySQL** - MySQL driver for Python
- **Alembic** - Database migration tool
- **Pydantic** - Data validation using Python type annotations
- **python-jose** - JWT token handling
- **passlib** - Password hashing with bcrypt
- **pytest** - Testing framework

### Frontend
- **React 19** - UI library
- **Vite 8** - Build tool and dev server
- **TypeScript 6** - Type-safe JavaScript
- **React Router 7** - Client-side routing
- **Axios 1** - HTTP client with interceptors
- **Razorpay Checkout.js** - Payment gateway integration

## Project Structure

```
semll/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management with pydantic-settings
│   ├── database.py          # SQLAlchemy engine and session
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas for request/response
│   ├── auth.py              # JWT authentication and RBAC
│   ├── seed.py              # Database seeding script
│   ├── utils.py             # Utility functions (haversine, config helpers)
│   ├── routers/             # API route modules
│   │   ├── __init__.py
│   │   ├── diagnoses.py     # Disease detection (Feature A)
│   │   ├── soil.py          # Soil health analyzer (Feature B)
│   │   ├── irrigation.py    # Water usage optimizer (Feature C)
│   │   ├── yield_predictions.py # Yield prediction (Feature D)
│   │   ├── alerts.py        # Pest outbreak alerts (Feature E)
│   │   ├── marketplace.py   # Marketplace (Feature F)
│   │   ├── transactions.py  # Payments with Razorpay (Feature G)
│   │   ├── schemes.py       # Government schemes (Supporting)
│   │   ├── finance.py       # Finance tracker (Supporting)
│   │   └── admin.py         # Admin dashboard & config (Features H & I)
│   └── integrations/        # External service integrations
│       ├── __init__.py
│       ├── ml_disease.py    # Disease detection ML model
│       ├── ml_yield.py      # Yield prediction ML model
│       ├── weather.py       # OpenWeatherMap integration
│       ├── notifications.py # SMTP email integration
│       └── payments.py      # Razorpay payment integration
├── frontend/                # React frontend (Part 4)
│   ├── src/
│   │   ├── api/             # API layer with axios
│   │   │   ├── axios.ts     # Axios instance with JWT interceptors
│   │   │   ├── auth.ts      # Authentication API
│   │   │   ├── disease.ts   # Disease scan API
│   │   │   ├── soil.ts      # Soil health API
│   │   │   ├── irrigation.ts # Irrigation API
│   │   │   ├── yield.ts     # Yield prediction API
│   │   │   ├── alerts.ts    # Alerts API
│   │   │   ├── marketplace.ts # Marketplace API
│   │   │   ├── transactions.ts # Transactions API
│   │   │   ├── finance.ts   # Finance tracker API
│   │   │   ├── schemes.ts   # Government schemes API
│   │   │   └── admin.ts     # Admin panel API
│   │   ├── pages/           # React page components
│   │   │   ├── Login.tsx    # Login/Register page
│   │   │   ├── Dashboard.tsx # Dashboard page
│   │   │   ├── DiseaseScan.tsx # Disease scan page
│   │   │   ├── SoilHealth.tsx # Soil health page
│   │   │   ├── Irrigation.tsx # Irrigation page
│   │   │   ├── YieldPrediction.tsx # Yield prediction page
│   │   │   ├── Alerts.tsx   # Alerts page
│   │   │   ├── Marketplace.tsx # Marketplace page
│   │   │   ├── Finance.tsx  # Finance tracker page
│   │   │   ├── Schemes.tsx  # Government schemes page
│   │   │   └── Admin.tsx    # Admin panel page
│   │   ├── App.tsx          # Main app component with routing
│   │   ├── main.tsx         # Entry point
│   │   ├── App.css          # App styles
│   │   └── index.css        # Global styles
│   ├── index.html           # HTML template with Razorpay script
│   ├── package.json         # Node dependencies
│   ├── vite.config.ts       # Vite configuration
│   └── tsconfig.json        # TypeScript configuration
├── alembic/                 # Database migrations
│   ├── versions/
│   │   └── 20240116_000001_add_ml_tables.py
│   ├── env.py
│   └── script.py.mako
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_ml_integrations.py
│   └── test_part3_features.py
├── ml/                      # ML models and training
│   ├── models/               # Trained model files
│   │   ├── disease_model.h5
│   │   ├── class_labels.json
│   │   ├── metadata.json
│   │   └── yield_model.pkl
│   ├── training/             # Training scripts and notebooks
│   │   ├── train_disease_model_colab.ipynb
│   │   └── train_yield_model.py
│   └── README.md
├── docs/                     # Documentation
│   ├── TRACEABILITY.md       # Requirements traceability matrix
│   ├── ASSUMPTIONS.md       # Design decisions and simplifications
│   └── ML_MODELS.md          # ML models documentation
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── docker-compose.yml      # Optional MySQL container
├── alembic.ini             # Alembic configuration
├── pytest.ini              # pytest configuration
└── README.md               # This file
```

## User Roles

The platform supports four user roles:

- **farmer** - Primary users who manage farms and crops
- **buyer** - Users who purchase crops from farmers
- **officer** - Agricultural officers who provide advisory services
- **admin** - System administrators with full access

## Database Models

The following database tables are created:

**Core Tables**:
- **users** - User accounts with role-based access
- **farms** - Farm locations with GPS coordinates
- **crops** - Crop information and planting details

**ML & Diagnostics**:
- **diagnoses** - Disease diagnosis records
- **treatments** - Disease treatment recommendations
- **prohibited_substances** - Banned agrochemicals in India
- **crop_nutrient_requirements** - Ideal soil nutrient ranges per crop
- **consent_records** - User consent tracking for training data

**Soil & Water**:
- **soil_records** - Soil test results
- **irrigation_schedules** - Irrigation planning

**Marketplace & Payments**:
- **listings** - Marketplace listings for crops
- **messages** - Marketplace messaging
- **transactions** - Purchase transactions
- **market_prices** - Crop market price benchmarks

**Alerts & Notifications**:
- **alerts** - User notifications
- **outbreak_alerts** - Pest outbreak alerts with geospatial data
- **notification_logs** - Notification delivery logs

**Schemes & Finance**:
- **schemes** - Government agricultural schemes
- **scheme_matches** - Government scheme recommendations
- **finance_entries** - Farm income/expense tracking

**Admin & Audit**:
- **audit_logs** - System audit trail
- **system_config** - Configurable system thresholds

**Yield Prediction**:
- **yield_predictions** - Yield prediction history

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- MySQL 8.0 or higher (or use Docker)
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd semll
```

### 2. MySQL Setup

#### Option A: Using Docker (Recommended)

Start MySQL using Docker Compose:

```bash
docker-compose up -d
```

This will start MySQL on port 3306 with:
- Database: `agriassist`
- Root password: `yourpass`
- Test database: `agriassist_test`

#### Option B: Local MySQL Installation

If you have MySQL installed locally, create the databases:

```sql
-- Connect to MySQL as root
mysql -u root -p

-- Create main database
CREATE DATABASE agriassist CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create test database
CREATE DATABASE agriassist_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a user (optional, you can use root)
CREATE USER 'agri_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON agriassist.* TO 'agri_user'@'localhost';
GRANT ALL PRIVILEGES ON agriassist_test.* TO 'agri_user'@'localhost';
FLUSH PRIVILEGES;
```

Update your `.env` file with your database credentials.

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and update the following values:

```env
DATABASE_URL=mysql+pymysql://root:yourpass@localhost:3306/agriassist
JWT_SECRET=change_me_to_a_secure_random_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Important:** Change `JWT_SECRET` to a secure random string in production.

### 5. Run Database Migrations

Apply the initial database schema:

```bash
alembic upgrade head
```

This will create all tables in the MySQL database.

### 6. Seed the Database

Populate the database with demo data:

```bash
python -m app.seed
```

This will create:
- 1 admin account
- 1 officer account
- 2 farmer accounts (with farms in Maharashtra)
- 2 buyer accounts
- 15 common Indian crops
- 8 government agricultural schemes
- 5 system configuration values
- 10 market price benchmarks
- Disease treatment recommendations
- Prohibited substances list
- Crop nutrient requirements

The script will print all login credentials to the console.

### 7. Start the Application

Run the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 8. Frontend Setup (Part 4)

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
```

Start the frontend development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or another port if 5173 is in use).

### API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Running Tests

### 1. Ensure Test Database Exists

The tests use a separate database `agriassist_test`. Create it if you haven't already:

```sql
CREATE DATABASE agriassist_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Run Tests

```bash
pytest
```

The test suite includes:
- User registration
- Login and authentication
- Token refresh
- Role-based access control
- Cross-role access blocking

### 3. Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

## Available API Endpoints

### Authentication

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and receive JWT tokens
- `GET /auth/me` - Get current user information
- `POST /auth/refresh` - Refresh access token

### Disease Detection (Feature A)

- `POST /diagnoses` - Create disease diagnosis with image upload
- `GET /diagnoses` - List all diagnoses for user's crops
- `GET /diagnoses/{id}` - Get specific diagnosis with treatments

### Soil Health (Feature B)

- `POST /soil-records` - Create manual soil record
- `POST /soil-records/from-sensor` - Create sensor soil record
- `GET /soil-records` - List all soil records for user's farms
- `GET /soil-records/{id}/analyze` - Analyze soil against crop requirements

### Irrigation (Feature C)

- `POST /irrigation-schedules` - Create schedule with auto water calculation
- `GET /irrigation-schedules` - List schedules with filtering
- `POST /irrigation-schedules/{id}/recalculate` - Recalculate with weather forecast
- `POST /irrigation-schedules/{id}/postpone` - Postpone by N days

### Yield Prediction (Feature D)

- `POST /yield-predictions` - Create yield prediction
- `GET /yield-predictions` - List predictions for user's farms
- `GET /yield-predictions/{id}` - Get specific prediction
- `GET /yield-predictions/crop/{crop_id}/history` - Get version history

### Pest Outbreak Alerts (Feature E)

- `POST /alerts` - Create manual outbreak alert (officer/admin only)
- `PATCH /alerts/{id}/retract` - Retract alert (officer/admin only)
- `GET /alerts?lat=&lon=` - Get alerts within range (farmer-facing)

### Marketplace (Feature F)

- `POST /listings` - Create listing (farmer only)
- `GET /listings` - List with filters (crop, price, distance, sort)
- `GET /listings/{id}` - Get specific listing
- `PATCH /listings/{id}` - Update/close listing (seller only)
- `POST /listings/{id}/messages` - Send message
- `GET /listings/{id}/messages` - Get conversation

### Payments (Feature G)

- `POST /transactions` - Create transaction and Razorpay order (buyer only)
- `GET /transactions/{id}/verify` - Verify payment status via polling
- `PATCH /transactions/{id}/status` - Manual status update (farmer/admin)
- `GET /transactions` - List user's transactions
- `GET /transactions/{id}` - Get specific transaction

### Government Schemes

- `POST /scheme-matches` - Get eligible schemes for a farm
- `GET /schemes` - List all active schemes

### Finance Tracker

- `POST /finance-entries` - Create finance entry
- `GET /finance-entries` - List entries with filters
- `GET /finance-entries/summary` - Get farm financial summary
- `GET /finance-entries/{id}` - Get specific entry

### Admin Dashboard (Feature H)

- `GET /admin/dashboard` - Get platform summary (admin only)

### Config Management (Feature I)

- `GET /admin/config` - List all config values (admin only)
- `PATCH /admin/config/{key}` - Update config value (admin only)
- `GET /admin/users` - List/search users (admin only)
- `GET /admin/audit-logs` - Get recent audit logs (admin only)

### General

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

## Required Accounts and API Keys

### For Full Functionality (Optional - mock data works without these)

1. **OpenWeatherMap API** (for real weather data in irrigation scheduling)
   - Sign up at: https://openweathermap.org/api
   - Get free API key
   - Add to `.env`: `OPENWEATHER_API_KEY=your_key_here`

2. **Razorpay Payment Gateway** (for real payment processing)
   - Sign up at: https://razorpay.com/docs/api/
   - Get test mode credentials
   - Add to `.env`:
     ```
     RAZORPAY_KEY_ID=your_key_id
     RAZORPAY_KEY_SECRET=your_key_secret
     ```
   - **Note**: Frontend uses Razorpay test mode with demo card numbers. No real money is charged.

3. **SMTP Email Service** (for email notifications on alerts)
   - Gmail: Enable 2FA and generate App Password
   - Add to `.env`:
     ```
     SMTP_HOST=smtp.gmail.com
     SMTP_PORT=587
     SMTP_USERNAME=your_email@gmail.com
     SMTP_PASSWORD=your_app_password
     SMTP_FROM_EMAIL=your_email@gmail.com
     ```

**The application works fully with mock data if these keys are not configured.**

## Adding Real API Keys

The application is designed to work with mock data when API keys are missing. To enable real integrations, add your API keys to the `.env` file:

### OpenWeatherMap API

```env
OPENWEATHER_API_KEY=your_openweathermap_api_key_here
```

Get your key at: https://openweathermap.org/api

### Razorpay Payment Gateway

```env
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

Get your credentials at: https://razorpay.com/docs/api/

**Note**: This uses Razorpay **TEST MODE** only (no real money). The system will fall back to a mock payment flow if these keys are not configured.

### SMTP Email Configuration

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
```

**For Gmail**:
1. Enable 2-Factor Authentication on your Google Account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the App Password as `SMTP_PASSWORD`
4. Set `SMTP_HOST=smtp.gmail.com` and `SMTP_PORT=587`

**Other SMTP Providers**:
- Outlook: `smtp-mail.outlook.com:587`
- Yahoo: `smtp.mail.yahoo.com:587`
- SendGrid: `smtp.sendgrid.net:587`

**Note**: The system will fall back to log-only mode if SMTP credentials are not configured. All notification attempts are logged to the `notification_logs` table regardless of email success.

Get your credentials at: https://razorpay.com/docs/api/

### Kaggle (for dataset downloads)

```env
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
```

Get your API key at: https://www.kaggle.com/settings

### ML Model Paths

```env
ML_DISEASE_MODEL_PATH=./ml/models/disease_model.h5
ML_YIELD_MODEL_PATH=./ml/models/yield_model.pkl
```

These will be used in Part 2 when ML models are implemented.

**Note:** The application will automatically use real services when keys are added, and fall back to mock implementations when keys are missing. No code changes are required.

## Demo Credentials

After running the seed script, you can use these credentials to test the application:

### Admin
- Email: `admin@agriassist.com`
- Password: `admin123`

### Officer
- Email: `officer@agriassist.com`
- Password: `officer123`

### Farmer 1
- Email: `farmer1@agriassist.com`
- Password: `farmer123`
- Farm: Green Valley Farm (Pimpri-Chinchwad, Maharashtra)

### Farmer 2
- Email: `farmer2@agriassist.com`
- Password: `farmer123`
- Farm: Sahyadri Farms (Nashik, Maharashtra)

### Buyer 1
- Email: `buyer1@agriassist.com`
- Password: `buyer123`

### Buyer 2
- Email: `buyer2@agriassist.com`
- Password: `buyer123`

## Development Workflow

### Creating New Migrations

After modifying models in `app/models.py`, create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply the migration:

```bash
alembic upgrade head
```

### Rolling Back Migrations

Roll back to the previous version:

```bash
alembic downgrade -1
```

### Adding New API Endpoints

1. Create Pydantic schemas in `app/schemas.py`
2. Add routes to the appropriate router in `app/routers/`
3. Register the router in `app/main.py`
4. Add tests in `tests/`

## Security Notes

- **JWT Secret**: Always use a strong, random JWT secret in production
- **Database Password**: Change the default MySQL password
- **HTTPS**: Use HTTPS in production for all API endpoints
- **Input Validation**: All inputs are validated using Pydantic schemas
- **Password Hashing**: Passwords are hashed using bcrypt before storage
- **SQL Injection**: SQLAlchemy ORM protects against SQL injection

## Troubleshooting

### Database Connection Issues

If you get database connection errors:

1. Verify MySQL is running: `docker-compose ps` (if using Docker)
2. Check the DATABASE_URL in `.env` matches your MySQL configuration
3. Ensure the database exists: `mysql -u root -p -e "SHOW DATABASES;"`

### Migration Errors

If migrations fail:

1. Check the database exists
2. Verify MySQL user has proper privileges
3. Check Alembic configuration in `alembic.ini`

### Import Errors

If you get import errors:

1. Ensure you're in the project root directory
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Check Python version is 3.11 or higher

## Current Implementation Status

### Completed Features (Parts 1-4)

**Part 1: Backend Foundation** ✅
- User authentication with JWT and RBAC
- Database models for core entities
- API foundation with FastAPI
- Database seeding with demo data

**Part 2: ML and Analytics Features** ✅
- Disease detection with ML model (stub fallback)
- Soil health analyzer with crop requirements
- Water usage optimizer with weather integration
- Yield prediction with ML model
- Treatment recommendations with prohibited substances filter

**Part 3: Marketplace, Alerts, Payments, and Admin** ✅
- Pest outbreak alerts with auto-detection and email notifications
- Marketplace with listings, messaging, and price benchmarks
- Razorpay payment integration (test mode with polling verification)
- Government scheme eligibility checker
- Finance tracker for farms
- Admin analytics dashboard
- Configurable system thresholds

**Part 4: Frontend Web Application** ✅
- React + Vite + TypeScript frontend
- React Router for navigation
- All 11 pages fully implemented:
  - Login/Register with role selector (farmer, buyer)
  - Dashboard with role-aware navigation and admin stats
  - Disease Scan with image upload and ML prediction
  - Soil Health analysis with recommendations
  - Irrigation scheduling with weather integration
  - Yield Prediction with history tracking
  - Alerts with officer create/retract functionality
  - Marketplace with Razorpay Checkout.js integration
  - Finance Tracker with income/expense summary
  - Government Schemes eligibility checker
  - Admin Panel with dashboard, config, users, and audit logs
- JWT authentication with localStorage and auto-refresh
- Axios interceptors for automatic token attachment
- Razorpay Checkout.js script loading for test-mode payments

### Testing Status

- ✅ Unit tests for authentication (8 tests)
- ✅ Unit tests for ML integrations (8 tests)
- ✅ Unit tests for Part 3 features (15 tests)
- **Total: 31 tests passing**

### Documentation

- ✅ TRACEABILITY.md - Requirements traceability matrix
- ✅ ASSUMPTIONS.md - Design decisions and simplifications
- ✅ ML_MODELS.md - ML models documentation
- ✅ README.md - Setup and usage guide

## Running Both Backend and Frontend Together

To run the full application:

1. **Terminal 1 - Backend:**
   ```bash
   cd semll
   uvicorn app.main:app --reload
   ```
   Backend runs on `http://localhost:8000`

2. **Terminal 2 - Frontend:**
   ```bash
   cd semll/frontend
   npm run dev
   ```
   Frontend runs on `http://localhost:5173` (or another port if 5173 is in use)

3. **Access the Application:**
   - Open your browser to `http://localhost:5173`
   - Login with the demo credentials below

## Demo Video Recording Script

Follow this script to record a comprehensive demo video:

### Scene 1: Introduction (30 seconds)
- Show the project structure and explain the 4-part architecture
- Mention the tech stack: FastAPI, MySQL, React, Vite, TypeScript

### Scene 2: Backend Setup (45 seconds)
- Show the backend running: `uvicorn app.main:app --reload`
- Show the API documentation at `http://localhost:8000/docs`
- Briefly show a few endpoints

### Scene 3: Frontend Setup (30 seconds)
- Show the frontend running: `npm run dev`
- Show the login page at `http://localhost:5173`

### Scene 4: Farmer Login (30 seconds)
- Login as farmer: `farmer1@agriassist.com` / `farmer123`
- Show the dashboard with farmer-specific links

### Scene 5: Disease Scan (1 minute)
- Navigate to Disease Scan
- Upload a leaf image (use any plant image)
- Show the prediction result with confidence score
- Show treatment recommendations

### Scene 6: Soil Health (45 seconds)
- Navigate to Soil Health
- Enter soil test values (pH, nitrogen, phosphorus, potassium)
- Show the analysis results and recommendations

### Scene 7: Irrigation (45 seconds)
- Navigate to Irrigation
- Generate an irrigation schedule
- Show the schedule table with weather-adjusted status
- Demonstrate recalculate and postpone buttons

### Scene 8: Yield Prediction (30 seconds)
- Navigate to Yield Prediction
- Generate a prediction
- Show the yield range and confidence
- Show the prediction history

### Scene 9: Marketplace - Seller (1 minute)
- Navigate to Marketplace
- Create a new listing (crop name, quantity, price, location)
- Show the listing appears with market price benchmark
- Show the "below/near/above" market price label

### Scene 10: Buyer Login (30 seconds)
- Logout and login as buyer: `buyer1@agriassist.com` / `buyer123`
- Show the buyer dashboard

### Scene 11: Marketplace - Buyer & Payment (1.5 minutes)
- Navigate to Marketplace
- Browse listings and filter by crop/price
- Click "View Details" on a listing
- Send a message in the message thread
- Click "Buy Now" to initiate payment
- Show the Razorpay Checkout.js modal
- Use test card: 4111 1111 1111 1111
- Show payment success and transaction verification
- Show the transaction in transaction history

### Scene 12: Alerts (1 minute)
- Navigate to Alerts
- Show the list of active alerts
- Logout and login as officer: `officer@agriassist.com` / `officer123`
- Create a new outbreak alert
- Show the alert appears in the list
- Retract the alert

### Scene 13: Finance Tracker (30 seconds)
- Login as farmer again
- Navigate to Finance Tracker
- Add an income entry
- Add an expense entry
- Show the financial summary (income, expenses, net)

### Scene 14: Government Schemes (45 seconds)
- Navigate to Schemes
- Check eligibility for a farm
- Show matched schemes with eligibility reasoning
- Browse all available schemes

### Scene 15: Admin Panel (1 minute)
- Login as admin: `admin@agriassist.com` / `admin123`
- Navigate to Admin Panel
- Show Dashboard stats (user counts, transactions, revenue)
- Show Config tab and edit a threshold value
- Show Users tab and search for users
- Show Audit Logs tab with recent activity

### Scene 16: Conclusion (30 seconds)
- Summarize all features demonstrated
- Mention the clean, functional UI
- End with the project repository link

**Total estimated time: ~12 minutes**

## Next Steps

Potential enhancements for future development:
- Advanced features as needed
- Performance optimization
- Additional testing and validation
- Mobile-responsive design improvements
- Real-time notifications via WebSockets

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the repository.

## Advisory and Payment API updates

Run `alembic upgrade head` before starting the backend to apply migrations `005` through `007`. Migration `005` adds soil moisture, structured irrigation inputs, immutable yield input snapshots/model versions, per-buyer message thread IDs, and a unique crop prediction version constraint. Migration `006` adds persistent buyer carts and saved listings, plus immutable transaction crop, seller, and unit-price snapshots. Migration `007` adds saved delivery addresses, order fulfilment history, cancellation requests, message read timestamps, in-app notification metadata, and buyer support tickets. Existing transaction rows are backfilled from the available listing/account data; historical source details that were never recorded cannot be recovered.

Buyer portal routes include `/dashboard`, `/marketplace`, `/cart`, `/orders`, `/messages`, `/saved-listings`, `/addresses`, and `/notifications`. Cart items are grouped by farmer and paid as separate listing transactions using the existing Razorpay flow. Checkout supports pickup or delivery to a saved address; listing quantities are reserved while payment is pending. Failed checkout can release reserved stock, while dismissing Razorpay leaves the order pending until its status is checked or the buyer explicitly cancels it. Buyers can request cancellation after payment, but refunds are not automatic or implemented. Farmers can track their orders at `/farmer-orders` and move paid orders through the permitted fulfilment steps. Support reports are recorded for follow-up; no support-agent response workflow is included.

Online payments require `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in the backend environment, plus `VITE_RAZORPAY_KEY_ID` in `frontend/.env.local`. Without a configured Razorpay SDK and credentials, the backend returns a service-unavailable response and never marks a demo transaction paid.
