# AgriAssist Assumptions and Design Decisions

This document documents key assumptions, simplifications, and design decisions made during the development of AgriAssist.

## Project Scope

### Semester Project Constraints

AgriAssist is designed as a **semester college project**, not a production system. The following assumptions reflect this scope:

1. **Dataset Size**: Small, scoped datasets suitable for demonstration
   - Disease: 300 images/class (sampled from PlantVillage)
   - Yield: 3,000 synthetic samples
   - Market prices: 10 crops with static benchmark data

2. **Accuracy Targets**: Moderate accuracy for demonstration purposes
   - Disease: 91.55% validation accuracy (trained model present but incompatible with current TensorFlow)
   - Yield: R² = 0.93 on synthetic data

3. **Geography**: Optimized for Indian agricultural conditions
   - Crops: 15 common Indian crops
   - Locations: Maharashtra region (Nashik, Pune)
   - Schemes: 8 real Indian government agricultural schemes
   - Prohibited substances: Indian regulatory list

4. **Real-time Constraints**: Not optimized for real-time production use
   - Disease model: ~500ms inference (MobileNetV2) when loaded
   - Yield model: ~50ms inference (RandomForest)
   - No message queues or background workers

5. **Training**: Minimal training for fast iteration
   - Disease: 8 epochs with early stopping
   - Yield: 100 trees, max depth 10

---

## Technology Choices

### Database

**Assumption**: MySQL with SQLAlchemy ORM

**Rationale**:
- Relational data model is natural for the domain (users, farms, crops, transactions)
- SQL allows complex queries for admin dashboard and analytics
- SQLAlchemy provides robust ORM with good test support
- MySQL is widely available and familiar to students

**Limitations**:
- No spatial indexing for geospatial queries (haversine calculated in Python)
- No full-text search (basic string matching only)

---

### Authentication

**Assumption**: JWT-based stateless authentication

**Rationale**:
- Simple to implement with FastAPI
- No session management overhead
- Easy to test
- Suitable for API-first architecture

**Limitations**:
- No refresh token rotation (security best practice for production)
- No token revocation middleware
- Access tokens expire after 60 minutes (configurable)

---

### ML Model Integration

**Assumption**: Stub fallback pattern for all ML integrations

**Rationale**:
- Allows development and testing without trained models
- Students can demonstrate functionality even without training infrastructure
- Easy to switch between stub and real models

**Current Status**:
- Disease model: Trained model present but TensorFlow version incompatible (stub mode active)
- Yield model: Trained and working
- Weather: Mock mode by default (requires API key for real data)

---

### Payment Integration

**Assumption**: Razorpay test mode with direct polling (no webhooks)

**Rationale**:
- Webhooks require ngrok or public endpoint for local development
- Direct polling is simpler for semester project
- Razorpay test mode allows full payment flow without real money
- Students can demonstrate the complete transaction lifecycle

**Production Alternative**:
- Webhooks would be used in production for real-time payment confirmation
- Ngrok or similar tunneling service would be needed for local webhook testing
- This is a deliberate simplification for local development feasibility

**Design Decision**:
- GET /transactions/{id}/verify endpoint for manual verification
- PATCH /transactions/{id}/status for manual completion/refund
- Dual approach: automated verification (polling) + manual override

---

### Email Notifications

**Assumption**: SMTP with graceful fallback to log-only mode

**Rationale**:
- Students may not have SMTP credentials readily available
- Log-only mode allows testing notification logic without email setup
- Standard smtplib library (no third-party dependencies)

**Configuration**:
- SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL
- Falls back to log-only if credentials not configured
- NotificationLog table tracks all attempts regardless of success

**Limitations**:
- No email queue (synchronous sending)
- No retry logic on failure
- No HTML email templates (plain text only)

---

### Geospatial Calculations

**Assumption**: Haversine formula calculated in Python (no PostGIS)

**Rationale**:
- Avoids database complexity (PostGIS installation)
- Python implementation is sufficient for demo scale
- No additional database extensions needed

**Limitations**:
- Not optimized for large-scale geospatial queries
- No spatial indexing
- Calculations run in application layer, not database

---

### Real-time Features

**Assumption**: No real-time features (no websockets, no message queues)

**Rationale**:
- Simplifies architecture for semester project
- Messaging is request/response (pull model, not push)
- No infrastructure complexity (Redis, RabbitMQ, etc.)

**Limitations**:
- No instant notifications
- Messaging requires page refresh
- No collaborative features

---

## Simplifications Made

### 1. Disease Model TensorFlow Compatibility

**Issue**: Trained model on Colab is incompatible with TensorFlow 2.22.0-rc0

**Resolution**:
- System falls back to stub mode gracefully
- Stub mode uses deterministic hash-based predictions
- Documentation updated to explain compatibility issue
- Recommendation: Retrain model on current TensorFlow version or downgrade TensorFlow

**Impact**: API works identically in structure, only prediction source differs

---

### 2. Webhooks vs Polling for Payments

**Simplification**: Direct polling instead of webhooks for payment verification

