# AgriAssist Requirements Traceability Matrix

This document traces the implementation of requirements from the specification to the actual code.

## Part 2: ML and Analytics Features

### FEATURE A: Crop Disease Detection (REQ-1 to REQ-5)

| REQ | Description | Status | Implementation | File |
|-----|-------------|--------|----------------|------|
| REQ-1 | ML disease model with stub fallback | ✅ Complete | `DiseaseModelLoader` class with model loading and stub mode | `app/integrations/ml_disease.py` |
| REQ-2 | Colab training notebook | ✅ Complete | Complete notebook with Kaggle download, training, and model export | `ml/training/train_disease_model_colab.ipynb` |
| REQ-3 | Treatment recommendations | ✅ Complete | Treatments table seeded with organic/chemical options | `app/seed.py`, `app/models.py` |
| REQ-4 | Diagnosis history endpoints | ✅ Complete | GET /diagnoses and GET /diagnoses/{id} endpoints | `app/routers/diagnoses.py` |
| REQ-5 | Low confidence warning | ✅ Complete | Confidence threshold check (0.6) with retake-photo message | `app/routers/diagnoses.py` |

**Additional Safety Features**:
- Prohibited substances filter (SRS 5.2) - `app/models.py`, `app/routers/diagnoses.py`
- Consent record for training data reuse - `app/models.py`, `app/routers/diagnoses.py`
- Fixed disclaimer on every response - `app/routers/diagnoses.py`
- Image upload with compression (max 1MB) - `app/routers/diagnoses.py`

**API Endpoints**:
- POST /diagnoses - Create diagnosis with image upload
- GET /diagnoses - List all diagnoses for user's crops
- GET /diagnoses/{id} - Get specific diagnosis with treatments

---

### FEATURE B: Soil Health Analyzer (REQ-6 to REQ-9)

| REQ | Description | Status | Implementation | File |
|-----|-------------|--------|----------------|------|
| REQ-6 | Soil record CRUD | ✅ Complete | POST /soil-records, GET /soil-records endpoints | `app/routers/soil.py` |
| REQ-7 | Sensor data source tag | ✅ Complete | POST /soil-records/from-sensor with source='sensor' | `app/routers/soil.py` |
| REQ-8 | Crop nutrient requirements | ✅ Complete | crop_nutrient_requirements table seeded for 15 crops | `app/seed.py`, `app/models.py` |
| REQ-9 | Low/optimal/high flags | ✅ Complete | Soil analysis with status flags and explanations | `app/routers/soil.py` |

**API Endpoints**:
- POST /soil-records - Create manual soil record
- POST /soil-records/from-sensor - Create sensor soil record
- GET /soil-records - List all soil records for user's farms
- GET /soil-records/{id}/analyze - Analyze soil against crop requirements

**Seeded Data**:
- 15 crops with ideal pH/N/P/K ranges
- Values based on Indian agricultural standards

---

### FEATURE C: Water Usage Optimizer (REQ-10 to REQ-13)

| REQ | Description | Status | Implementation | File |
|-----|-------------|--------|----------------|------|
| REQ-10 | Weather API integration | ✅ Complete | OpenWeatherMap client with mock fallback | `app/integrations/weather.py` |
| REQ-11 | Irrigation recalculation | ✅ Complete | POST /irrigation-schedules/{id}/recalculate with rain check | `app/routers/irrigation.py` |
| REQ-12 | Notification logging | ✅ Complete | NotificationLog table created on schedule changes | `app/models.py`, `app/routers/irrigation.py` |
| REQ-13 | Manual override/postpone | ✅ Complete | POST /irrigation-schedules/{id}/postpone endpoint | `app/routers/irrigation.py` |

**Calculation Method**:
- Hargreaves method for evapotranspiration estimation
- Crop coefficients (Kc) for 15 Indian crops
- Rainfall subtraction (70% effective rainfall)
- Water amount in liters

