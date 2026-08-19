# Deploying ShortX to Render

This repo ships a `render.yaml` Blueprint that provisions everything:

| Service | What it is | Plan |
|---|---|---|
| `shortx-db` | PostgreSQL | free |
| `shortx-redis` | Redis (Key Value) — cache + rate limiting | free |
| `shortx-api` | FastAPI backend (Celery runs inline, no worker) | free |
| `shortx-frontend` | React + Vite static site | free |

> Free Postgres on Render is deleted after ~30 days and free web services sleep
> after inactivity (first request is slow). Fine for a demo/portfolio; upgrade
> the two paid-but-cheap plans if you want it always-on.

## Steps

1. **Push this repo to GitHub** (already done: `Yuvrajbhagyedh/Url-shortner`).

2. **Create a Render account** at https://render.com and connect your GitHub.

3. **New + → Blueprint**, pick the `Url-shortner` repo. Render reads
   `render.yaml` and shows the four services. Click **Apply**.

4. Render will ask for the two `sync: false` values. You can leave them blank
   for the first apply and fill them once the URLs exist:
   - On **shortx-api**, set `CORS_ORIGINS` = the frontend URL
     (e.g. `https://shortx-frontend.onrender.com`).
   - On **shortx-frontend**, set `VITE_API_BASE` = the backend URL
     (e.g. `https://shortx-api.onrender.com`), then **Manual Deploy → Clear
     build cache & deploy** so Vite re-bakes it in.

5. Open the frontend URL, sign up, and create a link. Short links are served by
   the backend (e.g. `https://shortx-api.onrender.com/abc1234`) and resolve
   automatically — `BASE_URL` is derived from Render's injected URL.

## Custom short-link domain (optional)

1. Add your domain to the **shortx-api** service (Settings → Custom Domains) and
   point its DNS at Render as instructed.
2. Set `BASE_URL=https://yourdomain.com` on **shortx-api**.
3. New short links will now read `yourdomain.com/abc1234`.

## Environment variables (reference)

See `backend/.env.example`. On Render, `DATABASE_URL`, `REDIS_URL`, the Celery
URLs, and `JWT_SECRET` are wired automatically by the Blueprint. `CELERY_ALWAYS_EAGER=1`
makes the redirect record clicks inline so no separate Celery worker is needed.

### Want a real Celery worker later?
Remove `CELERY_ALWAYS_EAGER`, then add a `worker` service in `render.yaml`:

```yaml
  - type: worker
    name: shortx-worker
    runtime: python
    plan: starter        # background workers are not free
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.celery_app.celery_app worker -Q analytics --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase: { name: shortx-db, property: connectionString }
      - key: CELERY_BROKER_URL
        fromService: { type: keyvalue, name: shortx-redis, property: connectionString }
      - key: CELERY_RESULT_BACKEND
        fromService: { type: keyvalue, name: shortx-redis, property: connectionString }
```
