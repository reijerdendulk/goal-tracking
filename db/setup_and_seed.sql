-- Goal Tracking Database Setup & Seed Data
-- Run this in Supabase SQL Editor (https://supabase.com/dashboard -> SQL Editor)

-- =========================
-- STEP 1: Extensions
-- =========================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================
-- STEP 2: Enums
-- =========================
DO $$ BEGIN
  CREATE TYPE activity_type AS ENUM ('run', 'hangout', 'work');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE run_workout_type AS ENUM ('easy','tempo','intervals','long','race','recovery');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE work_status AS ENUM ('idea','todo','in_progress','blocked','done');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

-- =========================
-- STEP 3: Tables
-- =========================

-- Base activity table
CREATE TABLE IF NOT EXISTS activity (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type          activity_type NOT NULL,
  title         text NOT NULL,
  notes         text,
  start_at      timestamptz NOT NULL,
  end_at        timestamptz,
  duration_min  integer,
  tags          jsonb,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_activity_type_start_at ON activity (type, start_at);
CREATE INDEX IF NOT EXISTS idx_activity_start_at ON activity (start_at);

-- Run details
CREATE TABLE IF NOT EXISTS run_detail (
  activity_id          uuid PRIMARY KEY REFERENCES activity(id) ON DELETE CASCADE,
  distance_meters      integer NOT NULL CHECK (distance_meters > 0),
  moving_time_sec      integer,
  avg_pace_sec_per_km  integer,
  elevation_gain_m     integer,
  rpe                  integer CHECK (rpe BETWEEN 1 AND 10),
  workout_type         run_workout_type NOT NULL,
  surface              text,
  shoe                 text,
  splits               jsonb
);

CREATE INDEX IF NOT EXISTS idx_run_detail_workout_type ON run_detail (workout_type);
CREATE INDEX IF NOT EXISTS idx_run_detail_distance_meters ON run_detail (distance_meters);

-- Hangout details
CREATE TABLE IF NOT EXISTS hangout_detail (
  activity_id    uuid PRIMARY KEY REFERENCES activity(id) ON DELETE CASCADE,
  location_name  text,
  location_type  text,
  cost_estimate  numeric(10,2),
  mood           integer CHECK (mood BETWEEN 1 AND 5)
);

-- People
CREATE TABLE IF NOT EXISTS person (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL,
  handle      text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- Activity participants (many-to-many)
CREATE TABLE IF NOT EXISTS activity_participant (
  activity_id  uuid NOT NULL REFERENCES activity(id) ON DELETE CASCADE,
  person_id    uuid NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  role         text,
  PRIMARY KEY (activity_id, person_id)
);

CREATE INDEX IF NOT EXISTS idx_activity_participant_person_activity ON activity_participant (person_id, activity_id);

-- Work details
CREATE TABLE IF NOT EXISTS work_detail (
  activity_id    uuid PRIMARY KEY REFERENCES activity(id) ON DELETE CASCADE,
  project        text NOT NULL,
  area           text,
  status         work_status NOT NULL DEFAULT 'in_progress',
  artifact_link  text
);

CREATE INDEX IF NOT EXISTS idx_work_detail_project ON work_detail (project);

-- =========================
-- STEP 4: Seed Data
-- =========================

-- Create some people for hangouts
INSERT INTO person (id, name, handle) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Alex', '@alex'),
  ('22222222-2222-2222-2222-222222222222', 'Jordan', '@jordan'),
  ('33333333-3333-3333-3333-333333333333', 'Sam', '@sam'),
  ('44444444-4444-4444-4444-444444444444', 'Casey', '@casey')
ON CONFLICT (id) DO NOTHING;

-- =========================
-- Seed Runs (past 2 weeks)
-- =========================

-- Run 1: Easy morning run (today - 1 day)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'run',
    'Morning Easy Run',
    'Felt good, nice weather',
    NOW() - INTERVAL '1 day' + TIME '07:00',
    NOW() - INTERVAL '1 day' + TIME '07:45',
    45,
    '["morning", "easy"]'::jsonb
  )
  RETURNING id
)
INSERT INTO run_detail (activity_id, distance_meters, moving_time_sec, avg_pace_sec_per_km, elevation_gain_m, rpe, workout_type, surface, shoe)
SELECT id, 8000, 2700, 338, 50, 4, 'easy', 'road', 'Nike Pegasus'
FROM new_activity;

-- Run 2: Tempo run (today - 3 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'run',
    'Tempo Thursday',
    'Hard but manageable pace',
    NOW() - INTERVAL '3 days' + TIME '18:00',
    NOW() - INTERVAL '3 days' + TIME '18:50',
    50,
    '["evening", "tempo", "workout"]'::jsonb
  )
  RETURNING id
)
INSERT INTO run_detail (activity_id, distance_meters, moving_time_sec, avg_pace_sec_per_km, elevation_gain_m, rpe, workout_type, surface, shoe)
SELECT id, 10000, 3000, 300, 30, 7, 'tempo', 'road', 'Nike Vaporfly'
FROM new_activity;