**API Endpoints**:
- POST /irrigation-schedules - Create schedule with auto water calculation
- GET /irrigation-schedules - List schedules with filtering
- POST /irrigation-schedules/{id}/recalculate - Recalculate with weather forecast
- PUT /irrigation-schedules/{id} - Update schedule
- POST /irrigation-schedules/{id}/postpone - Postpone by N days

**Weather Integration**:
- OpenWeatherMap API (requires OPENWEATHER_API_KEY in .env)
- Mock fallback if API key not configured
- Current weather and 5-day forecast support

---

### FEATURE D: Yield Prediction (REQ-14 to REQ-16)

| REQ | Description | Status | Implementation | File |
|-----|-------------|--------|----------------|------|
| REQ-14 | Local yield model training | ✅ Complete | train_yield_model.py with synthetic dataset | `ml/training/train_yield_model.py` |
| REQ-15 | Yield prediction endpoint | ✅ Complete | POST /yield-predictions with ML integration | `app/routers/yield_predictions.py` |
| REQ-16 | Version history | ✅ Complete | Version tracking (regenerating creates new version) | `app/routers/yield_predictions.py` |

**Model Details**:
- Architecture: RandomForestRegressor (scikit-learn)
- Features: Crop, land size, rainfall, temperature, season
- Dataset: 3,000 synthetic samples
- R² Score: 0.93
- MAE: 35.4 quintals

**API Endpoints**:
- POST /yield-predictions - Create yield prediction
- GET /yield-predictions - List predictions for user's farms
- GET /yield-predictions/{id} - Get specific prediction
- GET /yield-predictions/crop/{crop_id}/history - Get version history

**Output Features**:
- Low/expected/high yield range
- Confidence label (low/medium/high)
- Harvest window estimation
- Version tracking

---

## Database Schema Changes

### New Tables (Migration 002)

| Table | Purpose | Status |
|-------|---------|--------|
| treatments | Disease treatment recommendations | ✅ Seeded |
| prohibited_substances | Banned agrochemicals in India | ✅ Seeded |
| crop_nutrient_requirements | Ideal soil nutrient ranges per crop | ✅ Seeded |
| yield_predictions | Yield prediction history | ✅ Created |

### Modified Tables

| Table | Changes | Status |
|-------|---------|--------|
| diagnoses | Added consent_record_id foreign key | ✅ Migrated |
| soil_records | Added source column (manual/sensor) | ✅ Migrated |

---

## Integration Points

### ML Integrations

| Integration | File | Purpose |
|-------------|------|---------|
| ml_disease.py | `app/integrations/ml_disease.py` | Disease detection with stub fallback |
| ml_yield.py | `app/integrations/ml_yield.py` | Yield prediction with stub fallback |
| weather.py | `app/integrations/weather.py` | OpenWeatherMap client with mock fallback |

### API Routers

| Router | File | Endpoints |
|--------|------|-----------|
| diagnoses | `app/routers/diagnoses.py` | Disease detection and history |
| soil | `app/routers/soil.py` | Soil health analyzer |
| irrigation | `app/routers/irrigation.py` | Water usage optimizer |
| yield_predictions | `app/routers/yield_predictions.py` | Yield prediction |

---

## Configuration

### Environment Variables

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| DATABASE_URL | MySQL connection string | Yes | - |
| JWT_SECRET | JWT signing key | Yes | - |
| OPENWEATHER_API_KEY | Weather API key | No | None (mock mode) |
| ML_DISEASE_MODEL_PATH | Disease model file path | No | ./ml/models/disease_model.h5 |
| ML_YIELD_MODEL_PATH | Yield model file path | No | ./ml/models/yield_model.pkl |

### Model Paths

| Model | Path | Status |
|-------|------|--------|
| Disease Model | ./ml/models/disease_model.h5 | Not present (stub mode) |
| Disease Labels | ./ml/models/class_labels.json | Not present (stub mode) |
| Disease Metadata | ./ml/models/metadata.json | Not present (stub mode) |
| Yield Model | ./ml/models/yield_model.pkl | ✅ Present (trained) |
| Yield Metadata | ./ml/models/yield_metadata.json | ✅ Present (trained) |

