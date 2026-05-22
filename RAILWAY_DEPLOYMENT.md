# Railway Production Deployment Guide

This document describes the production deployment configuration for the Wedding Kiosk application on Railway.

## Architecture

The application is deployed as 5 independent services on Railway:

1. **PostgreSQL** - Database (Railway template)
2. **Redis** - Cache & message broker (Railway template)
3. **Backend** - Django API (Gunicorn + 4 workers)
4. **Celery Worker** - Async task processor
5. **Frontend** - React + Vite (served via `serve`)

## Service Configuration

### PostgreSQL
- **Image**: postgres:16-alpine
- **Volume**: Persistent storage at `/var/lib/postgresql/data`
- **Health Check**: `pg_isready` every 5 seconds
- **Auto-generated Variables**:
  - `DATABASE_URL` - Full connection string
  - `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`

### Redis
- **Image**: redis:7-alpine
- **Health Check**: `redis-cli ping` every 5 seconds
- **Auto-generated Variables**:
  - `REDIS_URL` - Full connection string
  - `REDISHOST`, `REDISPORT`, `REDISUSER`, `REDISPASSWORD`

### Backend (Django)
- **Build**: `backend/Dockerfile`
- **Start Command**: `python manage.py migrate --noinput && gunicorn app.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120`
- **Health Check**: GET `/api/health/` (returns 200 OK)
- **Public Domain**: Yes (HTTPS)
- **Key Environment Variables**:
  - `DEBUG=false` - Production mode
  - `DJANGO_SECRET_KEY` - Generated secret (Railway)
  - `DATABASE_URL` - From Postgres service
  - `REDIS_URL` - From Redis service
  - `CELERY_BROKER_URL` - Points to Redis
  - `ALLOWED_HOSTS` - Backend domain + localhost
  - `CORS_ALLOWED_ORIGINS` - Frontend domain (HTTPS)
  - `CSRF_TRUSTED_ORIGINS` - Frontend domain (HTTPS)
  - `SECURE_SSL_REDIRECT=true` - Force HTTPS
  - `SESSION_COOKIE_SECURE=true` - Secure cookies
  - `CSRF_COOKIE_SECURE=true` - Secure CSRF cookies
  - `SECURE_HSTS_SECONDS=31536000` - 1-year HSTS
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS=true`
  - `SECURE_HSTS_PRELOAD=true`

### Celery Worker
- **Build**: `backend/Dockerfile` (same as backend)
- **Start Command**: `celery -A app worker -l info --concurrency=2`
- **No Public Domain** - Internal only
- **Key Environment Variables**:
  - Same as backend (except no public domain vars)
  - `NUMBA_DISABLE_CACHING=1` - Disable numba caching
  - `NUMBA_DISABLE_JIT=1` - Disable JIT compilation

### Frontend (React + Vite)
- **Build**: `frontend/Dockerfile` (multi-stage build)
- **Start Command**: `serve -s dist -l 3000`
- **Health Check**: GET `/` (returns 200 OK)
- **Public Domain**: Yes (HTTPS)
- **Key Environment Variables**:
  - `VITE_API_URL` - Backend domain (HTTPS)
  - `PORT=3000` - Listen port

## Environment Variables

### Service References
Railway automatically injects variables from other services using the syntax `${{ServiceName.VARIABLE_NAME}}`:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CORS_ALLOWED_ORIGINS=https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}
VITE_API_URL=https://${{backend.RAILWAY_PUBLIC_DOMAIN}}
```

### Generated Secrets
Railway generates secure values for:
- `DJANGO_SECRET_KEY` - 50-character random string

### Manual Configuration
Set these in the Railway dashboard:
- `OPENAI_API_KEY` - For AI image generation
- `REPLICATE_API_TOKEN` - For Replicate models
- Any other API keys or secrets

## Security Features

### HTTPS & SSL/TLS
- All services use HTTPS via Railway's managed certificates
- `SECURE_PROXY_SSL_HEADER` configured for Railway's proxy
- `SECURE_SSL_REDIRECT=true` forces HTTP → HTTPS

### Secure Cookies
- `SESSION_COOKIE_SECURE=true` - Only sent over HTTPS
- `CSRF_COOKIE_SECURE=true` - CSRF token only over HTTPS
- `SECURE_BROWSER_XSS_FILTER=true` - XSS protection header
- `SECURE_CONTENT_TYPE_NOSNIFF=true` - MIME type sniffing protection

