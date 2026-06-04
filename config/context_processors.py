"""Context-Processor fuer die Versionsanzeige.

Single Source of Truth ist ``karteikarten.__version__``. Optional ergaenzt um
Build-Metadaten aus ``BASE_DIR/.build_info`` (eine Zeile ``<commit> <iso-timestamp>``),
die der Docker-Build schreiben kann.

Verwendung im base.html (Footer):

    <span class="text-muted small">v{{ app_version }}</span>
"""

from __future__ import annotations

from django.conf import settings

from karteikarten import __version__


def _read_build_info() -> tuple[str | None, str | None]:
    path = settings.BASE_DIR / ".build_info"
    try:
        commit, _, build_time = path.read_text(encoding="utf-8").strip().partition(" ")
        return (commit or None), (build_time or None)
    except OSError:
        return None, None


def version_context(request) -> dict:
    commit, build_time = _read_build_info()
    return {
        "app_version": __version__,
        "build_commit": commit,
        "build_time": build_time,
    }