-- Run 3: Long run (today - 5 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'run',
    'Sunday Long Run',
    'Great long run through the park. Legs felt strong.',
    NOW() - INTERVAL '5 days' + TIME '08:00',
    NOW() - INTERVAL '5 days' + TIME '10:00',
    120,
    '["weekend", "long", "park"]'::jsonb
  )
  RETURNING id
)
INSERT INTO run_detail (activity_id, distance_meters, moving_time_sec, avg_pace_sec_per_km, elevation_gain_m, rpe, workout_type, surface, shoe)
SELECT id, 21000, 7200, 343, 150, 6, 'long', 'trail', 'ASICS Gel-Nimbus'
FROM new_activity;

-- Run 4: Recovery run (today - 7 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'run',
    'Recovery Jog',
    'Easy shakeout after long run',
    NOW() - INTERVAL '7 days' + TIME '07:30',
    NOW() - INTERVAL '7 days' + TIME '08:00',
    30,
    '["recovery", "easy"]'::jsonb
  )
  RETURNING id
)
INSERT INTO run_detail (activity_id, distance_meters, moving_time_sec, avg_pace_sec_per_km, elevation_gain_m, rpe, workout_type, surface, shoe)
SELECT id, 5000, 1800, 360, 20, 2, 'recovery', 'road', 'Nike Pegasus'
FROM new_activity;

-- Run 5: Interval session (today - 10 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'run',
    'Track Intervals',
    '8x400m with 200m recovery. Hit target paces!',
    NOW() - INTERVAL '10 days' + TIME '17:30',
    NOW() - INTERVAL '10 days' + TIME '18:30',
    60,
    '["track", "intervals", "speed"]'::jsonb
  )
  RETURNING id
)
INSERT INTO run_detail (activity_id, distance_meters, moving_time_sec, avg_pace_sec_per_km, elevation_gain_m, rpe, workout_type, surface, shoe, splits)
SELECT id, 7000, 2400, 343, 5, 8, 'intervals', 'track', 'Nike Vaporfly',
  '[{"km": 1, "time_sec": 90}, {"km": 2, "time_sec": 88}, {"km": 3, "time_sec": 89}]'::jsonb
FROM new_activity;

-- =========================
-- Seed Hangouts
-- =========================

-- Hangout 1: Coffee with Alex (today - 2 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'hangout',
    'Coffee catch-up with Alex',
    'Great conversation about travel plans',
    NOW() - INTERVAL '2 days' + TIME '10:00',
    NOW() - INTERVAL '2 days' + TIME '11:30',
    90,
    '["coffee", "catchup"]'::jsonb
  )
  RETURNING id
)
INSERT INTO hangout_detail (activity_id, location_name, location_type, cost_estimate, mood)
SELECT id, 'Blue Bottle Coffee', 'cafe', 12.50, 5
FROM new_activity;

-- Add participant to the hangout
INSERT INTO activity_participant (activity_id, person_id, role)
SELECT a.id, '11111111-1111-1111-1111-111111111111', 'friend'
FROM activity a WHERE a.title = 'Coffee catch-up with Alex' AND a.type = 'hangout';

-- Hangout 2: Dinner with friends (today - 4 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'hangout',
    'Friday dinner with the crew',
    'Amazing sushi and good vibes',
    NOW() - INTERVAL '4 days' + TIME '19:00',
    NOW() - INTERVAL '4 days' + TIME '22:00',
    180,
    '["dinner", "friends", "weekend"]'::jsonb
  )
  RETURNING id
)
INSERT INTO hangout_detail (activity_id, location_name, location_type, cost_estimate, mood)
SELECT id, 'Sushi Palace', 'restaurant', 65.00, 5
FROM new_activity;

-- Add participants
INSERT INTO activity_participant (activity_id, person_id, role)
SELECT a.id, '22222222-2222-2222-2222-222222222222', 'friend'
FROM activity a WHERE a.title = 'Friday dinner with the crew' AND a.type = 'hangout';

