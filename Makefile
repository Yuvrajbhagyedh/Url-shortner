.PHONY: up down logs build test seed fmt

up:            ## Start the full stack (db, redis, api, worker, frontend)
	docker compose up --build

down:          ## Stop and remove containers
	docker compose down

logs:          ## Tail all logs
	docker compose logs -f

test:          ## Run backend tests locally (SQLite + fakeredis, no services needed)
	cd backend && python -m pytest -q

seed:          ## Generate demo links + synthetic click analytics
	docker compose exec api python scripts/seed_demo.py

migrate:       ## Autogenerate + apply an Alembic migration inside the api container
	docker compose exec api alembic revision --autogenerate -m "auto"
	docker compose exec api alembic upgrade head
