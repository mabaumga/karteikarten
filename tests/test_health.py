"""Tests fuer den Health-Report (Contract + ``degraded_checks``).

Diese Datei ist der erste Test des Repos. Sie deckt bewusst den Health-Report ab: Er wird
von aussen konsumiert (Docker-HEALTHCHECK, Uptime Kuma) und ist damit die Stelle, an der
eine stille Aenderung am meisten anrichtet.

Framework-neutral — ``build_report``/``aggregate`` brauchen weder DB noch Django-Request.
"""

from karteikarten.health import CheckResult, HealthStatus, aggregate, build_report


def _report(*results: CheckResult) -> dict:
    report, _http = build_report(list(results), version="1.0.0")
    return report


# --- Aggregation: Gesamtstatus ist der schlechteste Einzelstatus ---------------------


def test_ohne_checks_gilt_als_gesund():
    assert aggregate([]) is HealthStatus.HEALTHY


def test_degraded_schlaegt_healthy():
    assert (
        aggregate(
            [
                CheckResult("datenbank", HealthStatus.HEALTHY),
                CheckResult("speicher", HealthStatus.DEGRADED),
            ]
        )
        is HealthStatus.DEGRADED
    )


def test_unhealthy_schlaegt_degraded():
    assert (
        aggregate(
            [
                CheckResult("datenbank", HealthStatus.UNHEALTHY),
                CheckResult("speicher", HealthStatus.DEGRADED),
            ]
        )
        is HealthStatus.UNHEALTHY
    )


# --- degraded_checks: nennt den betroffenen Check in der Kuma-Meldung ----------------


def test_bei_gesundheit_bindestrich():
    """Kuma wertet null/undefined als Fehler — "-" statt leer, sonst wird der Monitor
    ausgerechnet dann rot, wenn alles in Ordnung ist."""
    report = _report(
        CheckResult("datenbank", HealthStatus.HEALTHY),
        CheckResult("speicher", HealthStatus.HEALTHY),
    )
    assert report["degraded_checks"] == "-"
    assert report["status"] == "healthy"


def test_nennt_betroffenen_check():
    report = _report(
        CheckResult("datenbank", HealthStatus.HEALTHY),
        CheckResult("speicher", HealthStatus.DEGRADED),
    )
    assert report["degraded_checks"] == "speicher"


def test_kommasepariert_und_inklusive_unhealthy():
    """Jeder Status ausser healthy zaehlt hinein, nicht nur degraded."""
    report = _report(
        CheckResult("datenbank", HealthStatus.UNHEALTHY),
        CheckResult("speicher", HealthStatus.DEGRADED),
    )
    assert report["degraded_checks"] == "datenbank, speicher"


# --- HTTP-Codes: degraded bleibt bewusst 200 ----------------------------------------


def test_degraded_bleibt_http_200():
    """Sonst faerbt eine blosse Warnung den Verfuegbarkeits-Monitor rot."""
    _report_dict, http = build_report(
        [CheckResult("speicher", HealthStatus.DEGRADED)], version="1.0.0"
    )
    assert http == 200


def test_unhealthy_ist_http_503():
    _report_dict, http = build_report(
        [CheckResult("datenbank", HealthStatus.UNHEALTHY)], version="1.0.0"
    )
    assert http == 503


def test_report_traegt_die_contract_felder():
    report = _report(CheckResult("datenbank", HealthStatus.HEALTHY))
    assert set(report) >= {
        "status",
        "degraded_checks",
        "version",
        "timestamp",
        "checks",
    }
    assert report["version"] == "1.0.0"
