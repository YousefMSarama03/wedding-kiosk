# AI Wedding Photo Kiosk

Guests take photos at the kiosk; the backend runs a keepsake pipeline (background removal, bride reference prep, then **Replicate InstantID** face-preserving generation). Optional **OpenAI** DALL-E legacy mode exists for emergencies. Guests scan a QR code to download the result.

## Requirements

- Docker and Docker Compose (to run with containers)
- Or: Python 3.12+, PostgreSQL (to run locally)

## Run with Docker

1. Copy or create a `.env` file in the project root with at least:

   ```bash
   POSTGRES_DB=wedding_kiosk
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   # AI: Replicate (required for default kiosk generation)
   REPLICATE_API_TOKEN=your-replicate-token
   # Optional: pin another InstantID-compatible model version (default: zsxkib/instant-id)
   # REPLICATE_INSTANTID_MODEL=lucataco/instantid:...
   # OPENAI_API_KEY=sk-...   # only if KEEPSAKE_USE_OPENAI_LEGACY=true
   # Optional: so phones can open QR download links (use your machine's LAN IP)
   PUBLIC_HOST=192.168.31.66
   PUBLIC_SCHEME=http
   PUBLIC_PORT=8000
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://192.168.31.66:3000
   CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.31.66:3000
   ```

2. From the project root:

   ```bash
   docker-compose up --build
   ```

3. Frontend (kiosk UI): http://localhost:3000  
   Backend API: http://localhost:8000  
   Admin: http://localhost:8000/admin/

4. Migrations run automatically on backend start. Create a superuser if needed:

   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

## Run locally (without Docker)

1. Create a virtual environment and install dependencies:

   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Ensure PostgreSQL is running and create a database (e.g. `wedding_kiosk`).

3. Set `backend/.env` or environment variables: `POSTGRES_HOST=localhost`, `REPLICATE_API_TOKEN`, and optionally `OPENAI_API_KEY` + `KEEPSAKE_USE_OPENAI_LEGACY=true` for the legacy path, plus `PUBLIC_HOST` for QR reachability.

4. Run migrations and start the server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Project structure

```
ai-wedding-kiosk/
├── backend/              # Django + DRF API (events, photos, AI, QR, download)
│   ├── app/
│   ├── events/
│   ├── photos/
│   ├── Dockerfile
│   ├── manage.py
│   └── requirements.txt
├── frontend/             # Vite + React + Tailwind (kiosk + admin UI)
│   ├── src/
│   ├── Dockerfile        # build + nginx (proxies /api, /media to backend)
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml    # db, backend, frontend
├── .env
└── README.md
```

## Production

Before a real deployment, set these in your environment (do **not** commit secrets):

| Variable | Purpose |
|----------|---------|
| `DEBUG` | Set to `false`. |
| `DJANGO_SECRET_KEY` | Generate a new one, e.g. `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`. |
| `ALLOWED_HOSTS` | Comma-separated hostnames and IPs that will serve the app (e.g. `kiosk.mywedding.com,192.168.31.66`). |
| `CORS_ALLOWED_ORIGINS` | Exact frontend origin(s), e.g. `https://kiosk.mywedding.com`. |
| `CSRF_TRUSTED_ORIGINS` | Same origin(s) as above, e.g. `https://kiosk.mywedding.com`. |
| `PUBLIC_HOST` | Hostname or IP used in QR download URLs so phones can reach the backend. |
| `PUBLIC_SCHEME` | `https` if the site is served over HTTPS. |
| `PUBLIC_PORT` | Leave empty for default 80/443, or set the port (e.g. `8000`) if different. |
| `REPLICATE_API_TOKEN` | Required for default generation (InstantID on Replicate). |
| `REPLICATE_INSTANTID_MODEL` | Optional; defaults to a pinned `zsxkib/instant-id` version. Other models may need code/schema tweaks. |
| `OPENAI_API_KEY` | Only if `KEEPSAKE_USE_OPENAI_LEGACY=true` (DALL-E guest-only path). |
| `KEEPSAKE_USE_OPENAI_LEGACY` | `true` to skip Replicate and use legacy OpenAI generation. |

Serve the app behind a reverse proxy (e.g. Caddy or Nginx) with HTTPS. Point the proxy at the backend and (if applicable) at the frontend build; set `PUBLIC_SCHEME=https` and the correct `PUBLIC_HOST` so QR codes use `https://...` and phones can download securely.

### Deploy on a Linux server (Docker Compose)

