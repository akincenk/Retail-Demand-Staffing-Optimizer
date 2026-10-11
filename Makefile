up:
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f --tail=200 api
revision:
	alembic revision --autogenerate -m "$${msg}"
upgrade:
	alembic upgrade head
lint:
	ruff check .
test:
	pytest -q
seed:
	docker compose exec api python -m app.seed.seed_demo
