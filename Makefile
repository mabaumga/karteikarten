.PHONY: run migrate setup init check release deploy seed clean help
.PHONY: release-local release-dry-run-local
.PHONY: docker-build docker-run docker-stop docker-logs docker-shell docker-migrate docker-push

# Auto-venv: PYTHON zeigt auf .venv/bin/python falls vorhanden, sonst system-python3.
# So laeuft `make check` lokal (mit venv) und in CI (System-Python) gleichermassen.
VENV := .venv
PYTHON ?= $(shell test -x $(VENV)/bin/python && echo $(VENV)/bin/python || echo python3)

# Registry (einheitlich ghcr.io — siehe release.yml + docker-compose.unraid.yml)
REGISTRY := ghcr.io/mabaumga
IMAGE := karteikarten
TAG := latest

# =============================================================================
# Development
# =============================================================================

run: ## Run Django dev server
	DJANGO_SETTINGS_MODULE=config.settings .venv/bin/python manage.py runserver 0.0.0.0:8000

migrate: ## Create and run migrations
	DJANGO_SETTINGS_MODULE=config.settings .venv/bin/python manage.py makemigrations
	DJANGO_SETTINGS_MODULE=config.settings .venv/bin/python manage.py migrate

setup: ## Create venv and install dependencies
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	mkdir -p data

init: ## Idempotent: Migrationen + Static (auch vom docker-entrypoint genutzt)
	DJANGO_SETTINGS_MODULE=config.settings $(PYTHON) manage.py migrate --noinput
	DJANGO_SETTINGS_MODULE=config.settings $(PYTHON) manage.py collectstatic --noinput

test: ## Tests ausfuehren
	DJANGO_SETTINGS_MODULE=config.settings $(PYTHON) -m pytest tests/ -q

lint: ## Linting + Format-Pruefung (im Gate)
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format: ## Formatierung anwenden
	$(PYTHON) -m ruff format .

check: ## Quality-Gate: Django System-Checks + Lint + Tests
	DJANGO_SETTINGS_MODULE=config.settings $(PYTHON) manage.py check
	$(MAKE) lint
	$(MAKE) test

release: ## Release ausloesen: semantic-release (Version + CHANGELOG + Tag + Docker-Push) via GitHub Actions
	gh workflow run release.yml

release-dry-run: ## Zeigt die nächste Version, ohne zu releasen
	gh workflow run release.yml -f dry_run=true
	@echo "Dry-Run gestartet — Ergebnis: gh run watch"

# --- Lokaler Release-Weg -----------------------------------------------------
# Solange GitHub Actions deaktiviert ist, laufen `release` und `release-dry-run`
# ins Leere: sie stossen nur einen Workflow an, der nicht startet. Die *-local-
# Ziele machen dasselbe von Hand.
#
# Eigenes venv, weil python-semantic-release ein zurueckgehaltenes GitPython
# braucht (Begruendung in requirements-release.txt) — das soll nicht im Dev-venv
# landen, mit dem `make check` laeuft.

RELEASE_VENV := .venv-release
SEMANTIC_RELEASE := $(RELEASE_VENV)/bin/semantic-release

$(SEMANTIC_RELEASE): requirements-release.txt
	python3 -m venv $(RELEASE_VENV)
	$(RELEASE_VENV)/bin/pip install -q -r requirements-release.txt

release-dry-run-local: $(SEMANTIC_RELEASE) ## Naechste Version anzeigen (ohne Actions)
	@GH_TOKEN=$$(gh auth token) $(SEMANTIC_RELEASE) version --print

release-local: $(SEMANTIC_RELEASE) ## Release ohne Actions: Gate + Version + Tag + CHANGELOG + Image nach ghcr.io
	$(MAKE) check
	GH_TOKEN=$$(gh auth token) $(SEMANTIC_RELEASE) version --push --tag --commit --changelog
	@VERSION=$$($(PYTHON) -c "import karteikarten; print(karteikarten.__version__)"); \
	  echo "Release $$VERSION — Image bauen und pushen"; \
	  gh auth token | docker login ghcr.io -u mabaumga --password-stdin; \
	  docker build --platform linux/amd64 \
	    -t $(REGISTRY)/$(IMAGE):$$VERSION -t $(REGISTRY)/$(IMAGE):latest .; \
	  docker push $(REGISTRY)/$(IMAGE):$$VERSION; \
	  docker push $(REGISTRY)/$(IMAGE):latest; \
	  echo "Deploy: ssh root@178.105.222.1 'cd /opt/hetzner && ./deploy.sh karteikarten'"

deploy: ## Hinweis: Deployment laeuft ueber das Release (ghcr.io) + Pull auf Unraid
	@echo "Kein direktes Deployment. 'make release' baut+pusht das Image nach ghcr.io;"
	@echo "auf Unraid danach: docker compose pull && docker compose up -d (karteikarten)."

seed: ## Seed database with Stilmittel
	DJANGO_SETTINGS_MODULE=config.settings .venv/bin/python scripts/seed_stilmittel.py

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build Docker image
	docker compose build

docker-run: ## Start Docker container
	docker compose up -d

docker-stop: ## Stop Docker container
	docker compose down

docker-logs: ## Show Docker logs
	docker compose logs -f

docker-shell: ## Shell into Docker container
	docker compose exec karteikarten /bin/bash

docker-migrate: ## Run migrations in Docker container
	docker compose exec karteikarten python manage.py migrate

docker-push: docker-build ## Build and push to registry
	docker tag karteikarten-karteikarten $(REGISTRY)/$(IMAGE):$(TAG)
	docker tag karteikarten-karteikarten $(REGISTRY)/$(IMAGE):$$(git describe --tags 2>/dev/null || echo "dev")
	docker push $(REGISTRY)/$(IMAGE):$(TAG)
	docker push $(REGISTRY)/$(IMAGE):$$(git describe --tags 2>/dev/null || echo "dev")
	@echo "Pushed: $(REGISTRY)/$(IMAGE):$(TAG)"

docker-seed: ## Seed database in Docker container
	docker compose exec karteikarten python scripts/seed_stilmittel.py

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Remove containers and cache
	docker compose down -v 2>/dev/null || true
	rm -rf staticfiles/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# =============================================================================
# Help
# =============================================================================

help: ## Show this help
	@echo "Karteikarten - Make Commands"
	@echo ""
	@echo "Development:"
	@echo "  make setup      - Create venv and install deps"
	@echo "  make run        - Run Django dev server (port 8000)"
	@echo "  make migrate    - Create and run migrations"
	@echo "  make seed       - Seed database with Stilmittel"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Start container"
	@echo "  make docker-stop    - Stop container"
	@echo "  make docker-logs    - Show logs"
	@echo "  make docker-shell   - Shell into container"
	@echo "  make docker-migrate - Run migrations in container"
	@echo "  make docker-push    - Build and push to registry"
	@echo "  make docker-seed    - Seed database in container"
	@echo ""
	@echo "Quality & Release:"
	@echo "  make check                 - Quality-Gate (Django-Checks + Lint + Tests)"
	@echo "  make release               - Release ueber GitHub Actions"
	@echo "  make release-dry-run       - Naechste Version anzeigen (ueber Actions)"
	@echo "  make release-local         - Release ohne Actions (Gate + Tag + Image)"
	@echo "  make release-dry-run-local - Naechste Version anzeigen (ohne Actions)"
	@echo ""
	@echo "  make clean      - Remove containers and cache"