---

## Testing Status

### Stub Mode Testing (No Model Files)

| Feature | Test | Status |
|---------|------|--------|
| Disease Detection | POST /diagnoses with image | ✅ Stub works |
| Yield Prediction | POST /yield-predictions | ✅ Stub works |
| Soil Analysis | GET /soil-records/{id}/analyze | ✅ Works |
| Irrigation | POST /irrigation-schedules | ✅ Works |

### Real Model Testing

| Feature | Test | Status |
|---------|------|--------|
| Disease Detection | With trained model | ⏳ Pending (needs Colab training) |
| Yield Prediction | With trained model | ✅ Works (R²=0.93) |

---

## Documentation

| Document | File | Status |
|----------|------|--------|
| ML Models Guide | `docs/ML_MODELS.md` | ✅ Complete |
| Training Guide | `ml/README.md` | ✅ Complete |
| Colab Notebook | `ml/training/train_disease_model_colab.ipynb` | ✅ Complete |
| Training Script | `ml/training/train_yield_model.py` | ✅ Complete |

---

## Acceptance Criteria Status

### Part 2 Acceptance Criteria

| Criterion | Status | Notes |
|-----------|--------|-------|
| Backend works without model files | ✅ Verified | Stub mode tested and working |
| train_yield_model.py runs locally | ✅ Verified | Trained in <2 minutes, R²=0.93 |
| Colab notebook complete | ✅ Verified | Ready to run in Colab |
| Backend picks up trained models | ✅ Verified | Yield model auto-loads |
| Test works with/without models | ⏳ Pending | Need to write integration tests |
| Full pytest suite passes | ⏳ Pending | Need to update tests |
| ML_MODELS.md documentation | ✅ Complete | See docs/ML_MODELS.md |
| TRACEABILITY.md updated | ✅ Complete | This document |

---

## Known Limitations

1. **Disease Model**: Not trained (stub mode active)
   - Requires Colab training (10-15 minutes on GPU)
   - No dataset downloaded locally (by design)

2. **Yield Model**: Trained on synthetic data
   - 3,000 samples, not real agricultural data
   - R²=0.93 on synthetic data (may not reflect real performance)

3. **Weather API**: Mock mode by default
   - Requires OPENWEATHER_API_KEY for real data
   - Mock data uses seasonal variation

4. **Geography**: Optimized for India
   - Crops: 15 Indian crops
   - Locations: Maharashtra (Nashik, Pune)
   - Prohibited substances: Indian regulatory list

5. **Project Scope**: Semester project, not production
   - Small datasets
   - Minimal training
   - Demonstration accuracy only

---

## Next Steps (Optional Enhancements)

1. **Train Disease Model**
   - Run Colab notebook
   - Download and place model files
   - Test real inference

2. **Real Yield Data**
   - Find public crop yield dataset
   - Retrain model on real data
   - Validate with domain experts

3. **Add Tests**
   - Integration tests for stub/real model switching
   - Unit tests for ML integrations
   - End-to-end API tests

4. **Improve Weather**
   - Add OPENWEATHER_API_KEY to .env
   - Test real weather data
   - Add caching for weather API calls

5. **Model Monitoring**
   - Log prediction accuracy
   - Track model version usage
   - Add A/B testing framework

---

## Part 3: Marketplace, Alerts, Payments, and Admin Features

### FEATURE E: Pest Outbreak Alerts (REQ-17 to REQ-20)

| REQ | Description | Status | Implementation | File |
|-----|-------------|--------|----------------|------|
| REQ-17 | Auto-alert on diagnosis count threshold | ✅ Complete | Post-diagnosis check with haversine distance and time window | `app/routers/alerts.py`, `app/routers/diagnoses.py` |
| REQ-18 | Manual alert creation (officer/admin) | ✅ Complete | POST /alerts with disease, region, severity | `app/routers/alerts.py` |
| REQ-19 | Email notification on alert | ✅ Complete | SMTP integration with graceful fallback to log-only | `app/integrations/notifications.py` |
| REQ-20 | Preventive measures from treatments | ✅ Complete | Treatments filtered through prohibited substances | `app/routers/alerts.py` |

