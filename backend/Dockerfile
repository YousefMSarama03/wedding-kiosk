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
RUN mkdir -p /tmp/.u2net /tmp/numba_cache \
    && curl -fsSL --connect-timeout 60 --retry 3 --retry-delay 5 --max-time 3600 \
        -o /tmp/.u2net/u2net.onnx \
        https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx \
    && chmod -R a+rX /tmp/.u2net /tmp/numba_cache

ENV U2NET_HOME=/tmp/.u2net
ENV NUMBA_CACHE_DIR=/tmp/numba_cache

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000"]
