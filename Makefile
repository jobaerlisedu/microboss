.PHONY: help install migrate run test lint clean docker-build docker-up

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  install       Install Python dependencies"
	@echo "  migrate       Run database migrations"
	@echo "  run           Start development server"
	@echo "  test          Run test suite"
	@echo "  lint          Run linting"
	@echo "  clean         Remove cache and temp files"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-up     Start Docker Compose services"

install:
	pip install -r requirements/dev.txt

migrate:
	python manage.py migrate

run:
	python manage.py runserver 0.0.0.0:8000

test:
	python manage.py test apps --keepdb

lint:
	ruff check apps config
	ruff format --check apps config

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf staticfiles/

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
