.PHONY: run migrate setup init check release deploy seed clean help
.PHONY: release-dry-run release-local release-dry-run-local
.PHONY: docker-build docker-run docker-stop docker-logs docker-shell docker-migrate docker-push

# Auto-venv: PYTHON zeigt auf .venv/bin/python falls vorhanden, sonst system-python3.
# So laeuft `make check` lokal (mit venv) und in CI (System-Python) gleichermassen.
VENV := .venv
PYTHON ?= $(shell test -x $(VENV)/bin/python && echo $(VENV)/bin/python || echo python3)

# Image-Name, wie ihn die Compose-Datei auf Unraid erwartet. Kein Registry-Weg mehr:
# deploy-lokal.sh baut lokal und laedt das Image per ssh (docker load).
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
	# **Auch die Entwicklungswerkzeuge.** Ohne sie legt `make setup` ein venv an,
	# in dem `make dod` sofort mit „No module named ruff" abbricht — das Ziel
	# verspricht „install dependencies" und laesst das Gate unbenutzbar.
	.venv/bin/pip install -r requirements-dev.txt
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

format-check:  ## Formatierung pruefen, ohne zu aendern
	$(PYTHON) -m ruff format --check .

# Typpruefung mit pyright im Modus `standard` (SK-21), Konfiguration in
# pyrightconfig.json. Ueber den Interpreter, nicht ueber ein `pyright` vom PATH —
# sonst prueft lokal und in der CI ein anderes Werkzeug. Der Exit-Code geht
# unveraendert ans Gate: ein Typfehler haelt `make dod` an.
typecheck: ## Typpruefung (pyright, Modus standard)
	$(PYTHON) -m pyright

migrations-check: ## Fehlende Migrationen aufdecken
	DJANGO_SETTINGS_MODULE=config.settings $(PYTHON) manage.py makemigrations --check --dry-run

# DAS Qualitaetsgate — einziger Einstiegspunkt fuer lokale Hooks UND die CI.
#
# CI und pre-push-Hook riefen hier schon dasselbe Ziel — das war bereits richtig.
# Es fehlten aber zwei Pruefungen, und zwar auf beiden Seiten gleichzeitig:
# `ruff format --check` und die Vollstaendigkeit der Migrationen. Ein geaendertes
# Modell ohne Migration waere nirgends aufgefallen.
#
# Das Ziel heisst jetzt `dod`, weil die Flotte diesen Namen fuehrt (CLAUDE.md,
# STACK.md, Skills); `check` bleibt als Alias.
#
# Siehe software/L0-entwicklungsphilosophie, Abschnitt Qualitaets-Gate.
dod: ## Definition of Done — DAS Gate (CI == lokal)
	DJANGO_SETTINGS_MODULE=config.settings $(PYTHON) manage.py check
	$(MAKE) lint
	$(MAKE) format-check
	$(MAKE) typecheck
	$(MAKE) migrations-check
	$(MAKE) test

check: dod ## Alias, weil der Name in Doku und Fingern verankert ist

# --- Release (lokal) -----------------------------------------------------------
# GitHub Actions ist flottenweit aus (INFRA-267). Das Release laeuft deshalb
# lokal: Version, CHANGELOG, Commit und Tag — kein Image, kein Deploy. Ausgerollt
# wird danach mit infrastruktur/scripts/ship.sh: Es ruft `make release-dry-run`
# und `make release` in einem frischen Klon und rollt dann ueber deploy-lokal.sh
# nach Unraid aus (Zielangaben: app-info.yml -> app.deployment).
#
# Eigenes venv, damit python-semantic-release nicht im Dev-venv landet, mit dem
# das Gate laeuft (Begruendung in requirements-release.txt).

RELEASE_VENV := .venv-release
RELEASE_PY := $(RELEASE_VENV)/bin/python
# Marke statt bin/python als Ziel: bin/python ist ein Symlink auf den System-
# Interpreter, ein touch darauf scheitert — und ohne Marke baut make jedes Mal neu.
RELEASE_STAMP := $(RELEASE_VENV)/.installiert

$(RELEASE_STAMP): requirements-release.txt
	python3 -m venv $(RELEASE_VENV)
	$(RELEASE_PY) -m pip install -q -r requirements-release.txt
	@touch $(RELEASE_STAMP)

# Letzte Ausgabezeile = naechste Version; ship.sh liest genau die.
release-dry-run: $(RELEASE_STAMP) ## Naechste Version anzeigen (schreibt nichts)
	@$(RELEASE_PY) -m semantic_release --noop version --print

release: $(RELEASE_STAMP) ## Version, CHANGELOG, Commit und Tag setzen, nach main pushen
	@# **`--no-vcs-release`:** Ohne den Schalter legt semantic-release nach Tag
	@# und Commit ein GitHub-Release an und scheitert mangels Token mit 401 — der
	@# Tag ist dann gesetzt, der Push fehlt (gesellschaft, GES-17). Gepusht wird
	@# deshalb erst am Ende, Commit und Tag atomar in einem Schritt.
	@test "$$(git rev-parse --abbrev-ref HEAD)" = "main" \
		|| { echo "Nur auf main. Aktuell: $$(git rev-parse --abbrev-ref HEAD)"; exit 1; }
	@test -z "$$(git status --porcelain)" || { echo "Arbeitsbaum nicht sauber."; exit 1; }
	@git fetch -q origin main && test "$$(git rev-parse HEAD)" = "$$(git rev-parse origin/main)" \
		|| { echo "main entspricht nicht origin/main. Erst pullen bzw. pushen."; exit 1; }
	$(RELEASE_PY) -m semantic_release version --no-push --no-vcs-release
	@TAG=$$(git tag --points-at HEAD --list 'v[0-9]*' --sort=-v:refname | head -n1); \
	  if [ -z "$$TAG" ]; then echo "Kein Release faellig — nichts zu pushen."; exit 0; fi; \
	  git push --atomic origin main "$$TAG"

# Alte Namen aus der Zeit vor KK-10, damit Notizen und Gewohnheit nicht ins Leere laufen.
release-local: release ## Alias fuer release
release-dry-run-local: release-dry-run ## Alias fuer release-dry-run

deploy: ## Hinweis: ausgerollt wird nur ein Release, ueber ship.sh
	@echo "Kein direktes Deployment. Release und Ausrollen nach Unraid in einem Schritt:"
	@echo "  ~/git/infrastruktur/scripts/ship.sh ~/git/karteikarten"
	@echo "Zielangaben (Host, Container, Image, Compose-Pfad): app-info.yml -> app.deployment"

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
	@echo "  make release-dry-run       - Naechste Version anzeigen (schreibt nichts)"
	@echo "  make release               - Version + CHANGELOG + Tag, Push (lokal, kein Deploy)"
	@echo "  make deploy                - Hinweis: Ausrollen ueber infrastruktur/scripts/ship.sh"
	@echo ""
	@echo "  make clean      - Remove containers and cache"
