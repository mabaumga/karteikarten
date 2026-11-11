# AGENTS.md — karteikarten

Einzige Quelle der Projektregeln für jeden KI-Agenten. Knapp halten: Was nicht bei fast jeder
Aufgabe gebraucht wird, steht in einer verlinkten Datei (Tabelle unten), nicht hier.
Maschinenlesbare Fakten (Deployment, Backup, Monitoring, Plane-Projekt): `app-info.yml`.

## Zweck und Status

Mobile Web-App zum Lernen mit digitalen Karteikarten nach dem Leitner-System (5 Stufen,
Intervalle 1/3/7/14/30 Tage), bidirektional, in Lernblöcken, als PWA offline nutzbar. Login
über Django-Auth; Verwaltung nur für `is_staff`. Bastelprojekt: einfach halten.

## Stack und Einstieg

- Python/Django, SQLite, Bootstrap 5 + Alpine.js + HTMX, gunicorn + whitenoise
- Flach im Repo-Root: `config/` (Projektpaket, `DJANGO_SETTINGS_MODULE=config.settings`) und
  die einzige App `karteikarten/`; Einstieg `karteikarten/models.py`
- Gate: `make dod` (= `make check`), auch als pre-push-Hook. GitHub Actions ist **aus** — nur
  das lokale Gate zählt.

## Harte Regeln

- In der Oberfläche heißt das Leitner-Fach „Stufe“; „Fach“ ist dort das Schulfach. Angezeigt
  wird immer `BenutzerKarteStatus.fach` (persönlich), nie `Karteikarte.fach` (altes globales
  Feld).
- Verwaltendes (Blöcke, Karten, Import, Benutzer, Backup) nur mit `is_staff` und in eigenen
  Abschnitten, nie zwischen den Lernaktionen.
- SQLite bleibt, kein PostgreSQL; mobile first.
- Tickets nur in Plane, Projekt „Karteikarten“ (`KK`), Beschreibungen als HTML. Nie GitHub
  Issues.

## Aktive Skills

- software/L0-entwicklungsphilosophie
- software/L1-architektur
- software/L1-anforderungen
- software/L1-dokumentation
- software/L2-django-standard

Abweichungen:
- software/L1-api-design: nicht aktiv — `api/…` bedient nur das eigene Frontend (Antworten,
  PWA-Sync), keine fremden Consumer.
- software/L2-django-standard: Code nicht unter `src/` bzw. `apps/`, sondern flach im
  Repo-Root — eine App, minimaler Schnitt.
- software/L3-deploy-one, L3-deploy-hetzner: nicht aktiv — läuft auf Unraid (`app-info.yml`
  → `deployment`).
- software/opt-in/barrierearm: nicht aktiv — Bastelprojekt, L0-Basis genügt.

## Lies bei Bedarf

| Wenn du … | lies |
|---|---|
| Struktur, Make-Targets, Tests, Version, Health oder Daten-Import im Detail brauchst | `docs/STACK.md` |
| Fachlichkeit, Lernmodi, Oberfläche oder Datenmodell verstehen willst | `docs/FACHLICHE_BESCHREIBUNG.md` |
| Lerninhalte per KI für den JSON-Import erzeugen willst | `docs/KI_IMPORT_ANLEITUNG.md`, Schema `docs/input/json/schema/` |
| deployen oder releasen willst | `app-info.yml` → `deployment`; Release lokal: `make release-local` |
