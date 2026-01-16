# Validation Guide for UI Implementation

This guide contains exact commands to validate the UI implementation.

## 1. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

Expected output: Should install `jinja2` and `python-multipart` if not already installed.

## 2. Run Unit Conversion Tests

```bash
pytest tests/test_conversions.py -v
```

**Expected output:**
```
15 passed in < 1 second
```

**What this verifies:**
- ✅ 1 mile = 1609.344 meters conversion
- ✅ min/mile → sec/km pace conversion
- ✅ Round-trip conversions preserve values
- ✅ Pace format validation (mm:ss with seconds 00-59)

## 3. Run Integration Tests (Requires Database)

If you have DATABASE_URL configured in `.env`:

```bash
pytest tests/test_ui_integration.py::TestConversionConstants -v
```

**Expected output:**
```
2 passed in < 1 second
```

**Full integration tests** (requires Supabase connection):
```bash
pytest tests/test_ui_integration.py -v
```

This tests:
- ✅ Creating runs via JSON API with converted units
- ✅ Rows in `activity` and `run_detail` tables
- ✅ Unit conversions: 5.5 miles = 8851 meters, 8:30/mile = 317 sec/km

## 4. Start the Server

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## 5. Verify UI is Accessible

### Homepage
Open in browser: **http://127.0.0.1:8000/ui**

**Expected:**
- ✅ Navigation bar with links to Add Run, Add Hangout, Add Work Session
- ✅ Recent activities tables (may be empty or show seeded data)
- ✅ Page styled with CSS (blue header, white cards)

### Run Form
Open: **http://127.0.0.1:8000/ui/runs**

**Expected:**
- ✅ Date input field
- ✅ Distance (miles) input with step="0.01"
- ✅ Pace (min/mile) input with pattern validation (mm:ss)
- ✅ Notes textarea
- ✅ Save and Cancel buttons
- ✅ Info box explaining unit conversions

### Hangout Form
Open: **http://127.0.0.1:8000/ui/hangouts**

**Expected:**
- ✅ Title input (required)
- ✅ Location name, location type inputs
- ✅ Mood input (1-5)
- ✅ Participants input (comma-separated names)
- ✅ Notes textarea

### Work Form
Open: **http://127.0.0.1:8000/ui/work**

**Expected:**
- ✅ Title input
- ✅ Project input (default: "Goal Tracking")
- ✅ Area, duration inputs
- ✅ Status dropdown (In Progress selected by default)
- ✅ Artifact link and notes

## 6. Test Form Submission (Manual)

### Test Run Entry

1. Go to http://127.0.0.1:8000/ui/runs
2. Fill in:
   - Date: Today's date
   - Distance: `3.1` (miles)
   - Pace: `8:00` (min/mile)
   - Notes: `Test run`
3. Click "Save Run"

**Expected behavior:**
- ✅ Redirects to http://127.0.0.1:8000/ui (PRG pattern)
- ✅ New run appears in "Recent Runs" table
- ✅ Distance shown as "3.1 mi"
- ✅ Pace shown as "8:00/mi"

**Database verification (optional):**
```sql
SELECT
  a.title,
  rd.distance_meters,
  rd.avg_pace_sec_per_km
FROM activity a
JOIN run_detail rd ON rd.activity_id = a.id
WHERE a.title LIKE '%3.1 mi%'
ORDER BY a.created_at DESC
LIMIT 1;
```

Expected values:
- `distance_meters`: 4989 (3.1 miles × 1609.344)
- `avg_pace_sec_per_km`: 298 (8:00/mile = 480 sec/mile ÷ 1.609344)

### Test Hangout Entry

1. Go to http://127.0.0.1:8000/ui/hangouts
2. Fill in:
   - Title: `Coffee with Alice`
   - Location Name: `Blue Bottle`
   - Mood: `5`
   - Participants: `Alice, Bob`
3. Click "Save Hangout"

**Expected:**
- ✅ Redirects to /ui
- ✅ New hangout in "Recent Hangouts" table
- ✅ Shows participants: "Alice, Bob"
- ✅ Shows mood: ⭐⭐⭐⭐⭐

### Test Work Session Entry

1. Go to http://127.0.0.1:8000/ui/work
2. Fill in:
   - Title: `UI implementation`
   - Project: `Goal Tracking`
   - Duration: `120`
   - Status: `Done`
3. Click "Save Work Session"

**Expected:**
- ✅ Redirects to /ui
- ✅ New work session in "Recent Work Sessions" table
- ✅ Shows duration: "120 min"
- ✅ Shows status badge: "done" (green)

## 7. Verify JSON API Still Works

The UI should NOT break the existing JSON API.

```bash
# Test JSON health endpoint
curl http://127.0.0.1:8000/health

# Expected: {"ok":true,"db":"ok"}
```

```bash
# Test creating run via JSON API (with unit conversions)
curl -X POST http://127.0.0.1:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API test run",
    "start_at": "2026-01-15T12:00:00Z",
    "distance_meters": 8047,
    "avg_pace_sec_per_km": 310,
    "workout_type": "easy"
  }'

# Expected: {"id":"<uuid>","created_at":"<timestamp>"}
```

Verify in UI: Refresh http://127.0.0.1:8000/ui and see "API test run" in Recent Runs.

## 8. Test Error Handling

### Invalid Pace Format

1. Go to /ui/runs
2. Enter pace as `830` (missing colon)
3. Click Save

**Expected:**
- ✅ Error message: "Pace must be in mm:ss format..."
- ✅ Form remains on same page (not redirect)
- ✅ Previous input values preserved

### Invalid Distance

1. Enter distance: `0` or `-5`
2. Click Save

**Expected:**
- ✅ Error message: "Distance must be greater than 0"

## 9. Check No Breaking Changes

```bash
# Run existing API tests
pytest tests/test_api.py -v
```

**Expected:**
- ✅ All existing tests still pass
- ✅ No regressions in JSON API functionality

## 10. Verify Seed Data Intact

```sql
-- In Supabase SQL Editor
SELECT type, COUNT(*) FROM activity GROUP BY type;
```

**Expected:**
- Seed data from `db/setup_and_seed.sql` is still present
- No activities were deleted during UI implementation

## Summary Checklist

- [ ] Dependencies installed (jinja2, python-multipart)
- [ ] Unit conversion tests pass (15/15)
- [ ] UI accessible at /ui
- [ ] All three forms load correctly
- [ ] Run form submits and converts units correctly
- [ ] Hangout form creates participants
- [ ] Work session form works
- [ ] Recent activities display correctly
- [ ] JSON API still works
- [ ] No breaking changes to existing tests
- [ ] Seed data intact

## Troubleshooting

**UI doesn't load:**
- Check `templates/` and `static/` directories exist
- Verify `jinja2` and `python-multipart` are installed

**Form submission fails:**
- Check DATABASE_URL is set correctly in `.env`
- Verify Supabase connection is active

**Conversion errors:**
- Run `pytest tests/test_conversions.py -v` to verify conversion logic
- Check pace format is exactly mm:ss (e.g., 8:30, not 8-30)
