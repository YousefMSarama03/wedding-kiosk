# Railway Deployment Checklist for Wedding Kiosk

## Pre-Deployment Setup

### 1. Railway Account & Project
- [ ] Create Railway account at [railway.app](https://railway.app)
- [ ] Create new Railway project
- [ ] Connect GitHub repository to Railway
- [ ] Set project name to `wedding-kiosk` or similar

### 2. Environment Secrets & Variables
Set these in Railway Environment Variables (Settings → Variables):

#### Django Core Settings
- [ ] `DJANGO_SECRET_KEY`: Generate a strong secret key (min 50 chars, use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] `DEBUG`: Set to `false`
- [ ] `ALLOWED_HOSTS`: Set to your Railway domains (e.g., `yourdomain.com,.up.railway.app`)
- [ ] `ALLOW_RAILWAY_HOSTS`: Set to `true` (auto-allows *.up.railway.app)
- [ ] `USE_X_FORWARDED_PROTO`: Set to `true` (trust Railway's X-Forwarded-Proto header)

#### Database Configuration
- [ ] `DATABASE_URL`: Will be auto-set when you add PostgreSQL plugin
- [ ] `DATABASE_SSL_REQUIRE`: Set to `true` (Railway requires SSL)
- [ ] `DATABASE_CONN_MAX_AGE`: `600` (connection pooling)

#### CORS & Frontend
- [ ] `CORS_ALLOWED_ORIGINS`: Set to your frontend domain (e.g., `https://yourdomain.com`)
- [ ] `CSRF_TRUSTED_ORIGINS`: Set to your frontend domain (e.g., `https://yourdomain.com`)
- [ ] `FRONTEND_ORIGIN`: Set to your frontend domain (used for QR URLs)
- [ ] `PUBLIC_HOST`: Set to your backend domain (for QR download URLs)
- [ ] `PUBLIC_SCHEME`: Set to `https`
- [ ] `PUBLIC_PORT`: Set to `443`

#### Redis & Celery
- [ ] `REDIS_URL`: Will be auto-set when you add Redis plugin
- [ ] `CELERY_BROKER_URL`: Can use `$REDIS_URL` reference
- [ ] `CELERY_RESULT_BACKEND`: Can use `$REDIS_URL` reference

#### AI/ML Services
- [ ] `OPENAI_API_KEY`: Get from [OpenAI API keys](https://platform.openai.com/api-keys)
- [ ] `OPENAI_IMAGE_MODEL`: `dall-e-3` (or `dall-e-2`)
- [ ] `OPENAI_IMAGE_EDIT_MODEL`: Leave empty or set to specific model
- [ ] `OPENAI_REFINE_MODEL`: `gpt-4-vision` (or appropriate model)
- [ ] `OPENAI_REFINE_SIZE`: `1536x1024`
- [ ] `REPLICATE_API_TOKEN`: Get from [Replicate API tokens](https://replicate.com/account/api-tokens) (if using Replicate models)
- [ ] `REPLICATE_MODEL`: Model ID from Replicate (e.g., `stability-ai/sdxl`)
- [ ] `REPLICATE_INSTANTID_MODEL`: InstantID model (e.g., `adirik/instantid`)
- [ ] `KEEPSAKE_USE_OPENAI_LEGACY`: Set to `false` (use latest OpenAI)

#### Optional Settings
- [ ] `KIOSK_SKIP_AUTH`: Set to `false` (enable authentication)

---

## Database & Storage

### 3. Add PostgreSQL Plugin
- [ ] In Railway dashboard, click "Add Service"
- [ ] Select "PostgreSQL" from marketplace
- [ ] Choose version `16` (matches docker-compose.yml)
- [ ] Wait for initialization (auto-creates `DATABASE_URL`)
- [ ] Verify `DATABASE_URL` appears in environment variables

### 4. Add Redis Plugin
- [ ] In Railway dashboard, click "Add Service"
- [ ] Select "Redis" from marketplace
- [ ] Choose version `7` (matches docker-compose.yml)
- [ ] Wait for initialization (auto-creates `REDIS_URL`)
- [ ] Verify `REDIS_URL` appears in environment variables

### 5. Media Storage Strategy
Choose one approach:

**Option A: Persistent Volume (Recommended for Media)**
- [ ] Add persistent volume to backend service (`/app/media`)
- [ ] Configure volume size (e.g., 5GB+)
- [ ] Note: Volumes are NOT ephemeral and persist across deployments

**Option B: External Cloud Storage (Recommended for Production Scale)**
- [ ] Set up AWS S3 bucket (or similar: GCS, Azure Blob Storage)
- [ ] Install `django-storages` and `boto3` in `requirements.txt`
- [ ] Add environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`
- [ ] Configure Django settings to use S3 backend for media

---

## Service Configuration

### 6. Backend Service Setup

#### Build Configuration
- [ ] Set build command: `./bin/start.sh` (already in Dockerfile CMD)
- [ ] Verify `Dockerfile` uses Python 3.12
- [ ] Check `requirements.txt` is present and complete
- [ ] Ensure `bin/start.sh` runs migrations and starts Gunicorn on `$PORT`

#### Deployment Configuration
- [ ] Set start command: Leave default (uses Dockerfile CMD)
- [ ] Port: Should use `$PORT` environment variable (Railway standard)
- [ ] Health check: Configure health endpoint (e.g., `/api/health/` or Django admin `/admin/`)

#### Scaling
- [ ] Set min instances: `1`
- [ ] Set max instances: `3` (adjust based on expected load)
- [ ] Enable auto-scaling if needed

### 7. Frontend Service Setup

#### Build Configuration
- [ ] Set build command: `npm install && npm run build`
- [ ] Dockerfile: Use provided `Dockerfile` (2-stage build)
- [ ] Node.js version: `20` (matches package.json)
- [ ] Verify `nginx.conf` routes API requests to backend

#### Environment Configuration
- [ ] Set `VITE_API_BASE`: Point to backend domain (e.g., `https://backend-domain.up.railway.app`)
- [ ] Check `src/config/apiBase.js` uses `VITE_API_BASE` variable

#### Deployment Configuration
- [ ] Port: `80` (nginx default)
- [ ] Health check: Configure nginx status endpoint

#### Scaling
- [ ] Set min instances: `1`
- [ ] Set max instances: `2` (static content doesn't require much scaling)

### 8. Celery Worker Service Setup

#### Create New Service
- [ ] Add another Docker service in Railway
- [ ] Point to same GitHub repo and backend `Dockerfile`
- [ ] Override start command: `celery -A app worker --loglevel=info`

#### Configuration
- [ ] CPU/Memory: 512MB RAM minimum, 1 CPU
- [ ] Instances: `1` (or more if high task volume)
- [ ] Set all same environment variables as backend service
- [ ] Disable auto-deploy or use Railway environment variable to control

---

## Pre-Deployment Checklist

### 9. Code Preparation
- [ ] All migrations are created: `python manage.py makemigrations`
- [ ] No uncomitted changes: `git status` is clean
- [ ] `.gitignore` excludes: `media/`, `.env`, `*.pyc`, `staticfiles/`, etc.
- [ ] `bin/start.sh` exists and is executable:
  ```bash
  #!/bin/bash
  set -e
  
  # Run migrations
  python manage.py migrate --noinput
  
  # Collect static files
  python manage.py collectstatic --noinput
  
  # Start Gunicorn
  exec gunicorn app.wsgi:application --bind 0.0.0.0:$PORT --workers 3
  ```

### 10. Dependencies Verification
- [ ] Check `requirements.txt` includes:
  - `Django>=5.0`
  - `psycopg[binary]>=3.1` (PostgreSQL)
  - `dj-database-url>=2.2` (DATABASE_URL support)
  - `gunicorn>=22.0`
  - `whitenoise>=6.6` (static files)
  - `celery[redis]>=5.3` (background tasks)
  - `openai>=1.0`
  - `replicate>=0.25` (if using)
  - `rembg>=2.0` (background removal)
  - `django-cors-headers>=4.3`

- [ ] Check `frontend/package.json` includes:
  - Vite build target
  - API base URL configuration

### 11. Configuration Files
- [ ] `app/settings.py` supports all Railway environment variables
- [ ] `bin/start.sh` is in repository and executable
- [ ] `Dockerfile` (backend) runs `bin/start.sh`
- [ ] `frontend/Dockerfile` (2-stage nginx build) is present
- [ ] `frontend/nginx.conf` is configured correctly

---

## Initial Deployment

### 12. Deploy Backend & Database
- [ ] Commit all code: `git push`
- [ ] Wait for Railway build to complete
- [ ] Check build logs in Railway dashboard for errors
- [ ] Verify backend service is running (check "Logs" tab)
- [ ] Check database migrations ran: Look for "Migrated" in logs

### 13. Deploy Frontend
- [ ] Frontend build should trigger automatically on push
- [ ] Wait for npm build to complete
- [ ] Check frontend logs for build errors
- [ ] Verify nginx is serving app on Railway domain

### 14. Deploy Celery Worker
- [ ] Worker deployment should trigger automatically
- [ ] Check worker logs: Should show "celery worker ready"
- [ ] Verify background tasks can queue (check Redis connection in logs)

### 15. Verify Deployment
- [ ] Visit frontend URL in browser
- [ ] Check Network tab: API calls should go to correct backend domain
- [ ] Test CORS: Verify no CORS errors in browser console
- [ ] Test API endpoint (e.g., GET `/api/events/`)
- [ ] Check Django admin at `/admin/`
- [ ] Verify static files load (CSS, JS, images)
- [ ] Check media files load if any exist

---

## Post-Deployment Validation

### 16. Health Checks
- [ ] Database connection verified in logs
- [ ] Redis connection verified in logs
- [ ] OpenAI/Replicate API keys validated (if used)
- [ ] Static files served correctly (WhiteNoise working)
- [ ] CORS headers present in API responses

### 17. Test Core Features
- [ ] Kiosk pages load without errors
- [ ] Photo upload functionality works
- [ ] Background job tasks queue and execute
- [ ] AI photo processing works (if enabled)
- [ ] QR code generation works
- [ ] Admin panel accessible

### 18. Monitoring Setup
- [ ] Enable Railway metrics monitoring
- [ ] Set up log aggregation/search
- [ ] Configure alerting for:
  - High memory usage (>500MB)
  - High CPU usage (>80%)
  - Service crashes/restarts
  - Failed background tasks (check Celery logs)

### 19. Set Custom Domain (Optional)
- [ ] Configure custom domain in Railway settings
- [ ] Add DNS records (CNAME or A record per Railway instructions)
- [ ] Wait for SSL certificate generation (auto via Let's Encrypt)
- [ ] Verify HTTPS works at custom domain

---

## Common Issues & Troubleshooting

### Issue: Database migrations fail
**Solution:**
- [ ] Check `DATABASE_URL` is set correctly
- [ ] Verify PostgreSQL plugin is initialized
- [ ] Check backend logs for specific migration error
- [ ] Run `python manage.py migrate --plan` locally to verify migrations

### Issue: CORS errors in browser console
**Solution:**
- [ ] Verify `CORS_ALLOWED_ORIGINS` includes frontend domain
- [ ] Verify `CSRF_TRUSTED_ORIGINS` includes frontend domain
- [ ] Check `FRONTEND_ORIGIN` is set if using dynamic routing
- [ ] Restart backend service after env var changes

### Issue: Static files 404 errors
**Solution:**
- [ ] Verify `python manage.py collectstatic` ran in `bin/start.sh`
- [ ] Check `STATIC_ROOT` is correct path
- [ ] Verify WhiteNoise middleware is in `MIDDLEWARE`
- [ ] Check backend logs for collectstatic output

### Issue: Background tasks not processing
**Solution:**
- [ ] Verify `REDIS_URL` is set and accessible
- [ ] Check Celery worker logs for connection errors
- [ ] Verify Celery worker service is running (1 instance)
- [ ] Check `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are set

### Issue: OpenAI/Replicate API calls fail
**Solution:**
- [ ] Verify API keys are set in environment variables
- [ ] Check API key is valid and has correct permissions
- [ ] Check rate limits haven't been exceeded
- [ ] Verify model names are correct (e.g., `dall-e-3` not `dall-e-2`)

### Issue: Memory/CPU spikes
**Solution:**
- [ ] Check background task queue (might be backed up)
- [ ] Increase Gunicorn workers in `bin/start.sh` carefully
- [ ] Monitor with Railway metrics dashboard
- [ ] Check for memory leaks in code

### Issue: Deployments slow or timing out
**Solution:**
- [ ] Check npm install/build time (could be slow)
- [ ] Consider using binary builds to cache dependencies
- [ ] Check internet speed for downloading u2net model (~176MB)
- [ ] Verify Dockerfile layers are optimized

---

## Performance Optimization

### 20. Backend Optimization
- [ ] Increase Gunicorn workers to 3-4 in `bin/start.sh`
- [ ] Enable database connection pooling (already set)
- [ ] Configure Redis cache if needed
- [ ] Set up CDN for static files (optional)
- [ ] Monitor slow database queries

### 21. Frontend Optimization
- [ ] Enable gzip compression in nginx
- [ ] Configure browser caching headers
- [ ] Optimize Vite build output
- [ ] Check asset sizes don't exceed browser limits

### 22. Celery Optimization
- [ ] Monitor task execution times
- [ ] Optimize task queue settings
- [ ] Consider multiple Celery workers if high volume
- [ ] Set task timeouts to prevent hung tasks

---

## Maintenance Checklist

### 23. Regular Maintenance
- [ ] Check logs weekly for errors or warnings
- [ ] Monitor API response times and errors
- [ ] Check background task success rate
- [ ] Monitor database storage growth
- [ ] Update Django security patches when available
- [ ] Review Railway metrics dashboard monthly

### 24. Backup & Recovery
- [ ] Enable PostgreSQL backups in Railway (if available)
- [ ] Implement media file backups (if using persistent volume)
- [ ] Document recovery procedures
- [ ] Test recovery procedure quarterly

### 25. Rollback Plan
- [ ] Keep previous deployment git commits accessible
- [ ] Document environment variable snapshots
- [ ] Have process to quickly revert to previous version
- [ ] Test rollback procedure before major deployments

---

## Final Sign-Off

- [ ] All environment variables configured
- [ ] All services deployed and running
- [ ] Core features tested and working
- [ ] Monitoring and alerts configured
- [ ] Team trained on managing Railway deployment
- [ ] Deployment documentation updated
- [ ] Performance baselines recorded

**Deployed by:** _________________
**Date:** _________________
**Version/Commit:** _________________