**API Endpoints**:
- POST /alerts - Create manual outbreak alert (officer/admin only)
- PATCH /alerts/{id}/retract - Retract alert (officer/admin only)
- GET /alerts?lat=&lon= - Get alerts within range (farmer-facing)

**Configuration**:
- outbreak_radius_km: Default 10km (configurable via admin panel)
- outbreak_days_window: Default 7 days (configurable)
- outbreak_threshold_count: Default 3 cases (configurable)
- outbreak_cooldown_hours: Default 24 hours (configurable)

**Safety Features**:
- No individual farmer location/identity exposed in alerts
- Cooldown period prevents duplicate alerts for same region
- Preventive measures filtered through prohibited substances

---

### FEATURE F: Marketplace (REQ-35 to REQ-38)

| REQ | Description | Status | Implementation | File |
|-----|-------------|--------|----------------|------|
| REQ-35 | Listing CRUD | ✅ Complete | POST /listings, PATCH /listings/{id}, GET /listings | `app/routers/marketplace.py` |
| REQ-36 | Listing filters and sorting | ✅ Complete | Filter by crop, price range, distance (haversine), sort by price/distance/newest | `app/routers/marketplace.py` |
| REQ-37 | Market price benchmark | ✅ Complete | Pulls from market_prices table with below/near/above label | `app/routers/marketplace.py` |
| REQ-38 | Threaded messaging | ✅ Complete | POST/GET /listings/{id}/messages (farmer <-> buyer) | `app/routers/marketplace.py` |

**API Endpoints**:
- POST /listings - Create listing (farmer only)
- GET /listings - List with filters (crop, price, distance, sort)
- GET /listings/{id} - Get specific listing
- PATCH /listings/{id} - Update/close listing (seller only)
- POST /listings/{id}/messages - Send message
- GET /listings/{id}/messages - Get conversation

**Features**:
- Optional photo upload
- Location-based filtering with haversine distance
- Market price benchmark comparison
- Simple threaded messaging (no real-time needed)

---

### FEATURE G: Payments - Razorpay Test Mode

| Feature | Description | Status | Implementation | File |
|---------|-------------|--------|----------------|------|
| Razorpay Integration | Official SDK with test mode | ✅ Complete | RazorpayClient with mock fallback | `app/integrations/payments.py` |
| Order Creation | POST /transactions creates Razorpay order | ✅ Complete | Real order when keys present, mock order otherwise | `app/routers/transactions.py` |
| Payment Verification | GET /transactions/{id}/verify polling | ✅ Complete | Direct Razorpay payment.fetch (no webhooks) | `app/routers/transactions.py` |
| Transaction Lifecycle | initiated -> confirmed -> completed/failed/refunded | ✅ Complete | PATCH /transactions/{id}/status for manual updates | `app/routers/transactions.py` |

**API Endpoints**:
- POST /transactions - Create transaction and Razorpay order (buyer only)
- GET /transactions/{id}/verify - Verify payment status via polling
- PATCH /transactions/{id}/status - Manual status update (farmer/admin)
- GET /transactions - List user's transactions
- GET /transactions/{id} - Get specific transaction

**Configuration**:
- RAZORPAY_KEY_ID: Test mode key ID (optional, falls back to mock)
- RAZORPAY_KEY_SECRET: Test mode key secret (optional, falls back to mock)

**Design Decision**:
- Verification via direct polling instead of webhooks
- Simplification for local development (no ngrok needed)
- Webhooks noted as production-grade alternative in ASSUMPTIONS.md

---

### Supporting Modules

#### Subsidy/Scheme Eligibility Checker

