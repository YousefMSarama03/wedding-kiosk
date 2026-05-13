FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake in rembg u2net weights so first request does not download ~176MB from GitHub (slow / 30s timeouts).
RUN mkdir -p /root/.u2net \
    && curl -fsSL --connect-timeout 60 --retry 3 --retry-delay 5 --max-time 3600 \
        -o /root/.u2net/u2net.onnx \
        https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx


COPY . .

# Collect static files for production
RUN python manage.py collectstatic --noinput --clear || true

EXPOSE 8000

# Use Gunicorn for production, runserver for development
CMD ["sh", "-c", "if [ \"$DEBUG\" = 'true' ]; then python manage.py runserver 0.0.0.0:${PORT:-8000}; else gunicorn app.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 4 --worker-class sync --timeout 120 --access-logfile - --error-logfile -; fi"]