**Reason**:
- Webhooks require public endpoint (ngrok needed for local dev)
- Polling is simpler for semester project scope
- Manual status update endpoint provides fallback

**Impact**:
- Slight delay in payment confirmation (polling interval)
- No real-time payment notifications
- Acceptable for demo purposes

---

### 3. Image Upload

**Simplification**: Max 1MB limit with JPEG compression

**Reason**:
- Prevents storage bloat
- Fast uploads for demo
- No CDN integration needed

**Impact**:
- Lower image quality acceptable for demo
- No support for high-resolution images

---

### 4. Weather API

**Simplification**: Mock mode by default with seasonal variation

**Reason**:
- Students may not have OpenWeatherMap API key
- Mock data provides reasonable demo experience
- Easy to enable real weather with API key

**Impact**:
- Not accurate weather data in mock mode
- Seasonal variation is deterministic, not real-time

---

### 5. Market Prices

**Simplification**: Static benchmark data seeded from database

**Reason**:
- No real-time market price API integration
- Static data sufficient for demo
- Easy to update by re-seeding

**Impact**:
- Prices may not reflect current market conditions
- No historical price tracking

---

## Security Considerations

### Password Storage

**Assumption**: bcrypt password hashing via passlib

**Rationale**:
- Industry standard for password hashing
- Built-in salt handling
- Cost factor can be adjusted for security vs performance

**Limitations**:
- No password complexity requirements
- No password expiration
- No account lockout on failed attempts

### RBAC

**Assumption**: Role-based access control with 4 roles (farmer, buyer, officer, admin)

**Rationale**:
- Simple permission model suitable for demo
- Easy to understand and test
- Covers main use cases

**Limitations**:
- No fine-grained permissions
- No role hierarchy
- No permission inheritance

### Data Privacy

**Assumption**: No PII exposed in alerts (aggregated region info only)

**Rationale**:
- Protects farmer privacy
- Compliance with data minimization principle
- Suitable for demo scenario

**Limitations**:
- No encryption at rest
- No data retention policies
- No GDPR/CCPA compliance features

---

## Testing Strategy

### Unit Tests

**Assumption**: Pytest with in-memory SQLite for unit tests

**Rationale**:
- Fast test execution
- No external dependencies
- Easy to set up and tear down

**Limitations**:
- Not testing against MySQL (production database)
- May miss MySQL-specific issues

### Integration Tests

**Assumption**: Test client with database override

**Rationale**:
- Tests FastAPI endpoints end-to-end
- Validates request/response cycle
- Tests authentication and authorization

**Limitations**:
- No multi-user concurrency testing
- No performance testing

---

## Deployment Considerations

### Local Development

**Assumption**: Uvicorn server for local development

**Rationale**:
- Built-in ASGI server
- Easy to run with `uvicorn app.main:app --reload`
- Suitable for development

**Production Note**:
- Would use Gunicorn + Uvicorn workers in production
- Would use environment-specific configuration
- Would use proper logging and monitoring

### Database Migrations

**Assumption**: Alembic for database migrations

**Rationale**:
- Industry standard for Python/SQLAlchemy
- Version-controlled schema changes
- Easy to roll back

**Current Status**:
- Tables created via Base.metadata.create_all for development
- Alembic configured but migrations not yet created
- Acceptable for demo, not for production

---

## Future Enhancements (Production-Grade)

To make AgriAssist production-ready, the following would be needed:

### 1. Real-time Features
- Websockets for instant messaging
- Redis for message queuing
- Push notifications for alerts

### 2. Scalability
- Database connection pooling
- Caching layer (Redis)
- CDN for static assets
- Load balancing

### 3. Security
- HTTPS enforcement
- Rate limiting
- Input validation and sanitization
- SQL injection prevention (already handled by ORM)
- XSS prevention (already handled by FastAPI)

### 4. Monitoring
- Application logging (ELK stack)
- Error tracking (Sentry)
- Performance monitoring (APM)
- Health check endpoints

### 5. Data Quality
- Real agricultural datasets
- Expert validation of ML predictions
- Continuous model retraining
- A/B testing framework

### 6. Geographic Features
- PostGIS for spatial queries
- Spatial indexing
- Advanced geospatial analytics

### 7. Email
- Email queue (Celery + Redis)
- HTML email templates
- Email service provider (SendGrid, AWS SES)
- Retry logic with exponential backoff

---

## Acceptance of Scope

AgriAssist is explicitly designed as a **semester project demonstration**. The simplifications documented here are intentional trade-offs to:

1. Keep the project achievable within a semester timeline
2. Avoid infrastructure complexity (ngrok, message queues, etc.)
3. Allow students to focus on core functionality
4. Provide a solid foundation for learning

The system is **not production-ready** but provides a **comprehensive demonstration** of:
- Full-stack web development (FastAPI + MySQL)
- ML model integration with stub fallback
- Role-based access control
- RESTful API design
- Database design and migrations
- Integration with external services (weather, payments, email)
- Admin dashboard and analytics

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-16 | 1.0 | Initial document created for Part 3 |