| Feature | Description | Status | Implementation | File |
|---------|-------------|--------|----------------|------|
| Scheme Seeding | 8-10 real Indian government schemes | ✅ Complete | PM-KISAN, PMFBY, Soil Health Card, KCC, etc. | `app/seed.py` |
| Rule-based Matching | Land size, crop type, state eligibility | ✅ Complete | POST /scheme-matches with eligibility reason | `app/routers/schemes.py` |

**API Endpoints**:
- POST /scheme-matches - Get eligible schemes for a farm
- GET /schemes - List all active schemes

**Seeded Schemes**:
- PM-KISAN (₹6,000/year income support)
- PMFBY (Crop insurance)
- Soil Health Card (Free soil testing)
- KCC (Credit card for farmers)
- PM-Kisan Samridhi (One-stop centers)
- National Food Security Mission
- Micro Irrigation Scheme
- Rashtriya Krishi Vikas Yojana

#### Finance Tracker

| Feature | Description | Status | Implementation | File |
|---------|-------------|--------|----------------|------|
| Finance Entry CRUD | Income/expense tracking per farm | ✅ Complete | POST /finance-entries, GET /finance-entries | `app/routers/finance.py` |
| Summary Dashboard | Totals by category, net profit/loss, monthly breakdown | ✅ Complete | GET /finance-entries/summary?farm_id= | `app/routers/finance.py` |

**API Endpoints**:
- POST /finance-entries - Create finance entry
- GET /finance-entries - List entries with filters
- GET /finance-entries/summary - Get farm financial summary
- GET /finance-entries/{id} - Get specific entry

---

### FEATURE H: Admin Analytics Dashboard (NEW)

| Feature | Description | Status | Implementation | File |
|---------|-------------|--------|----------------|------|
| Dashboard Summary | Platform-wide metrics snapshot | ✅ Complete | GET /admin/dashboard (admin only) | `app/routers/admin.py` |

**Metrics Included**:
- Total users by role
- Total diagnoses (and low-confidence count)
- Top 5 most diagnosed diseases
- Active alerts count
- Total listings (open vs closed)
- Total transaction volume (completed transactions)
- Total registered farms

**API Endpoints**:
- GET /admin/dashboard - Get platform summary (admin only)

---

### FEATURE I: Config Management (NEW)

| Feature | Description | Status | Implementation | File |
|---------|-------------|--------|----------------|------|
| Config CRUD | Key-value configuration management | ✅ Complete | GET/PATCH /admin/config (admin only) | `app/routers/admin.py` |
| User Management | List/search users | ✅ Complete | GET /admin/users (admin only) | `app/routers/admin.py` |
| Audit Logs | Recent activity logs | ✅ Complete | GET /admin/audit-logs (admin only) | `app/routers/admin.py` |

**Configurable Thresholds**:
- outbreak_radius_km
- outbreak_days_window
- outbreak_threshold_count
- outbreak_cooldown_hours
- disease_confidence_threshold

**API Endpoints**:
- GET /admin/config - List all config values
- PATCH /admin/config/{key} - Update config value
- GET /admin/users - List/search users
- GET /admin/audit-logs - Get recent audit logs

---

## Database Schema Changes (Part 3)

### New Tables (Migration 003)

| Table | Purpose | Status |
|-------|---------|--------|
| outbreak_alerts | Pest outbreak alerts with geospatial data | ✅ Created |
| messages | Marketplace messaging between farmers and buyers | ✅ Created |
| schemes | Government agricultural schemes with eligibility criteria | ✅ Seeded |
| finance_entries | Farm income/expense tracking | ✅ Created |
| system_config | Configurable system thresholds | ✅ Seeded |
| market_prices | Market price benchmarks for crops | ✅ Seeded |

### Modified Tables

| Table | Changes | Status |
|-------|---------|--------|
| listings | Added latitude, longitude, unit, photo_path columns | ✅ Updated |
| transactions | Added razorpay_order_id, razorpay_payment_id columns | ✅ Updated |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-16 | 1.0 | Initial Part 2 implementation |
| 2024-01-16 | 2.0 | Part 3 implementation - Alerts, Marketplace, Payments, Admin |