1. **Server**: Install [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose plugin](https://docs.docker.com/compose/install/).

2. **Code**: Clone the repo and `cd` into the project root (same folder as `docker-compose.yml`).

3. **Environment**: Copy the template and edit secrets and domains.
   ```bash
   cp .env.example .env
   nano .env   # or vim
   ```
   Set at minimum: `POSTGRES_PASSWORD`, `DJANGO_SECRET_KEY`, `DEBUG=false`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `PUBLIC_HOST`, `PUBLIC_SCHEME` (use `https` behind TLS), `REPLICATE_API_TOKEN`. For GPT Image 2 tuning, set `REPLICATE_MODEL`, `REPLICATE_GPT_IMAGE_ASPECT_RATIO`, etc. (see `.env.example` comments).

4. **Firewall**: Open the port you expose (default `3000` for the kiosk UI nginx, or only `80`/`443` if you put a host reverse proxy in front).

5. **Start**:
   ```bash
   docker compose up -d --build
   ```
   - Kiosk UI: `http://YOUR_SERVER_IP:3000` (or your proxy URL).
   - API (direct): `http://YOUR_SERVER_IP:8000` (usually only needed for debugging; the frontend container proxies `/api` and `/media` to the backend).

6. **Admin user**:
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

7. **Production hardening (recommended)**:
   - Put **Caddy** or **Nginx** on the host terminating HTTPS and proxy to `127.0.0.1:3000` (frontend) so users hit `https://your-domain` without `:3000`.
   - Replace Django `runserver` with **Gunicorn** (or uwsgi) in `docker-compose.yml` for the backend service; `runserver` is fine for demos, not ideal under load.
   - For releases without bind-mounting source, remove the `./backend:/app` volume and rely on the image build only (current compose mounts code for convenience).

`backend` and `celery-worker` load **`env_file: .env`** so variables in the project root `.env` are available to Django and Celery without duplicating every key in `docker-compose.yml`.

### Deploy on Railway

Use **three services** from the same GitHub repo (plus managed **Postgres** and **Redis**), so the kiosk UI, API, and Celery each scale and restart independently.

#### 1. Create the project

1. [Railway](https://railway.app) → **New Project** → **Deploy from GitHub** → select this repo.

#### 2. Add databases

1. **New** → **Database** → **PostgreSQL**. Railway injects `DATABASE_URL` on linked services.
2. **New** → **Database** → **Redis**. Railway injects `REDIS_URL`. Leave `CELERY_BROKER_URL` empty on workers so Django/Celery pick up `REDIS_URL` automatically (see `backend/app/settings.py`).

#### 3. Service: **backend** (Django API)

1. **New** → **Empty service** → connect the repo.
2. **Settings** → **Root Directory**: `backend`
3. **Settings** → **Dockerfile** (default `Dockerfile` is fine). The image `CMD` runs `bin/start-railway.sh` (migrations + **Gunicorn** on Railway’s `PORT`).
4. **Variables** → **Reference** `DATABASE_URL` and `REDIS_URL` from the plugins. Add at least:
   - `DJANGO_SECRET_KEY` (long random string)
   - `DEBUG=false`
   - `ALLOWED_HOSTS` = your backend’s public hostname (e.g. `backend-production-xxxx.up.railway.app`)
   - `USE_X_FORWARDED_PROTO=true` (HTTPS terminates at Railway’s edge)
   - `CORS_ALLOWED_ORIGINS` = your **frontend** public URL (e.g. `https://frontend-production-yyyy.up.railway.app`)
   - `CSRF_TRUSTED_ORIGINS` = same as `CORS_ALLOWED_ORIGINS`
   - `PUBLIC_HOST`, `PUBLIC_SCHEME=https`, `PUBLIC_PORT=` (empty if default 443) so **QR download links** point at a host phones can open (often the **frontend** URL if `/media/` is only used through the nginx proxy, or the backend URL if you expose media there)
   - `REPLICATE_API_TOKEN` and any `REPLICATE_*` options you use locally
5. **Volumes** (recommended): add a volume mounted at **`/app/media`** so guest and generated photos survive redeploys.

Generate a domain for the service (**Settings** → **Networking** → **Generate domain**). Use that hostname in `ALLOWED_HOSTS`.

#### 4. Service: **celery-worker**

1. **New** → **Empty service** → same repo, **Root Directory**: `backend`
2. **Settings** → **Start Command**:
   ```bash
   celery -A app worker -l info --concurrency=2
   ```
3. **Variables**: same references as **backend** (`DATABASE_URL`, `REDIS_URL`, `DJANGO_SECRET_KEY`, `REPLICATE_*`, etc.). Workers do not need `PORT`.

#### 5. Service: **frontend** (kiosk nginx)

1. **New** → **Empty service** → same repo.
2. **Root Directory**: `frontend`
3. **Settings** → **Dockerfile path**: `Dockerfile.railway`
4. **Variables**:
   - `BACKEND_PROXY_URL` = the **public https URL** of the **backend** service (no path), e.g. `https://backend-production-xxxx.up.railway.app`
5. **Networking** → generate a domain for the kiosk (this is the URL guests open).

Railway sets **`PORT`** automatically; the entrypoint renders `nginx.railway.template` and starts nginx.

#### 6. Smoke test

- Open the **frontend** URL → kiosk should load and API calls should succeed.
- Run **`python manage.py createsuperuser`** once via Railway’s shell on the **backend** service if you need Django admin.

| Variable | Railway notes |
|----------|----------------|
| `DATABASE_URL` | Provided by Postgres plugin when variables are referenced on the service. |
| `REDIS_URL` | Provided by Redis plugin; used as Celery broker when `CELERY_BROKER_URL` is unset. |
| `USE_X_FORWARDED_PROTO` | Set to `true` on the Django service behind HTTPS. |
| `BACKEND_PROXY_URL` | **Frontend service only**: full `https://…` URL of the backend. |
| `DJANGO_EXTRA_ALLOWED_HOSTS` | Optional comma list if you add custom domains without rewriting `ALLOWED_HOSTS`. |
