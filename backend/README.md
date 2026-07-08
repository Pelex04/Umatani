# UMATANI — Student Talent & Business Discovery Platform

> *"Umatani"* is a Chichewa word meaning **"What do you do?"**

UMATANI helps students showcase their businesses and skills while allowing anyone to discover trusted student entrepreneurs at African universities.

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- A PostgreSQL database (Supabase free tier works perfectly)

### 2. Clone and install

```bash
git clone https://github.com/Pelex04/umatani.git
cd umatani
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your values:
#   DATABASE_URL=postgresql+asyncpg://...
#   JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
#   STORAGE_BACKEND=local   # for development
```

### 4. Run migrations

```bash
python -m alembic upgrade head
```

### 5. Seed demo data (optional but recommended for testing)

```bash
python -m scripts.seed
```

This creates:
- An approved school (MUBAS)
- 12 categories
- An admin account: `admin@umatani.app` / `Admin@Umatani2026`
- 3 verified business owners with approved profiles and reviews

### 6. Start the API

```bash
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** to explore the full API.

---

## Create the first admin (production)

Admin accounts are never self-service-registerable. Use the bootstrap script:

```bash
python -m scripts.create_admin --email admin@umatani.app --name "Platform Admin"
# Prompts for password interactively
```

---

## User Flows

### Visitor (no account needed)
```
GET /api/v1/businesses                    # Browse / search
GET /api/v1/businesses/{id}               # View profile
GET /api/v1/businesses/slug/{slug}        # View profile by slug
GET /api/v1/reviews?business_id={id}      # Read reviews
GET /api/v1/schools                       # Browse schools
GET /api/v1/categories                    # Browse categories
```

### Business Owner
```
POST /api/v1/auth/register                # Register with school email
POST /api/v1/auth/verify-email            # Verify email
POST /api/v1/media/upload                 # Upload student ID image
POST /api/v1/auth/student-id             # Submit student ID for review
POST /api/v1/auth/login                   # Login → access + refresh tokens
POST /api/v1/businesses                   # Create business profile (after admin approval)
PATCH /api/v1/businesses/me               # Update profile
PATCH /api/v1/businesses/me/logo          # Set logo
PATCH /api/v1/businesses/me/cover         # Set cover image
POST /api/v1/businesses/me/portfolio      # Add portfolio item
DELETE /api/v1/businesses/me/portfolio/{id}
POST /api/v1/reviews/{id}/reply           # Reply to a review on your business
```

### Admin
```
GET  /api/v1/admin/stats                  # Platform analytics
GET  /api/v1/admin/users                  # User management
PATCH /api/v1/admin/users/{id}/verify     # Approve student ID → mark verified
PATCH /api/v1/admin/users/{id}/suspend    # Suspend user
GET  /api/v1/admin/schools                # All schools (any status)
POST /api/v1/admin/schools                # Add school
PATCH /api/v1/admin/schools/{id}/approve  # Approve school
PATCH /api/v1/admin/schools/{id}/suspend
GET  /api/v1/admin/businesses             # All businesses
PATCH /api/v1/admin/businesses/{id}/approve
PATCH /api/v1/admin/businesses/{id}/suspend
GET  /api/v1/admin/reviews/{id}/flag
GET  /api/v1/admin/support/reports        # View reports
PATCH /api/v1/admin/support/reports/{id} # Resolve report
GET  /api/v1/admin/support/tickets        # View tickets
PATCH /api/v1/admin/support/tickets/{id} # Respond to ticket
GET  /api/v1/admin/audit-logs             # Full audit trail
GET  /api/v1/admin/media/signed-url       # View student ID images
```

---

## Architecture

```
app/
  core/           # Config, database, security (Argon2id + JWT), rate limiter, email
  shared/         # Base repository, audit log model + service
  modules/
    auth/         # Registration, login, email verification, student ID submission
    schools/      # School CRUD + admin approval workflow
    categories/   # Admin-managed business taxonomy
    businesses/   # Business profiles, services, portfolio
    reviews/      # Ratings, replies, anti-spam, admin moderation
    media/        # Upload validation (magic-byte sniffing), storage abstraction
    support/      # Reports + support tickets
    admin/        # Dashboard stats, user management, audit logs
scripts/
  create_admin.py # Bootstrap first admin account
  seed.py         # Demo data for local testing
alembic/          # Database migrations
tests/
  unit/           # Security primitives, upload validation, storage
  integration/    # Full HTTP flow tests (125 tests, 0 failures)
```

**Stack**: FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL · Alembic · Argon2id · JWT · Supabase Storage

---

## Running Tests

```bash
export JWT_SECRET_KEY="any-long-test-secret"
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/umatani_test"
export ENVIRONMENT=development
export STORAGE_BACKEND=local

python -m pytest tests/ -q
# 125 passed in ~25s (uses in-memory SQLite — no live DB needed for tests)
```

---

## Deployment (Render)

1. Set environment variables in Render dashboard (see `.env.example`)
2. Build command: `pip install -r requirements.txt && python -m alembic upgrade head`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Run seed script once via Render Shell: `python -m scripts.seed`
