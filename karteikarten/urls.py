"""URL configuration for Karteikarten app."""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="karteikarten/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    # Reiter der Hauptnavigation
    path("fortschritt/", views.fortschritt, name="fortschritt"),
    path("mehr/", views.mehr, name="mehr"),
    # User profile and block selection
    path("profil/", views.profil, name="profil"),
    path("meine-lernbloecke/", views.meine_lernbloecke, name="meine_lernbloecke"),
    path(
        "meine-lernbloecke/speichern/",
        views.lernbloecke_speichern,
        name="lernbloecke_speichern",
    ),
    # Tests (frei zusammengestellte Uebungssets)
    path("tests/", views.test_liste, name="test_liste"),
    path("tests/neu/", views.test_create, name="test_create"),
    path("tests/<int:pk>/", views.test_detail, name="test_detail"),
    path("tests/<int:pk>/bearbeiten/", views.test_edit, name="test_edit"),
    path("tests/<int:pk>/loeschen/", views.test_loeschen, name="test_loeschen"),
    path("tests/<int:pk>/lernen/", views.test_lernen, name="test_lernen"),
    path(
        "tests/<int:pk>/lernen/<str:modus>/",
        views.test_lernen_modus,
        name="test_lernen_modus",
    ),
    path(
        "tests/<int:pk>/zuruecksetzen/",
        views.test_zuruecksetzen,
        name="test_zuruecksetzen",
    ),
    path(
        "tests/<int:pk>/fortschritt/", views.test_fortschritt, name="test_fortschritt"
    ),
    path(
        "tests/<int:pk>/karte/<int:karte_pk>/entfernen/",
        views.test_karte_entfernen,
        name="test_karte_entfernen",
    ),
    path(
        "lernblock/<int:pk>/in-test/",
        views.test_karten_uebernehmen,
        name="test_karten_uebernehmen",
    ),
    # Buecher und Kapitel (Verwaltung)
    path("buecher/", views.buecher, name="buecher"),
    path("buecher/neu/", views.buch_create, name="buch_create"),
    path("buecher/<int:pk>/", views.buch_detail, name="buch_detail"),
    path("buecher/<int:pk>/bearbeiten/", views.buch_edit, name="buch_edit"),
    path("buecher/<int:pk>/loeschen/", views.buch_loeschen, name="buch_loeschen"),
    path("buecher/<int:pk>/kapitel/neu/", views.kapitel_create, name="kapitel_create"),
    path("kapitel/<int:pk>/bearbeiten/", views.kapitel_edit, name="kapitel_edit"),
    path("kapitel/<int:pk>/loeschen/", views.kapitel_loeschen, name="kapitel_loeschen"),
    # Lernblock CRUD
    path("lernblock/neu/", views.lernblock_create, name="lernblock_create"),
    path("lernblock/<int:pk>/", views.lernblock_detail, name="lernblock_detail"),
    path("lernblock/<int:pk>/bearbeiten/", views.lernblock_edit, name="lernblock_edit"),
    path(
        "lernblock/<int:pk>/loeschen/", views.lernblock_delete, name="lernblock_delete"
    ),
    # Karten
    path("lernblock/<int:pk>/karten/", views.karten_liste, name="karten_liste"),
    path("lernblock/<int:pk>/karten/neu/", views.karte_create, name="karte_create"),
    path("lernblock/<int:pk>/karten/import/", views.csv_import, name="csv_import"),
    path("karte/<int:pk>/bearbeiten/", views.karte_edit, name="karte_edit"),
    path("karte/<int:pk>/loeschen/", views.karte_delete, name="karte_delete"),
    # Kartenauswahl (temporaerer Subblock)
    path("lernblock/<int:pk>/auswahl/", views.kartenauswahl, name="kartenauswahl"),
    path(
        "lernblock/<int:pk>/auswahl/aufheben/",
        views.kartenauswahl_aufheben,
        name="kartenauswahl_aufheben",
    ),
    path(
        "lernblock/<int:pk>/fortschritt/",
        views.lernblock_fortschritt,
        name="lernblock_fortschritt",
    ),
    path("lernblock/<int:pk>/modus/", views.modus_waehlen, name="modus_waehlen"),
    # Learning modes
    path(
        "lernblock/<int:pk>/lernen/",
        views.lernen_starten,
        name="lernen_starten",
    ),
    path(
        "lernblock/<int:pk>/lernen/klassisch/",
        views.lernen_klassisch,
        name="lernen_klassisch",
    ),
    path(
        "lernblock/<int:pk>/lernen/rueckwaerts/",
        views.lernen_rueckwaerts,
        name="lernen_rueckwaerts",
    ),
    path(
        "lernblock/<int:pk>/lernen/multiple-choice/",
        views.lernen_multiple_choice,
        name="lernen_multiple_choice",
    ),
    path(
        "lernblock/<int:pk>/lernen/tippen/",
        views.lernen_tippen,
        name="lernen_tippen",
    ),
    path(
        "lernblock/<int:pk>/lernen/zuruecksetzen/",
        views.karten_zuruecksetzen,
        name="karten_zuruecksetzen",
    ),
    # Combined learning (multiple blocks)
    path(
        "lernen/kombiniert/auswahl/",
        views.lernen_kombiniert_auswahl,
        name="lernen_kombiniert_auswahl",
    ),
    path("lernen/alles/", views.lernen_alles, name="lernen_alles"),
    path("lernen/kombiniert/", views.lernen_kombiniert, name="lernen_kombiniert"),
    path(
        "lernen/kombiniert/multiple-choice/",
        views.lernen_kombiniert_mc,
        name="lernen_kombiniert_mc",
    ),
    path(
        "lernen/kombiniert/tippen/",
        views.lernen_kombiniert_tippen,
        name="lernen_kombiniert_tippen",
    ),
    path(
        "lernen/kombiniert/zuruecksetzen/",
        views.karten_zuruecksetzen_kombiniert,
        name="karten_zuruecksetzen_kombiniert",
    ),
    # API
    path("api/karte/<int:pk>/antwort/", views.karte_antwort, name="karte_antwort"),
    path(
        "api/karte/<int:pk>/tippen/",
        views.karte_tippen_antwort,
        name="karte_tippen_antwort",
    ),
    path("api/sync/pull/", views.sync_pull, name="sync_pull"),
    path("api/sync/push/", views.sync_push, name="sync_push"),
    # PWA
    path("manifest.json", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("js/db.js", views.js_db, name="js_db"),
    path("js/sync.js", views.js_sync, name="js_sync"),
    path(
        "js/offline-learning.js", views.js_offline_learning, name="js_offline_learning"
    ),
    # Offline Learning
    path("lernen/offline/", views.lernen_offline, name="lernen_offline"),
    # Admin: User Management
    path("admin-benutzer/", views.benutzer_liste, name="benutzer_liste"),
    path("admin-benutzer/neu/", views.benutzer_erstellen, name="benutzer_erstellen"),
    path(
        "admin-benutzer/<int:pk>/bearbeiten/",
        views.benutzer_bearbeiten,
        name="benutzer_bearbeiten",
    ),
    path(
        "admin-benutzer/<int:pk>/loeschen/",
        views.benutzer_loeschen,
        name="benutzer_loeschen",
    ),
    # Password
    path("passwort-aendern/", views.passwort_aendern, name="passwort_aendern"),
    # Backup
    path("admin-backup/", views.backup_liste, name="backup_liste"),
    path("admin-backup/erstellen/", views.backup_erstellen, name="backup_erstellen"),
    path(
        "admin-backup/download/<str:filename>/",
        views.backup_download,
        name="backup_download",
    ),
]
