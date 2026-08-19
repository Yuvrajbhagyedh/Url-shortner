FROM node:22-alpine AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_BASE=
RUN npm run build && test -f dist/index.html && test -d dist/assets

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend /web/dist ./frontend/dist
RUN test -f /app/frontend/dist/index.html && ls /app/frontend/dist/assets | head
ENV FRONTEND_DIST=/app/frontend/dist \
    DATABASE_URL=sqlite+pysqlite:////app/shortx.db \
    REDIS_URL=memory:// \
    CELERY_ALWAYS_EAGER=1 \
    SHORTX_LOCAL=1
EXPOSE 8000
# Single uvicorn process — lighter on Render Free (512MB) than gunicorn.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

