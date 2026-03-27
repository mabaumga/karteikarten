# CLAUDE.md

> Projektspezifische Anweisungen fuer die Karteikarten-App.
> **Stand:** 2026-03-27

---

## Projektuebersicht

**Karteikarten** — Mobile-optimierte Webanwendung zum Lernen mit digitalen Karteikarten (Leitner-System).

- **Stack:** Python 3.12, Django 4.2+, SQLite, Bootstrap 5, Alpine.js, HTMX
- **Deployment:** Docker (Standalone-Container), Unraid via docker-compose
- **Benutzer:** Einzelbenutzer-Anwendung (kein Login)
- **PWA:** Progressive Web App fuer Offline-Nutzung

---

## Projektstruktur

```
config/                    # Django-Projektpaket (Settings, URLs, WSGI)
karteikarten/              # Haupt-App (Models, Views, Templates, Services)
  management/commands/     # Import-Commands (import_json, import_csv)
  services/                # Import-Services
  static/                  # CSS, JS, Icons, Manifest
  templates/karteikarten/  # Django Templates
docs/                      # Dokumentation
  input/json/schema/       # JSON-Import-Schema + Beispiele
  FACHLICHE_BESCHREIBUNG.md
scripts/                   # Seed-Skripte
```

**Hinweis:** Kein hexagonales Layout — einfache Django-App-Struktur (Bastelprojekt).

---

## Fachliche Konzepte

- **Lernblock**: Thematische Sammlung von Karteikarten
- **Karteikarte**: Vorderseite (Begriff) + Rueckseite (Definition) + optionale Zusatzinfos
- **Leitner-System**: 5 Faecher mit steigenden Wiederholungsintervallen (1, 3, 7, 14, 30 Tage)
- **Bidirektional**: Karten koennen in beide Richtungen gelernt werden

---

## Import-Formate

### JSON (bevorzugt)
- Schema: `docs/input/json/schema/lerninhalt_schema.json`
- Beispiele: `docs/input/json/schema/beispiel_*.json`
- Struktur: `meta → inhalt → units → bloecke → karten`
- Management Command: `python manage.py import_json <datei.json>`

### CSV (einfach)
- Spalten: `vorne;hinten;beispiel;tags`
- Management Command: `python manage.py import_csv <datei.csv> --block "Name"`

---

## Entwicklung

```bash
make setup     # venv + Dependencies
make run       # Django Dev Server (Port 8000)
make migrate   # Migrationen erstellen + ausfuehren
make seed      # Beispieldaten laden
```

### Docker

```bash
make docker-build   # Image bauen
make docker-run     # Container starten
make docker-push    # Image in Registry pushen
```

---

## Sprache

- **Domaenenbegriffe** auf Deutsch (Lernblock, Karteikarte, Fach)
- **IT-Begriffe** auf Englisch (Model, View, Template, Service)
- **Dokumentation** auf Deutsch

---

## Vorgaben

- Einfach halten — kein Over-Engineering
- SQLite als Datenbank (kein PostgreSQL noetig)
- Mobile-first Design (Bootstrap 5)
- Keine Tests vorhanden (Bastelprojekt)
- `DJANGO_SETTINGS_MODULE=config.settings`
