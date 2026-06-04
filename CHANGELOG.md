# Changelog

Alle nennenswerten Änderungen werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).
Dieses Projekt verwendet [Semantic Versioning](https://semver.org/lang/de/).
Einträge ab Version 1.0.0 werden von python-semantic-release aus den
Conventional Commits generiert.

## [Unreleased]

### Added
- Versionsanzeige im Footer (`__version__` als Single Source)
- Health-Endpoint `GET /health/` (Datenbank- und Speicher-Check) für Docker + Uptime Kuma
- Make-Targets `init`, `check`, `release`, `deploy`
- AGENTS.md (KI-Steckbrief) und app-info.yml (Skill-Provenienz)
- Release-Pipeline mit python-semantic-release (Version + CHANGELOG + Tag + Docker-Push nach ghcr.io)

### Changed
- Container-Registry vereinheitlicht auf `ghcr.io/mabaumga`

## [1.0.0] - 2026-06-04

### Added
- Erste stabile Baseline der produktiv auf Unraid laufenden Karteikarten-App