INSERT INTO activity_participant (activity_id, person_id, role)
SELECT a.id, '33333333-3333-3333-3333-333333333333', 'friend'
FROM activity a WHERE a.title = 'Friday dinner with the crew' AND a.type = 'hangout';

-- Hangout 3: Movie night (today - 8 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'hangout',
    'Movie night at home',
    'Watched Dune Part 2, incredible visuals',
    NOW() - INTERVAL '8 days' + TIME '20:00',
    NOW() - INTERVAL '8 days' + TIME '23:00',
    180,
    '["movie", "home"]'::jsonb
  )
  RETURNING id
)
INSERT INTO hangout_detail (activity_id, location_name, location_type, cost_estimate, mood)
SELECT id, 'Home', 'home', 0.00, 4
FROM new_activity;

INSERT INTO activity_participant (activity_id, person_id, role)
SELECT a.id, '44444444-4444-4444-4444-444444444444', 'friend'
FROM activity a WHERE a.title = 'Movie night at home' AND a.type = 'hangout';

-- =========================
-- Seed Work Sessions
-- =========================

-- Work 1: Goal tracking API (today)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'work',
    'Build Goal Tracking API endpoints',
    'Implemented CRUD for runs and hangouts',
    NOW() - INTERVAL '4 hours',
    NOW() - INTERVAL '1 hour',
    180,
    '["coding", "api", "python"]'::jsonb
  )
  RETURNING id
)
INSERT INTO work_detail (activity_id, project, area, status, artifact_link)
SELECT id, 'Goal Tracking App', 'backend', 'in_progress', 'https://github.com/user/goal-tracking'
FROM new_activity;

-- Work 2: Frontend design (today - 2 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'work',
    'Design dashboard mockups',
    'Created wireframes for activity dashboard',
    NOW() - INTERVAL '2 days' + TIME '14:00',
    NOW() - INTERVAL '2 days' + TIME '16:30',
    150,
    '["design", "figma", "ui"]'::jsonb
  )
  RETURNING id
)
INSERT INTO work_detail (activity_id, project, area, status, artifact_link)
SELECT id, 'Goal Tracking App', 'frontend', 'done', 'https://figma.com/file/xyz'
FROM new_activity;

-- Work 3: Database schema (today - 6 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'work',
    'Design database schema',
    'Created normalized schema for activities',
    NOW() - INTERVAL '6 days' + TIME '10:00',
    NOW() - INTERVAL '6 days' + TIME '13:00',
    180,
    '["database", "postgres", "schema"]'::jsonb
  )
  RETURNING id
)
INSERT INTO work_detail (activity_id, project, area, status, artifact_link)
SELECT id, 'Goal Tracking App', 'database', 'done', NULL
FROM new_activity;

-- Work 4: Blog post writing (today - 9 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'work',
    'Write blog post on FastAPI',
    'Draft about building APIs with FastAPI',
    NOW() - INTERVAL '9 days' + TIME '09:00',
    NOW() - INTERVAL '9 days' + TIME '11:00',
    120,
    '["writing", "blog", "fastapi"]'::jsonb
  )
  RETURNING id
)
INSERT INTO work_detail (activity_id, project, area, status, artifact_link)
SELECT id, 'Personal Blog', 'content', 'in_progress', NULL
FROM new_activity;

-- Work 5: Code review (today - 11 days)
WITH new_activity AS (
  INSERT INTO activity (type, title, notes, start_at, end_at, duration_min, tags)
  VALUES (
    'work',
    'Review PR for auth module',
    'Reviewed authentication implementation',
    NOW() - INTERVAL '11 days' + TIME '15:00',
    NOW() - INTERVAL '11 days' + TIME '16:00',
    60,
    '["review", "auth"]'::jsonb
  )
  RETURNING id
)
INSERT INTO work_detail (activity_id, project, area, status, artifact_link)
SELECT id, 'Work Project', 'backend', 'done', 'https://github.com/company/project/pull/123'
FROM new_activity;

-- =========================
-- Verification Queries (optional - uncomment to check data)
-- =========================

-- SELECT 'Activities' as table_name, COUNT(*) as count FROM activity
-- UNION ALL SELECT 'Runs', COUNT(*) FROM run_detail
-- UNION ALL SELECT 'Hangouts', COUNT(*) FROM hangout_detail
-- UNION ALL SELECT 'Work Sessions', COUNT(*) FROM work_detail
-- UNION ALL SELECT 'People', COUNT(*) FROM person
-- UNION ALL SELECT 'Participants', COUNT(*) FROM activity_participant;
