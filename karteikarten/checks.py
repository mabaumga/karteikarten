"""Konkrete Liveness-Checks fuer den oeffentlichen ``/health/``-Poll.

Nur lokale, schnelle Pflicht-Checks — laufen ohne Auth im Docker/Kuma-Poll.
Keine externen Integrationen (die App hat keine).

Geprueft wird die **Datenbank**. Sie *ist* eine Eigenschaft der Anwendung: Die App
hat ihre eigene, und ohne sie kann sie nicht arbeiten.

Der **Plattenplatz gehoert nicht dazu** (INFRA-249). Er ist eine Eigenschaft des
Hosts: Auf hetzner-web liegen fuenfzehn Stacks auf derselben Platte, und am
02.09.2026 meldeten deswegen acht Dienste gleichzeitig ``degraded`` — acht Alarme
fuer eine Tatsache, gegen die keine der acht etwas tun konnte. Geprueft wird der
Host jetzt einmal, in ``check_disk.sh``.

``DiskSpaceCheck`` bleibt trotzdem hier: Liegen die Daten einmal auf einem eigenen
Datentraeger, wird die Pruefung mit dessen Pfad wieder eingehaengt.
"""

from __future__ import annotations

import shutil
from typing import Any

from django.conf import settings
from django.db import connections

from .health import CheckResult, HealthCheck, HealthStatus


class DatabaseCheck(HealthCheck):
    """Prueft die Standard-Datenbankverbindung mit ``SELECT 1``."""

    name = "datenbank"
    critical = True

    def __init__(self, alias: str = "default") -> None:
        self.alias = alias

    def run(self) -> CheckResult:
        with connections[self.alias].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return CheckResult(
            self.name, HealthStatus.HEALTHY, {"details": "Verbindung erfolgreich"}
        )


class DiskSpaceCheck(HealthCheck):
    """Freier Plattenplatz (degraded ab ``warn_pct``, unhealthy ab ``crit_pct``).

    Seit INFRA-249 **nicht mehr Teil von** ``liveness_checks()`` — siehe Modul-Kopf.
    """

    name = "speicher"
    critical = True

    def __init__(
        self, path: Any = None, warn_pct: int = 80, crit_pct: int = 95
    ) -> None:
        self.path = path or getattr(settings, "DATA_DIR", settings.BASE_DIR)
        self.warn_pct = warn_pct
        self.crit_pct = crit_pct

    def run(self) -> CheckResult:
        usage = shutil.disk_usage(self.path)
        belegt_pct = usage.used / usage.total * 100
        if belegt_pct >= self.crit_pct:
            status = HealthStatus.UNHEALTHY
        elif belegt_pct >= self.warn_pct:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        return CheckResult(
            self.name,
            status,
            {
                "frei_gb": round(usage.free / 1024**3, 1),
                "gesamt_gb": round(usage.total / 1024**3, 1),
                "belegt_pct": round(belegt_pct, 1),
            },
        )


def liveness_checks() -> list[HealthCheck]:
    """Oeffentlicher Health-Poll: nur lokal und schnell."""
    return [DatabaseCheck()]
