# AWS Deployment Reference

Two paths, depending on how much you want to invest in ops maturity.

## Option A — Managed, production-shaped (ECS Fargate)

```
                    Route 53  (short.yourdomain.com)
                        │
                        ▼
                 CloudFront (optional CDN for the SPA + redirects)
                        │
                        ▼
              Application Load Balancer (HTTPS via ACM)
                   │                     │
          /  and  /api/*            (SPA static)
                   ▼                     ▼
        ┌────────────────────┐   ┌────────────────────┐
        │ ECS Service: api   │   │ S3 + CloudFront     │
        │ (FastAPI/gunicorn) │   │ React build         │
        └─────────┬──────────┘   └────────────────────┘
                  │
        ┌─────────┴──────────┐
        │ ECS Service: worker│  (Celery, no public ingress)
        └─────────┬──────────┘
                  │
     ┌────────────┼─────────────┐
     ▼            ▼             ▼
  RDS Postgres  ElastiCache  (CloudWatch logs/metrics)
  (Multi-AZ)    Redis
```

### Components

| Concern | AWS service | Notes |
|---------|-------------|-------|
| API container | **ECS Fargate** service behind an **ALB** | 2+ tasks, autoscale on CPU/RPS |
| Worker container | **ECS Fargate** service (no ALB) | scales independently of the API |
| Database | **RDS for PostgreSQL** (Multi-AZ) | automated backups, private subnets |
| Cache / broker | **ElastiCache for Redis** | cache, rate-limit counters, Celery broker |
| SPA hosting | **S3 + CloudFront** | build with `VITE_API_BASE=https://short.yourdomain.com` |
| Images | **ECR** | push the `backend` image once; api & worker share it |
| TLS | **ACM** cert on the ALB / CloudFront | |
| Secrets | **SSM Parameter Store / Secrets Manager** | inject `JWT_SECRET`, DB creds as task env |
| Observability | **CloudWatch** logs + alarms | 5xx rate, queue depth, DB connections |

### Rollout sketch

```bash
# 1. Build & push the backend image (api and worker use the same image)
aws ecr get-login-password | docker login --username AWS --password-stdin <acct>.dkr.ecr.<region>.amazonaws.com
docker build -t shortx-backend ./backend
docker tag shortx-backend <acct>.dkr.ecr.<region>.amazonaws.com/shortx-backend:latest
docker push <acct>.dkr.ecr.<region>.amazonaws.com/shortx-backend:latest

# 2. Run DB migrations as a one-off ECS task
#    command: alembic upgrade head

# 3. api task command:
#    gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4
# 4. worker task command:
#    celery -A app.celery_app.celery_app worker -Q analytics --concurrency 4

# 5. Build & sync the SPA
cd frontend && VITE_API_BASE=https://short.yourdomain.com npm run build
aws s3 sync dist/ s3://shortx-frontend --delete
aws cloudfront create-invalidation --distribution-id <id> --paths '/*'
```

### Production hardening checklist

- [ ] `JWT_SECRET` from Secrets Manager, not `.env`
- [ ] RDS + ElastiCache in **private** subnets; only ECS SGs may reach them
- [ ] ALB security group allows 443 from the internet only
- [ ] Enable RDS automated backups + a read replica if analytics reads grow
- [ ] Set `BASE_URL` and `CORS_ORIGINS` to the real domain(s)
- [ ] Autoscaling: api on request count, worker on Redis queue depth
- [ ] CloudWatch alarms on 5xx, latency p99, and Celery backlog

## Option B — Single VM (fastest to stand up)

For a demo or low volume, run the whole `docker-compose.yml` on one EC2 instance
(or Lightsail) behind an nginx/Caddy TLS terminator:

```bash
# on the instance
git clone <repo> && cd shortx
cp .env.example .env      # set JWT_SECRET, BASE_URL=https://your.domain
docker compose up -d --build
docker compose exec api alembic upgrade head
```

Point a domain at the instance and terminate TLS with Caddy (automatic Let's Encrypt).
This trades the resilience/scaling of Option A for a 5-minute setup.

## Migrations

The API image ships Alembic. Generate and apply migrations rather than relying on
`create_all` (which is only a dev/demo convenience):

```bash
docker compose exec api alembic revision --autogenerate -m "add feature x"
docker compose exec api alembic upgrade head
```
