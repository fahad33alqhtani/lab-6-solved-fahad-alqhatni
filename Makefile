.PHONY: install run-batch lint test serve up down image-size smoke

install:
	pip install -e ".[dev,api]"

run-batch:
	python -m fraud_service.batch

lint:
	ruff check src tests

test:
	python -m pytest -v

serve:
	fastapi dev src/fraud_service/api/app.py

up:
	docker compose up -d --build

down:
	docker compose down

image-size:
	docker images fraud-service:dev --format "{{.Size}}"

smoke:
	curl -fsS localhost:8000/v1/health
	curl -fsS localhost:8000/v1/ready
