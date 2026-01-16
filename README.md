# Goal Tracking API

A FastAPI application for tracking personal goals across three domains:
- **Running Training** - Track runs with distance, pace, workout type (goal: sub-2-hour half marathon)
- **Social Hangouts** - Track who you hung out with, where, and your mood
- **Project Work Sessions** - Track hours worked and project status

## Tech Stack

**Backend:**
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL (Supabase compatible)
- **Migrations**: Alembic

**Frontend:**
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS

**Deployment:**
- Backend: Railway
- Frontend: Vercel (or any Next.js host)

## Quick Start (Local Development)

### Option 1: Using Docker Compose (Recommended)

```bash
# Clone and enter the project
cd goal-tracking

# Start the database and API
docker-compose up -d

# The API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
# Web UI at http://localhost:8000/ui
```

### Option 2: Local Development (Backend + Frontend)

**Terminal 1 - Start Backend (FastAPI):**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Supabase DATABASE_URL

# Run migrations (if needed)
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload

# API will be available at http://127.0.0.1:8000
# API docs at http://127.0.0.1:8000/docs
```

**Terminal 2 - Start Frontend (Next.js):**
```bash
# Navigate to client directory
cd client

# Install dependencies (first time only)
npm install

# Create environment file (first time only)
cp .env.local.example .env.local
# (default: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000)

# Start the dev server
npm run dev

# Frontend will be available at http://localhost:3000
```

**Access Points:**
- **Next.js UI**: http://localhost:3000 (primary interface)
- **API Docs**: http://127.0.0.1:8000/docs
- **Legacy Jinja UI** (deprecated): http://127.0.0.1:8000/ui

## Environment Variables

**Backend (.env):**
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `APP_ENV` | Environment (local/production) | `local` |
| `LOG_LEVEL` | Logging level | `info` |
| `PORT` | Server port (Railway sets this) | `8000` |

**Frontend (client/.env.local):**
| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI backend URL | `http://localhost:8000` |

## Next.js Frontend

The primary user interface is a Next.js application located in `/client`.

### Pages

- **/** - Home dashboard with recent activities and quick action buttons
- **/runs/new** - Add a new run
- **/hangouts/new** - Add a new hangout
- **/work/new** - Add a new work session

### Data Entry Features

**Run Entry (Miles & Min/Mile):**
- Input distance in miles (e.g., 5.5)
- Input pace in mm:ss format (e.g., 8:30)
- Client-side unit conversion:
  - Distance: miles → meters (1 mile = 1609.344 meters)
  - Pace: min/mile → sec/km
- Timestamps set to 12:00 UTC deterministically

**Hangout Entry:**
- Comma-separated participant names
- Participants auto-created or matched by name
- Optional mood rating (1-5)

**Work Session Entry:**
- Default project: "Goal Tracking"
- Status dropdown (idea/todo/in_progress/blocked/done)
- Optional duration tracking

### CORS Configuration

The FastAPI backend includes CORS middleware configured for local development:
- Allowed origins: `http://localhost:3000`
- All methods and headers allowed for development

## iPhone Client Contract

This section documents the API contract for mobile app clients (iPhone, Android).

### Recommended Endpoint: POST /runs/simple

**This is the recommended endpoint for mobile apps.** It accepts human-friendly inputs and handles all unit conversions server-side.

```bash
POST /runs/simple
Content-Type: application/json

{
  "date": "2026-01-14",
  "distance_miles": 5.5,
  "pace_min_per_mile": "8:30",
  "notes": "Great morning run!",
  "workout_type": "easy"
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | Yes | Date in `YYYY-MM-DD` format (e.g., `"2026-01-14"`) |
| `distance_miles` | number | Yes | Distance in miles (e.g., `5.5`) |
| `pace_min_per_mile` | string | Yes | Pace in `mm:ss` format (e.g., `"8:30"`) |
| `notes` | string | No | Optional notes about the run |
| `workout_type` | string | No | One of: `easy`, `tempo`, `intervals`, `long`, `race`, `recovery`. Defaults to `easy` |

**Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-14T20:00:00.000000Z"
}
```

**Timezone Handling:**
- The `date` field is interpreted as a local date in **America/Los_Angeles** timezone
- Time is set to 12:00 noon local to avoid DST edge cases
- The timestamp is converted to UTC before storage

**Unit Conversions (Server-Side):**
- Distance: `distance_miles × 1609.344` → stored as meters (integer)
- Pace: `(minutes × 60 + seconds) ÷ 1.609344` → stored as seconds per km (integer)

**Error Response (400 Bad Request):**

```json
{
  "detail": "Invalid date format '2026/01/14'. Use YYYY-MM-DD (preferred) or MM/DD/YYYY."
}
```

### Alternative: POST /runs (Internal Format)

For clients that prefer to handle unit conversions themselves, use the internal endpoint:

```bash
POST /runs
Content-Type: application/json

{
  "title": "Morning tempo run",
  "start_at": "2024-01-15T07:00:00Z",
  "distance_meters": 10000,
  "avg_pace_sec_per_km": 300,
  "workout_type": "tempo"
}
```

