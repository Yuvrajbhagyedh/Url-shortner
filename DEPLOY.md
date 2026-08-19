# Deploy ShortX (free, no card for Postgres/Redis)

Host everything as **one Free web service** — SQLite + in-memory cache, UI and API on the same URL. Same pattern as the realtime chat app.

## Steps on Render

1. Open [https://dashboard.render.com](https://dashboard.render.com) (already logged in with GitHub).

2. **+ New → Web Service** (do **not** pick Blueprint / Postgres / Key Value).

3. Connect repo **Yuvrajbhagyedh/Url-shortner**, branch **main**.

4. Settings:
   - **Language:** Docker  
   - **Dockerfile path:** `./Dockerfile`  
   - **Instance type:** **Free**  
   - Root directory: leave empty  

5. Environment variables (optional — Dockerfile already sets defaults):

   | Name | Value |
   | --- | --- |
   | `DATABASE_URL` | `sqlite+pysqlite:////app/shortx.db` |
   | `REDIS_URL` | `memory://` |
   | `CELERY_ALWAYS_EAGER` | `1` |
   | `SHORTX_LOCAL` | `1` |
   | `JWT_SECRET` | click **Generate** |

6. Click **Deploy Web Service**. Wait until **Live**.

7. Open the `.onrender.com` URL → register → create a short link.

Short links look like `https://your-service.onrender.com/abc1234`.

## Notes

- Free instances sleep after idle time; first load can take ~30–50s.
- SQLite data can reset when the free instance restarts (no paid disk).
- Do not add Postgres or Key Value unless you want to pay.

Repo: https://github.com/Yuvrajbhagyedh/Url-shortner
