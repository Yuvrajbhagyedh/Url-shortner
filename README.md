# ShortX — URL Shortener with Click Analytics

A production-style URL shortener: fast redirects (Redis cache in front of the DB),
async click analytics via Celery, JWT auth, API keys with monthly quotas, rate
limiting, and QR codes. React + Vite dashboard on top of a FastAPI backend.

**Stack:** FastAPI · SQLAlchemy · Alembic · Celery · Redis · PostgreSQL · React 18 · Vite · Docker

---

## Run locally (no Docker, no Postgres, no Redis)

A `SHORTX_LOCAL=1` mode runs the whole app offline: SQLite instead of Postgres,
in-process fakeredis instead of Redis, and inline (eager) Celery so redirects
still record clicks — no broker or worker needed.

### Backend
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt fakeredis pytest   # Windows
# source .venv/bin/activate && pip install -r requirements.txt fakeredis pytest   # macOS/Linux
python run_local.py
```
API: http://localhost:8000  ·  Docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:5173

### Tests
```bash
cd backend && python -m pytest -q
```

---

## Run with Docker (full stack: Postgres + Redis + API + worker + frontend)

> Note: `docker-compose.yml` and `scripts/seed_demo.py` referenced by the
> `Makefile` are not included in this snapshot; add them (or use the local mode
> above) before `make up`.

```bash
make up      # build + start everything
make test    # backend tests
make down    # stop
```

---

## Hosting online

1. **Backend** — deploy to Render / Railway / Fly.io / a VPS. Provision a
   PostgreSQL DB and a Redis instance, run a Celery worker, and set env vars
   (see `backend/.env.example`). Set `BASE_URL` to your public domain so short
   links are built correctly, and set a strong `JWT_SECRET`.
2. **Frontend** — `npm run build` and deploy the `dist/` to any static host
   (Vercel / Netlify / Cloudflare Pages). Set `VITE_API_BASE` to the backend URL.
3. **Custom short-link domain** — point your domain's DNS at the backend and set
   `BASE_URL=https://yourdomain.com`.

See `infra/aws-deployment.md` for an AWS deployment sketch.

## Configuration

All backend settings are environment variables — see `backend/.env.example`.
Copy it to `backend/.env` and fill in real values.
