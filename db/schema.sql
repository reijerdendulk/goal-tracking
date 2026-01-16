-- Goal Tracking Database Schema
-- Compatible with PostgreSQL / Supabase

-- =========================
-- Extensions
-- =========================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================
-- Enums
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
-- Base activity table
-- =========================
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

-- Helpful indexes for weekly rollups and filtering
CREATE INDEX IF NOT EXISTS idx_activity_type_start_at ON activity (type, start_at);
CREATE INDEX IF NOT EXISTS idx_activity_start_at ON activity (start_at);

-- =========================
-- Run details (1:1 with activity where type='run')
-- =========================
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

-- =========================
-- Hangout details (1:1 with activity where type='hangout')
-- =========================
CREATE TABLE IF NOT EXISTS hangout_detail (
  activity_id    uuid PRIMARY KEY REFERENCES activity(id) ON DELETE CASCADE,
  location_name  text,
  location_type  text,
  cost_estimate  numeric(10,2),
  mood           integer CHECK (mood BETWEEN 1 AND 5)
);

-- =========================
-- People + participants (many:many)
-- =========================
CREATE TABLE IF NOT EXISTS person (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL,
  handle      text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- A person can be attached to any activity, but hangouts will use it most.
CREATE TABLE IF NOT EXISTS activity_participant (
  activity_id  uuid NOT NULL REFERENCES activity(id) ON DELETE CASCADE,
  person_id    uuid NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  role         text,
  PRIMARY KEY (activity_id, person_id)
);

CREATE INDEX IF NOT EXISTS idx_activity_participant_person_activity ON activity_participant (person_id, activity_id);

-- =========================
-- Work details (1:1 with activity where type='work')
-- =========================
CREATE TABLE IF NOT EXISTS work_detail (
  activity_id    uuid PRIMARY KEY REFERENCES activity(id) ON DELETE CASCADE,
  project        text NOT NULL,
  area           text,
  status         work_status NOT NULL DEFAULT 'in_progress',
  artifact_link  text
);

CREATE INDEX IF NOT EXISTS idx_work_detail_project ON work_detail (project);
