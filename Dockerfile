FROM node:22-alpine AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Same-origin API when UI is served by FastAPI.
ENV VITE_API_BASE=
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend /web/dist /frontend/dist
ENV FRONTEND_DIST=/frontend/dist \
    DATABASE_URL=sqlite+pysqlite:////app/shortx.db \
    REDIS_URL=memory:// \
    CELERY_ALWAYS_EAGER=1 \
    SHORTX_LOCAL=1
EXPOSE 8000
CMD ["sh", "-c", "gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --workers 1"]
