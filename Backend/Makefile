.PHONY: run dev test test-unit test-integration lint format clean

# === Development ===
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev: run

# === Services ===
d-up:
	docker compose up -d

d-down:
	docker compose down

d-logs:
	docker compose logs -f db

d-res:
	docker compose restart

migrate:
	alembic upgrade head

# === Testing ===
test:
	pytest --cov=app --cov-report=term-missing

test-unit:
	pytest -m unit --tb=short

test-integration:
	pytest -m integration --tb=short

test-e2e:
	pytest -m e2e --tb=short

# === Code Quality ===
lint:
	ruff check app tests scripts
	mypy app

format:
	ruff format app tests scripts
	ruff check --fix app tests scripts

# === Utilities ===
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov

install:
	pip install -r requirements.txt

# === Extraction ===
extract:
	python scripts/extract_papers.py --subject "$(subject)" --limit $(limit)
