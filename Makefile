.PHONY: install dev test smoke run docker-up docker-down seed openapi clean

install:
	pip install -e ".[dev]"

dev:
	uvicorn app.main:app --reload

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	pytest -q

smoke:
	python scripts/smoke_test.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down

seed:
	python examples/seed_dashboard_data.py

openapi:
	python scripts/export_openapi.py

clean:
	rm -rf .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
