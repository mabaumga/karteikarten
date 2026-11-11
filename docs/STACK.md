# Stack, Struktur und Betrieb im Detail

Ergänzt `AGENTS.md`. Deployment-Fakten (Host, Image, Container, Pfade) stehen nur in
`app-info.yml` → `deployment`.

## Struktur

```
config/                    # Django-Projektpaket (Settings, URLs, WSGI, Context-Processor)
karteikarten/              # die einzige App
  models.py                # Datenmodell — hier anfangen
  views.py · urls.py       # UI/Routing; api/… nur für das eigene Frontend (Antworten, PWA-Sync)
  services/                # Antwortprüfung, Statistik, JSON-Import/-Export, Import-Scheduler
  management/commands/     # import_json, import_csv
  middleware.py            # Auto-Import-Middleware
  health.py · checks.py    # /health/
  templates/karteikarten/  # UI inkl. manifest.json + sw.js (PWA)
docs/                      # Fachliche Beschreibung, KI-Import, JSON-Schema unter input/json/schema/
scripts/                   # Seed-Skripte
tests/                     # pytest
```

Kern-Entitäten: Schulfach, Jahrgangsstufe, Lehrwerk/LehrwerkUnit, Lernblock, Karteikarte,
Test, ImportLog, Lernergebnis, Tages-/Globale-/BenutzerStatistik, BenutzerLernblock,
BenutzerKarteStatus.

## Make-Targets

| Befehl | Zweck |
|---|---|
| `make setup` | venv + Abhängigkeiten inkl. Dev-Werkzeuge |
| `make run` | Dev-Server, Port 8000 |
| `make migrate` | Migrationen erstellen + ausführen |
| `make init` | idempotent: `migrate --noinput` + `collectstatic` (auch im Docker-Entrypoint) |
| `make seed` | Beispieldaten laden |
| `make dod` (= `make check`) | Gate: Django-Check, ruff lint + format, pyright, Migrations-Check, pytest |
| `make release-dry-run` | nächste Version ausgeben, ändert nichts |
| `make release` | lokal: Version, CHANGELOG, Commit, Tag, Push — kein Image, kein Deploy |
| `make deploy` | Hinweis auf den Weg live: `infrastruktur/scripts/ship.sh ~/git/karteikarten` |
| `make docker-build` / `docker-run` | Image lokal bauen / starten |

Das Gate läuft als pre-push-Hook (`.pre-commit-config.yaml`); beim Commit nur schnelle
Autofixes und gitleaks. Release und Deploy laufen lokal (Actions ist aus): `ship.sh` ruft
`make release-dry-run` und `make release` in einem frischen Klon von `origin/main` und rollt
dann über `deploy-lokal.sh` nach Unraid aus (Image lokal gebaut, per ssh geladen).
`release-local` / `release-dry-run-local` sind nur noch Aliase.

## Tests

pytest unter `tests/`. Fachlogik (Antwortprüfung, Statistik) hat eigene Tests, die Seiten einen
Rauchtest (`tests/test_seiten.py`).

## Version und Health

- Version: Single Source `karteikarten/__version__`, angezeigt über
  `config.context_processors.version_context` im Footer. Bumpt python-semantic-release
  (`pyproject.toml` → `[tool.semantic_release]`), nie von Hand.
- `GET /health/`: JSON-Contract ohne Auth, prüft Datenbank + Speicher
  (`karteikarten/health.py`, `checks.py`).

## Daten-Import

- **JSON (bevorzugt):** `python manage.py import_json <datei.json>` — Schema
  `docs/input/json/schema/lerninhalt_schema.json`, Beispiele daneben, Struktur
  `meta → inhalt → units → bloecke → karten`. Inhalte per KI erzeugen:
  `docs/KI_IMPORT_ANLEITUNG.md`.
- **CSV:** `python manage.py import_csv <datei.csv> --block "Name"` — Spalten
  `vorne;hinten;beispiel;tags`.
- **Auto-Import:** Dateien in `data/import` (`KARTEIKARTEN_IMPORT_DIR`, im Container
  `/app/data/import`) werden periodisch eingelesen (`KARTEIKARTEN_IMPORT_INTERVAL`, Default
  60 s) und nach `data/archive` (`KARTEIKARTEN_ARCHIVE_DIR`) verschoben.
