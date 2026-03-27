"""URL configuration for Karteikarten app."""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='karteikarten/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # User profile and block selection
    path('profil/', views.profil, name='profil'),
    path('meine-lernbloecke/', views.meine_lernbloecke, name='meine_lernbloecke'),
    path('lernblock/<int:pk>/hinzufuegen/', views.lernblock_hinzufuegen, name='lernblock_hinzufuegen'),
    path('lernblock/<int:pk>/entfernen/', views.lernblock_entfernen, name='lernblock_entfernen'),

    # Lernblock CRUD
    path('lernblock/neu/', views.lernblock_create, name='lernblock_create'),
    path('lernblock/<int:pk>/', views.lernblock_detail, name='lernblock_detail'),
    path('lernblock/<int:pk>/bearbeiten/', views.lernblock_edit, name='lernblock_edit'),
    path('lernblock/<int:pk>/loeschen/', views.lernblock_delete, name='lernblock_delete'),

    # Karten
    path('lernblock/<int:pk>/karten/', views.karten_liste, name='karten_liste'),
    path('lernblock/<int:pk>/karten/neu/', views.karte_create, name='karte_create'),
    path('lernblock/<int:pk>/karten/import/', views.csv_import, name='csv_import'),
    path('karte/<int:pk>/bearbeiten/', views.karte_edit, name='karte_edit'),
    path('karte/<int:pk>/loeschen/', views.karte_delete, name='karte_delete'),

    # Learning modes
    path('lernblock/<int:pk>/lernen/klassisch/', views.lernen_klassisch, name='lernen_klassisch'),
    path('lernblock/<int:pk>/lernen/rueckwaerts/', views.lernen_rueckwaerts, name='lernen_rueckwaerts'),
    path('lernblock/<int:pk>/lernen/multiple-choice/', views.lernen_multiple_choice, name='lernen_multiple_choice'),
    path('lernblock/<int:pk>/lernen/zuruecksetzen/', views.karten_zuruecksetzen, name='karten_zuruecksetzen'),

    # Combined learning (multiple blocks)
    path('lernen/kombiniert/auswahl/', views.lernen_kombiniert_auswahl, name='lernen_kombiniert_auswahl'),
    path('lernen/kombiniert/', views.lernen_kombiniert, name='lernen_kombiniert'),
    path('lernen/kombiniert/multiple-choice/', views.lernen_kombiniert_mc, name='lernen_kombiniert_mc'),
    path('lernen/kombiniert/zuruecksetzen/', views.karten_zuruecksetzen_kombiniert, name='karten_zuruecksetzen_kombiniert'),

    # API
    path('api/karte/<int:pk>/antwort/', views.karte_antwort, name='karte_antwort'),
    path('api/sync/pull/', views.sync_pull, name='sync_pull'),
    path('api/sync/push/', views.sync_push, name='sync_push'),

    # PWA
    path('manifest.json', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('js/db.js', views.js_db, name='js_db'),
    path('js/sync.js', views.js_sync, name='js_sync'),
    path('js/offline-learning.js', views.js_offline_learning, name='js_offline_learning'),

    # Offline Learning
    path('lernen/offline/', views.lernen_offline, name='lernen_offline'),

    # Admin: User Management
    path('admin-benutzer/', views.benutzer_liste, name='benutzer_liste'),
    path('admin-benutzer/neu/', views.benutzer_erstellen, name='benutzer_erstellen'),
    path('admin-benutzer/<int:pk>/bearbeiten/', views.benutzer_bearbeiten, name='benutzer_bearbeiten'),
    path('admin-benutzer/<int:pk>/loeschen/', views.benutzer_loeschen, name='benutzer_loeschen'),

    # Password
    path('passwort-aendern/', views.passwort_aendern, name='passwort_aendern'),

    # Backup
    path('admin-backup/', views.backup_liste, name='backup_liste'),
    path('admin-backup/erstellen/', views.backup_erstellen, name='backup_erstellen'),
    path('admin-backup/download/<str:filename>/', views.backup_download, name='backup_download'),
]
