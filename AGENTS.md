# AGENTS.md — Karteikarten

> **Mobile-optimierte Web-App zum Lernen mit digitalen Karteikarten (Leitner-System) — Einzelbenutzer, als PWA offline nutzbar.**
> Kompakter Steckbrief für KI-Agenten. Ausführliche Arbeitsanweisungen: siehe `CLAUDE.md`.

## Zweck

Lern-Anwendung für digitale Karteikarten nach dem **Leitner-System** (5 Fächer mit
steigenden Wiederholungsintervallen: 1/3/7/14/30 Tage). Karten haben Vorder-/Rückseite +
Zusatzinfos, sind bidirektional lernbar und in thematischen Lernblöcken organisiert.
Single-User (kein Login), mobile-first, als Progressive Web App offline nutzbar.

## Tech-Stack

- **Sprache:** Python 3.12
- **Framework:** Django 6.0.5
- **Persistenz:** SQLite
- **Frontend:** Bootstrap 5, Alpine.js, HTMX, PWA (Manifest + Service Worker)
- **Serving:** gunicorn + whitenoise (Static Files)
- **Tooling:** make, Docker

## Architektur

Einfache, flache **Django-App-Struktur** — bewusst **kein** hexagonales Layout
(erklärtes „Bastelprojekt", keine Tests). `config/` ist das Django-Projektpaket,
die gesamte Fachlichkeit liegt in der einzelnen App `karteikarten/`.

## Struktur & Einstiegspunkte

```
config/                    # Django-Projektpaket (Settings, URLs, WSGI) — DJANGO_SETTINGS_MODULE=config.settings
karteikarten/              # Haupt-App
  models.py                # Domänen-Modelle (Einstieg für Datenmodell)
  views.py · urls.py       # UI/Routing
  services/                # Import-Services
  management/commands/     # import_json, import_csv
  middleware.py            # Auto-Import-Middleware
  templates/ · static/     # UI, CSS/JS, PWA-Manifest
docs/                      # FACHLICHE_BESCHREIBUNG.md, KI_IMPORT_ANLEITUNG.md, JSON-Import-Schema
scripts/                   # Seed-Skripte
```

- **Hier anfangen:** `karteikarten/models.py` (Datenmodell) + `docs/FACHLICHE_BESCHREIBUNG.md`.
- **Kern-Entitäten:** Schulfach, Jahrgangsstufe, Lehrwerk(Unit), Lernblock, Karteikarte,
  ImportLog, Lernergebnis, Tages-/Globale-/Benutzer-Statistik, BenutzerLernblock, BenutzerKarteStatus.

## Bauen & Ausführen

| Befehl | Zweck |
|---|---|
| `make setup` | venv + Dependencies |
| `make run` | Django Dev Server (Port 8000) |
| `make migrate` | Migrationen erstellen + ausführen |
| `make seed` | Beispieldaten laden |
| `make release` | Release auslösen (semantic-release: Version + CHANGELOG + Tag + Docker-Push nach ghcr.io) |
| `make docker-build` / `docker-run` | Image lokal bauen / starten |

## Daten-Import

- **JSON (bevorzugt):** `python manage.py import_json <datei.json>` — Schema unter
  `docs/input/json/schema/`, Struktur `meta → inhalt → units → bloecke → karten`.
- **CSV (einfach):** `python manage.py import_csv <datei.csv> --block "Name"` — Spalten `vorne;hinten;beispiel;tags`.
- **Auto-Import:** Dateien in `/app/data/import` werden periodisch eingelesen
  (`KARTEIKARTEN_IMPORT_INTERVAL`, Default 60s) und nach `/app/data/archive` verschoben.

## Konventionen (Kurz)

- Domänenbegriffe Deutsch (Lernblock, Karteikarte, Fach), IT-Begriffe Englisch, Doku Deutsch.
- Einfach halten, kein Over-Engineering. SQLite statt PostgreSQL. Mobile-first (Bootstrap 5).
- Keine Tests (Bastelprojekt). `DJANGO_SETTINGS_MODULE=config.settings`.

→ Vollständig: `CLAUDE.md`.

## Integrationen & verwandte Repos

- Keine externen APIs. Datenzufluss ausschließlich über Datei-Import (JSON/CSV).

## Deployment

Docker-Standalone auf **Unraid** (Homeserver Baumgartner, privat), URL
`https://karteikarten.baumgartner.online`. Image `ghcr.io/mabaumga/karteikarten:latest`,
Container `karteikarten`, Port 8080→8000, persistente Volumes (`data`/`import`/`archive`).
**Release:** `make release` → GitHub Actions (`release.yml`) mit python-semantic-release
(Version + CHANGELOG + Tag) und Docker-Push nach ghcr.io.

## Mehr Kontext

- `CLAUDE.md` — Arbeitsanweisungen & Konventionen
- `docs/FACHLICHE_BESCHREIBUNG.md` — fachliche Beschreibung
- `docs/KI_IMPORT_ANLEITUNG.md` — Import-Anleitung für KI-gestützte Inhaltserstellung
