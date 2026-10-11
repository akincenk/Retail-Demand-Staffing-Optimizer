up:
	docker compose -f infra/docker-compose.yml up -d --build
down:
	docker compose -f infra/docker-compose.yml down
logs:
	docker compose -f infra/docker-compose.yml logs -f --tail=200 api
migrate:
	docker compose -f infra/docker-compose.yml exec api alembic revision -m "$${msg}"
upgrade:
	docker compose -f infra/docker-compose.yml exec api alembic upgrade head
seed:
	docker compose -f infra/docker-compose.yml exec api python -m app.seed.seed_demo
test:
	docker compose -f infra/docker-compose.yml exec api pytest -q
