"""Context-Processor fuer Versionsanzeige und Navigation.

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


# Welcher der vier Reiter gehoert zu welcher Seite. Die Zuordnung liegt hier und
# nicht in den Views: sonst muesste jede einzelne View einen Wert mitschleppen,
# den nur das Basis-Template braucht.
_REITER_JE_SEITE = {
    "start": {"dashboard"},
    "bloecke": {
        "meine_lernbloecke",
        "lernblock_detail",
        "lernblock_create",
        "lernblock_edit",
        "karten_liste",
        "karte_create",
        "karte_edit",
        "csv_import",
        "kartenauswahl",
        "modus_waehlen",
        "lernen_kombiniert_auswahl",
        "test_liste",
        "test_create",
        "test_detail",
        "test_edit",
    },
    "fortschritt": {"fortschritt", "lernblock_fortschritt", "test_fortschritt"},
    "mehr": {
        "mehr",
        "profil",
        "passwort_aendern",
        "lernen_offline",
        "benutzer_liste",
        "benutzer_erstellen",
        "benutzer_bearbeiten",
        "backup_liste",
        "buecher",
        "buch_create",
        "buch_detail",
        "buch_edit",
        "kapitel_create",
        "kapitel_edit",
    },
}

_REITER_JE_URL = {
    url_name: reiter
    for reiter, url_names in _REITER_JE_SEITE.items()
    for url_name in url_names
}


def navigation_context(request) -> dict:
    """Markiert den Reiter, der zur aktuellen Seite gehoert.

    Ohne Treffer bleibt der Wert leer — Lernansichten blenden die Navigation
    ohnehin aus, dort waere jede Markierung falsch.
    """
    treffer = getattr(request, "resolver_match", None)
    url_name = treffer.url_name if treffer else None
    return {"aktiver_reiter": _REITER_JE_URL.get(url_name, "")}
