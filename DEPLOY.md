# Deploying to Railway with Supabase Postgres

This guide explains how to deploy the Goal Tracking API to Railway using Supabase as the database.

## Prerequisites

- A [Railway](https://railway.app) account
- A [Supabase](https://supabase.com) project with Postgres database
- Git repository with your code

## Step 1: Get Your Supabase Connection String

1. Go to your Supabase project dashboard
2. Navigate to **Settings** > **Database**
3. Find the **Connection string** section
4. Copy the **URI** (direct connection)

Example:
```
postgresql://postgres:reijergoaltracking@db.slofiyeatobqlamwinrk.supabase.co:5432/postgres
```

> **Note**: Use the direct connection string, not the pooler connection, for migrations and general use.

## Step 2: Create Railway Project

1. Log in to [Railway](https://railway.app)
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Connect your GitHub account and select this repository

## Step 3: Configure Environment Variables

In your Railway project:

1. Go to your service settings
2. Click **Variables**
3. Add the following environment variables:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Supabase connection string |
| `APP_ENV` | `production` |
| `LOG_LEVEL` | `info` |

> **Important**: Railway automatically sets the `PORT` variable. Do not set it manually.

## Step 4: Configure the Start Command

Railway should automatically detect the Dockerfile or use the following start command.

If using **Nixpacks** (Railway's default builder), create a `railway.json`:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Or if using Docker, Railway will use the Dockerfile automatically.

## Step 5: Run Database Migrations

### Option A: Railway Release Command (Recommended)

Add a release command that runs before deployment:

1. In your `railway.json`, add:
```json
{
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "releaseCommand": "alembic upgrade head"
  }
}
```

### Option B: Manual Migration

Run migrations manually using Railway CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run migrations
railway run alembic upgrade head
```

### Option C: Run SQL Directly on Supabase

1. Go to Supabase SQL Editor
2. Copy contents of `db/schema.sql`
3. Execute the SQL

## Step 6: Deploy

Push to your main branch to trigger deployment:

```bash
git push origin main
```

Railway will:
1. Build your application
2. Run the release command (migrations)
3. Start the server

## Step 7: Verify Deployment

1. Get your Railway URL from the project dashboard
2. Test the health endpoint:

```bash
curl https://your-app.railway.app/health
# Should return: {"ok":true,"db":"ok"}
```

3. View API docs at `https://your-app.railway.app/docs`

## Troubleshooting

### Connection Errors

If you see database connection errors:

1. Verify `DATABASE_URL` is correct
2. Check Supabase is not in "Paused" state
3. Ensure your IP is not blocked (Supabase > Settings > Database > Network)

### Migration Errors

If migrations fail:

1. Check Railway logs for error details
2. Verify database credentials are correct
3. Try running migrations manually:
   ```bash
   railway run alembic upgrade head
   ```

### "Address already in use" Error

Ensure you're using `$PORT` (not a hardcoded port):
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Production Checklist

- [ ] `DATABASE_URL` set to Supabase connection string
- [ ] `APP_ENV` set to `production`
- [ ] Migrations have been run
- [ ] Health check returns `{"ok": true, "db": "ok"}`
- [ ] API docs accessible at `/docs`

## Scaling

Railway automatically handles scaling. For high traffic:

1. Consider using Supabase connection pooling (PgBouncer)
2. Update `DATABASE_URL` to use the pooler connection string
3. Adjust pool settings in `app/db.py` if needed

## Monitoring

- **Railway**: View logs and metrics in the Railway dashboard
- **Supabase**: Monitor database metrics in Supabase dashboard
- **Health endpoint**: Set up external monitoring on `/health`
