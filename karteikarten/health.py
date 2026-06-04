"""Health-Domain: Status-Werte, Check-Ergebnis und Aggregation.

Framework-neutral (keine Django-Importe) — dadurch testbar und wiederverwendbar.
Konkrete Checks siehe ``checks.py``, der Endpoint ``health_views.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class HealthStatus(str, Enum):
    """Moegliche Zustaende. Reihenfolge = Schweregrad (aufsteigend)."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


_SEVERITY = {HealthStatus.HEALTHY: 0, HealthStatus.DEGRADED: 1, HealthStatus.UNHEALTHY: 2}


@dataclass
class CheckResult:
    """Ergebnis eines einzelnen Checks."""

    name: str
    status: HealthStatus
    details: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"status": self.status.value, **self.details}


class HealthCheck:
    """Basisklasse fuer einen Check. ``run()`` ueberschreiben.

    ``critical=True`` (Default): Ausfall macht das Gesamtsystem ``unhealthy``.
    ``critical=False``: Ausfall macht es nur ``degraded`` (optionale Abhaengigkeit).
    """

    name = "check"
    critical = True

    def run(self) -> CheckResult:  # pragma: no cover - Schnittstelle
        raise NotImplementedError

    def safe_run(self) -> CheckResult:
        """``run()`` ausfuehren und Exceptions in ein Ergebnis uebersetzen."""
        try:
            return self.run()
        except Exception as exc:  # noqa: BLE001 - Health darf nie selbst crashen
            status = HealthStatus.UNHEALTHY if self.critical else HealthStatus.DEGRADED
            return CheckResult(self.name, status, {"details": f"Fehler: {exc}"})


def aggregate(results: list[CheckResult]) -> HealthStatus:
    """Gesamtstatus = schlechtester Einzelstatus."""
    if not results:
        return HealthStatus.HEALTHY
    return max((r.status for r in results), key=lambda s: _SEVERITY[s])


def build_report(results: list[CheckResult], version: str) -> tuple[dict, int]:
    """Health-Report nach Contract bauen. Gibt (json_dict, http_status) zurueck."""
    overall = aggregate(results)
    report = {
        "status": overall.value,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {r.name: r.as_dict() for r in results},
    }
    http_status = 503 if overall is HealthStatus.UNHEALTHY else 200
    return report, http_status
