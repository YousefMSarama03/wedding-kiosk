# AI Wedding Photo Kiosk

Guests take photos at the kiosk; the backend runs a keepsake pipeline (background removal, bride reference prep, then **Replicate InstantID** face-preserving generation). Optional **OpenAI** DALL-E legacy mode exists for emergencies. Guests scan a QR code to download the result.

## Requirements

- Docker and Docker Compose (to run with containers)
- Or: Python 3.12+, PostgreSQL (to run locally)

## Run with Docker

1. Copy `.env.example` to `.env` in the project root and fill in values, or configure the same environment variables in your shell.

   ```bash
   # Local dev with Docker Compose uses either DATABASE_URL or POSTGRES_* vars.
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
   VITE_API_URL=http://localhost:8000
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

3. Set `backend/.env` or environment variables: `DATABASE_URL` (preferred) or `POSTGRES_HOST=localhost`, `REPLICATE_API_TOKEN`, and optionally `OPENAI_API_KEY` + `KEEPSAKE_USE_OPENAI_LEGACY=true` for the legacy path, plus `PUBLIC_HOST` for QR reachability.

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
| `REDIS_URL` | Railway Redis connection URL for Celery and caching. |
| `VITE_API_URL` | Backend API URL exposed to the frontend in production. |
| `REPLICATE_API_TOKEN` | Required for default generation (InstantID on Replicate). |
| `REPLICATE_INSTANTID_MODEL` | Optional; defaults to a pinned `zsxkib/instant-id` version. Other models may need code/schema tweaks. |
| `OPENAI_API_KEY` | Only if `KEEPSAKE_USE_OPENAI_LEGACY=true` (DALL-E guest-only path). |
| `KEEPSAKE_USE_OPENAI_LEGACY` | `true` to skip Replicate and use legacy OpenAI generation. |

Serve the app behind a reverse proxy (e.g. Caddy or Nginx) with HTTPS. Point the proxy at the backend and (if applicable) at the frontend build; set `PUBLIC_SCHEME=https` and the correct `PUBLIC_HOST` so QR codes use `https://...` and phones can download securely.
