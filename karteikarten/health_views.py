"""Oeffentlicher Health-Endpoint ``/health/`` (JSON, ohne Auth) fuer Docker + Uptime Kuma.

Liefert den Health-Contract: status / version / timestamp / checks.
HTTP 200 bei healthy/degraded, 503 bei unhealthy. Keine Secrets/Details nach aussen.
"""

from __future__ import annotations

from django.http import JsonResponse

from . import __version__
from .checks import liveness_checks
from .health import build_report


def health(request) -> JsonResponse:
    results = [check.safe_run() for check in liveness_checks()]
    report, http_status = build_report(results, __version__)
    return JsonResponse(report, status=http_status)