### HSTS (HTTP Strict Transport Security)
- `SECURE_HSTS_SECONDS=31536000` - 1 year
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=true`
- `SECURE_HSTS_PRELOAD=true` - Preload list eligible

### CORS & CSRF
- `CORS_ALLOWED_ORIGINS` - Only frontend domain
- `CSRF_TRUSTED_ORIGINS` - Only frontend domain
- `CORS_ALLOW_CREDENTIALS=true` - Allow cookies in CORS requests

## Database Migrations

Migrations run automatically on backend startup:
```bash
python manage.py migrate --noinput
```

This happens before Gunicorn starts, ensuring the database schema is up-to-date.

## Static Files

Static files are served by Django in production:
- `STATIC_ROOT=/app/staticfiles`
- `STATIC_URL=/static/`
- Created during Docker build

## Media Files

Media files (uploaded photos) are stored in:
- `MEDIA_ROOT=/app/media`
- `MEDIA_URL=/media/`
- Directory created with proper permissions during Docker build

## Celery Task Queue

Celery uses Redis as both broker and result backend:
- **Broker**: `redis://...` (from REDIS_URL)
- **Result Backend**: `redis://...` (from REDIS_URL)
- **Concurrency**: 2 workers (configurable)
- **Task Timeout**: 900 seconds (15 minutes)
- **Soft Timeout**: 840 seconds (14 minutes)

## Health Checks

Railway monitors service health via:

1. **Backend**: GET `/api/health/` → `{"status": "ok", "service": "backend"}`
2. **Frontend**: GET `/` → HTML response (200 OK)
3. **PostgreSQL**: `pg_isready -U postgres`
4. **Redis**: `redis-cli ping`

If a health check fails, Railway will restart the service.

## Deployment Steps

1. **Create Services** (one-time):
   ```bash
   # Railway UI or CLI
   railway service create postgres
   railway service create redis
   railway service create backend
   railway service create celery-worker
   railway service create frontend
   ```

2. **Configure Environment Variables**:
   - Railway auto-generates `DATABASE_URL`, `REDIS_URL`
   - Set `OPENAI_API_KEY`, `REPLICATE_API_TOKEN` in dashboard
   - Other vars are set via service references

3. **Deploy**:
   ```bash
   git push origin main
   # Railway auto-deploys on push
   ```

4. **Monitor**:
   - Check deployment logs in Railway dashboard
   - Verify health checks pass
   - Test API endpoints

## Troubleshooting

### Backend won't start
- Check logs: `railway logs backend`
- Verify `DATABASE_URL` is set
- Ensure migrations pass: `python manage.py migrate --noinput`
- Check `ALLOWED_HOSTS` includes your domain

### CORS errors
- Verify `CORS_ALLOWED_ORIGINS` includes frontend domain
- Check frontend is using HTTPS
- Ensure `CORS_ALLOW_CREDENTIALS=true`

### Celery tasks not running
- Check Redis connection: `redis-cli ping`
- Verify `CELERY_BROKER_URL` is set
- Check celery-worker logs: `railway logs celery-worker`

### Frontend can't reach backend
- Verify `VITE_API_URL` is set to backend domain
- Check CORS headers in backend response
- Ensure backend is publicly accessible

### Database connection issues
- Verify `DATABASE_URL` format
- Check PostgreSQL service is healthy
- Ensure migrations have run

## Scaling

### Horizontal Scaling
- Increase backend replicas in Railway dashboard
- Celery workers scale independently
- Frontend can be scaled (stateless)

### Vertical Scaling
- Increase CPU/RAM per service in Railway dashboard
- Database may need more resources for large datasets

## Monitoring

Monitor these metrics in Railway dashboard:
- **CPU Usage** - Should be < 80% under normal load
- **Memory Usage** - Should be < 80% of limit
- **Network I/O** - Monitor for unusual traffic
- **Deployment Status** - Check for failed restarts

## Backups

PostgreSQL backups are handled by Railway:
- Daily automated backups
- 7-day retention
- Restore via Railway dashboard

## Updates

To update the application:
1. Push changes to `main` branch
2. Railway auto-deploys
3. Migrations run automatically
4. Services restart with new code

## Rollback

To rollback to a previous version:
1. Go to Railway dashboard
2. Select the service
3. Choose a previous deployment
4. Click "Redeploy"

## Support

For issues:
1. Check Railway documentation: https://docs.railway.app
2. Review service logs in dashboard
3. Check health check endpoints
4. Verify environment variables are set correctly
