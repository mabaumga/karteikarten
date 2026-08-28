# Changelog

Alle nennenswerten Änderungen werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).
Dieses Projekt verwendet [Semantic Versioning](https://semver.org/lang/de/).
Einträge ab Version 1.0.0 werden von python-semantic-release aus den
Conventional Commits generiert.

<!-- version list -->

## v1.5.0 (2026-08-28)

### Features

- **struktur**: Buecher und Kapitel pflegen, Blockauswahl als Baum
  ([#47](https://github.com/mabaumga/karteikarten/pull/47),
  [`e7cf600`](https://github.com/mabaumga/karteikarten/commit/e7cf600db95db1b5ba26e10973e13fbb5c7203fd))

- **tests**: Frei zusammengestellte Uebungssets ueber Block- und Buchgrenzen
  ([#48](https://github.com/mabaumga/karteikarten/pull/48),
  [`aed7565`](https://github.com/mabaumga/karteikarten/commit/aed75658130a7bac3833d7c08e5a5c7aa3195649))


## v1.4.0 (2026-08-28)

### Features

- **fortschritt**: Nach Schulfach und Lehrbuch gliedern, Blockstand in der Abfrage
  ([#46](https://github.com/mabaumga/karteikarten/pull/46),
  [`f6f5fd8`](https://github.com/mabaumga/karteikarten/commit/f6f5fd80779c50f358cab780b77fc264f7137cc3))


## v1.3.0 (2026-08-28)

### Bug Fixes

- **lernen**: Karten zufaellig statt in fester Reihenfolge abfragen
  ([#42](https://github.com/mabaumga/karteikarten/pull/42),
  [`30c4089`](https://github.com/mabaumga/karteikarten/commit/30c40899b13f035e2049b238f1d8552040d82df0))

- **release**: Semantic-release wieder lauffaehig machen
  ([#40](https://github.com/mabaumga/karteikarten/pull/40),
  [`c2c7fc8`](https://github.com/mabaumga/karteikarten/commit/c2c7fc8ad45201e4d47478d17c910ccf29c6dc9d))

- **release**: Semantic-release wieder lauffähig machen
  ([#40](https://github.com/mabaumga/karteikarten/pull/40),
  [`c2c7fc8`](https://github.com/mabaumga/karteikarten/commit/c2c7fc8ad45201e4d47478d17c910ccf29c6dc9d))

### Documentation

- Unraid-Altinstanz aus der Doku entfernen ([#41](https://github.com/mabaumga/karteikarten/pull/41),
  [`d5f0e63`](https://github.com/mabaumga/karteikarten/commit/d5f0e63794b5c41f65cb0ebc0ecb19e838cdb548))

- **makefile**: Deploy-Hinweis zeigt auf Hetzner statt Unraid
  ([#40](https://github.com/mabaumga/karteikarten/pull/40),
  [`c2c7fc8`](https://github.com/mabaumga/karteikarten/commit/c2c7fc8ad45201e4d47478d17c910ccf29c6dc9d))

### Features

- **lernen**: Tippmodus — die Antwort wird eingetippt statt aufgedeckt
  ([#45](https://github.com/mabaumga/karteikarten/pull/45),
  [`909e532`](https://github.com/mabaumga/karteikarten/commit/909e532ef96409310090ec0c83ea10ac52d5ce17))

- **ui**: Neustrukturierung — vier Bereiche, ein Weg ins Lernen, Fortschritt
  ([#44](https://github.com/mabaumga/karteikarten/pull/44),
  [`40c0915`](https://github.com/mabaumga/karteikarten/commit/40c09154bdd88d659f5087ffc8125f0f1e23f90d))


## v1.2.0 (2026-08-28)

### Bug Fixes

- **deps**: Dependabot-Gruppierung nach update-type
  ([`2c81280`](https://github.com/mabaumga/karteikarten/commit/2c81280409318d6fd73483502113db530d2690ac))

- **lint**: 16 Lint-Befunde bereinigt, ruff check ins Quality-Gate
  ([#9](https://github.com/mabaumga/karteikarten/pull/9),
  [`3885f63`](https://github.com/mabaumga/karteikarten/commit/3885f63d981555b735910fc9e46ab98ae93c97e3))

- **lint**: Ruff-Regelsatz explizit festschreiben + ruff/pytest aktualisieren
  ([`1348f49`](https://github.com/mabaumga/karteikarten/commit/1348f497027d6cebe9e23aad763d9d943f201e91))

### Chores

- **app-info**: Typ + lifecycle gem. Standards-Review 2026-08
  ([`2b1b412`](https://github.com/mabaumga/karteikarten/commit/2b1b4120b86bb730d1725581a7ee9ee3a4ec7713))

- **deps**: Bump actions/checkout from 4 to 7
  ([`0d32867`](https://github.com/mabaumga/karteikarten/commit/0d32867642f91a54903808d071ae20ec56800809))

- **deps**: Bump actions/setup-python from 5 to 7
  ([`fc31902`](https://github.com/mabaumga/karteikarten/commit/fc31902a528ca8e2b54e7182eec2c965d98106ca))

- **deps**: Bump docker/build-push-action from 6 to 7
  ([`5ea4cfd`](https://github.com/mabaumga/karteikarten/commit/5ea4cfd8bbf0d51d01fcb118c1093a6dcb92d23b))

- **deps**: Bump docker/login-action from 3 to 4
  ([`0abd3cc`](https://github.com/mabaumga/karteikarten/commit/0abd3cc4ce7f72d8f7595e53078f4a626f1c90c5))

- **deps**: Bump python from 3.12-slim to 3.14-slim
  ([`c3d3968`](https://github.com/mabaumga/karteikarten/commit/c3d3968a3e9aea3d9049a3c9aa3aba158c012298))

- **deps**: Bump sqlparse from 0.5.5 to 0.6.0
  ([#25](https://github.com/mabaumga/karteikarten/pull/25),
  [`34e4269`](https://github.com/mabaumga/karteikarten/commit/34e42692b1a69f1be67272b3f393fe5cb349ba5b))

- **deps**: Bump the python-deps-minor-patch group across 1 directory with 2 updates
  ([#29](https://github.com/mabaumga/karteikarten/pull/29),
  [`fadd3ef`](https://github.com/mabaumga/karteikarten/commit/fadd3ef062f6c4e61a61c6eaaba8f406a1bd8640))

- **deps**: Bump the python-deps-minor-patch group across 1 directory with 2 updates
  ([`e5bf0fc`](https://github.com/mabaumga/karteikarten/commit/e5bf0fc8a72a69603ee5a3a6a0070c47c0a9f627))

- **deps**: Bump the python-deps-minor-patch group across 1 directory with 5 updates
  ([#26](https://github.com/mabaumga/karteikarten/pull/26),
  [`3a5c917`](https://github.com/mabaumga/karteikarten/commit/3a5c9178db55c792a35738464c6dd0666de7fe95))

- **deps**: Dependabot statt dependency-check-Eigenbau (Standards-Review 2026-08 §9)
  ([`1365ec5`](https://github.com/mabaumga/karteikarten/commit/1365ec532d2b5cedc1cd021989d9f3667c2601f7))

- **gate**: Ruff flottenweit auf 0.16.4 konsolidieren
  ([#30](https://github.com/mabaumga/karteikarten/pull/30),
  [`b1260b6`](https://github.com/mabaumga/karteikarten/commit/b1260b67d720438c72d06949ad8200654d57487b))

- **hooks**: Pre-commit-hooks auf v6.0.0 ([#31](https://github.com/mabaumga/karteikarten/pull/31),
  [`3b5b498`](https://github.com/mabaumga/karteikarten/commit/3b5b498a6c9e12dc8d009111e7290d0ffeac452d))

- **qualitaet**: Pruefung beim Commit und beim Push
  ([#28](https://github.com/mabaumga/karteikarten/pull/28),
  [`09ab4fe`](https://github.com/mabaumga/karteikarten/commit/09ab4feebfcc1a3edd4fe025bcc5c8f4d5371f4b))

- **security**: Gitleaks als Pre-Commit-Hook, .env-Varianten gesperrt
  ([#32](https://github.com/mabaumga/karteikarten/pull/32),
  [`be9e0bb`](https://github.com/mabaumga/karteikarten/commit/be9e0bbaf89a3286ae158208ae75ba6db886d588))

### Code Style

- Repo mit ruff formatieren + Format-Pruefung ins Gate
  ([#10](https://github.com/mabaumga/karteikarten/pull/10),
  [`0faadf9`](https://github.com/mabaumga/karteikarten/commit/0faadf928c4b8db6591f52f15d13ef4edee24cc8))

### Documentation

- README ergaenzen ([#36](https://github.com/mabaumga/karteikarten/pull/36),
  [`9273880`](https://github.com/mabaumga/karteikarten/commit/92738806aea028d146053a95d1576b380b20d13f))

- **changelog**: Einfuegemarke fuer semantic-release ergaenzen
  ([#39](https://github.com/mabaumga/karteikarten/pull/39),
  [`c08e3f4`](https://github.com/mabaumga/karteikarten/commit/c08e3f49b0ded0dfe652ef72f26ebebb5c71868a))

### Features

- **dashboard**: Lernbloecke nach Schulfach filtern
  ([#38](https://github.com/mabaumga/karteikarten/pull/38),
  [`613f22c`](https://github.com/mabaumga/karteikarten/commit/613f22c0cd56b74c3b4a58b0f273f29759f8f037))

- **lernen**: Karten fuer eine Lernsitzung abwaehlen
  ([#37](https://github.com/mabaumga/karteikarten/pull/37),
  [`2a11857`](https://github.com/mabaumga/karteikarten/commit/2a118575da06b4eb8489610c3e94872900bb4692))

- **release**: Release-dry-run ergaenzt ([#8](https://github.com/mabaumga/karteikarten/pull/8),
  [`f3aa901`](https://github.com/mabaumga/karteikarten/commit/f3aa901ae38406f04bf8f8f31b2be68f5d0ae887))

- **tests**: Testinfrastruktur + erste Tests fuer den Health-Report
  ([#9](https://github.com/mabaumga/karteikarten/pull/9),
  [`3885f63`](https://github.com/mabaumga/karteikarten/commit/3885f63d981555b735910fc9e46ab98ae93c97e3))

- **tests**: Testinfrastruktur, erste Tests und Lint-Bereinigung
  ([#9](https://github.com/mabaumga/karteikarten/pull/9),
  [`3885f63`](https://github.com/mabaumga/karteikarten/commit/3885f63d981555b735910fc9e46ab98ae93c97e3))


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