This endpoint expects pre-converted values (meters, seconds per km, ISO timestamps).

### OpenAPI Documentation

Full API documentation with interactive testing is available at:
- Local: http://localhost:8000/docs
- The `/runs/simple` endpoint includes detailed examples in the OpenAPI schema

## API Endpoints

### Health Check
```bash
GET /health
# Returns: {"ok": true, "db": "ok"}
```

### Create a Run (Simple - Recommended for Mobile)
```bash
POST /runs/simple
Content-Type: application/json

{
  "date": "2026-01-14",
  "distance_miles": 5.5,
  "pace_min_per_mile": "8:30",
  "notes": "Morning run"
}
```

### Create a Run (Internal Format)
```bash
POST /runs
Content-Type: application/json

{
  "title": "Morning tempo run",
  "start_at": "2024-01-15T07:00:00Z",
  "end_at": "2024-01-15T07:45:00Z",
  "distance_meters": 10000,
  "workout_type": "tempo",
  "rpe": 7,
  "surface": "road",
  "shoe": "Nike Pegasus",
  "tags": ["morning", "tempo"]
}
```

### Create a Hangout
```bash
POST /hangouts
Content-Type: application/json

{
  "title": "Coffee with friends",
  "start_at": "2024-01-15T14:00:00Z",
  "location_name": "Blue Bottle Coffee",
  "location_type": "cafe",
  "mood": 4,
  "participants": [
    {"name": "Alice", "handle": "@alice"},
    {"name": "Bob"}
  ]
}
```

### Create a Work Session
```bash
POST /work-sessions
Content-Type: application/json

{
  "title": "Implement user auth",
  "start_at": "2024-01-15T09:00:00Z",
  "end_at": "2024-01-15T12:00:00Z",
  "project": "goal-tracker",
  "area": "backend",
  "status": "in_progress"
}
```

### Get Recent Activities
```bash
GET /activity/recent?limit=10

# Returns array of recent activities with details
[
  {
    "id": "uuid",
    "type": "run",
    "title": "Morning Run",
    "start_at": "2024-01-15T12:00:00Z",
    "created_at": "2024-01-15T12:05:00Z",
    "duration_min": 45,
    "run_detail": {
      "distance_meters": 8000,
      "avg_pace_sec_per_km": 317
    }
  }
]
```

### Get Weekly Stats
```bash
GET /stats/weekly?start_date=2024-01-01&end_date=2024-01-31

# Returns:
{
  "total_runs": 5,
  "total_distance_meters": 45000,
  "total_run_duration_min": 225,
  "total_hangouts": 3,
  "total_work_sessions": 10,
  "total_work_minutes": 1200,
  "weeks": [
    {
      "week_start": "2024-01-01",
      "runs_count": 2,
      "distance_meters": 18000,
      "run_duration_min": 90,
      "hangouts_count": 1,
      "work_sessions_count": 4,
      "work_minutes": 480
    }
  ]
}
```

## Database Schema

See `db/schema.sql` for the complete DDL. Key tables:

- `activity` - Base table for all activities (run, hangout, work)
- `run_detail` - Running-specific data (distance, pace, workout type)
- `hangout_detail` - Hangout-specific data (location, mood)
- `work_detail` - Work session data (project, status)
- `person` - People who participate in activities
- `activity_participant` - Links activities to participants

## Running Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Downgrade one version
alembic downgrade -1
```

## Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test files
pytest tests/test_conversions.py -v
pytest tests/test_ui_integration.py -v
```

### Testing Unit Conversions

The test suite includes comprehensive tests for unit conversions:
- `tests/test_conversions.py` - Unit conversion functions
- `tests/test_ui_integration.py` - End-to-end tests for run creation with conversions

Key tests verify:
- 1 mile = 1609.344 meters
- Pace conversion: min/mile → sec/km
- Round-trip conversions preserve values within acceptable tolerance

## Project Structure

```
goal-tracking/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app and JSON API routes
│   ├── ui_routes.py     # Web UI routes (forms)
│   ├── conversions.py   # Unit conversion utilities
│   ├── config.py        # Settings management
│   ├── db.py            # Database connection
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database operations (canonical)
│   └── utils.py         # Helper functions
├── templates/           # Jinja2 HTML templates
│   ├── base.html        # Base template
│   ├── home.html        # UI homepage
│   ├── run_form.html    # Run entry form
│   ├── hangout_form.html  # Hangout entry form
│   └── work_form.html   # Work session form
├── static/
│   └── style.css        # CSS styles
├── alembic/
│   ├── versions/        # Migration files
│   ├── env.py
│   └── script.py.mako
├── db/
│   └── schema.sql       # Raw DDL
├── tests/
│   ├── conftest.py      # Test fixtures
│   ├── test_api.py      # JSON API tests
│   ├── test_conversions.py  # Unit conversion tests
│   └── test_ui_integration.py  # UI integration tests
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
└── DEPLOY.md
```

## Deployment

See [DEPLOY.md](DEPLOY.md) for Railway deployment instructions.
