.PHONY: install run worker test lint format docker-up

install:
	python -m pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	celery -A app.workers.celery_app:celery_app worker --loglevel=info

test:
	pytest

lint:
	ruff check .
	mypy app

format:
	ruff format .

docker-up:
	docker compose up --build
