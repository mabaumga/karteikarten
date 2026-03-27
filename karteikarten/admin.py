"""Admin configuration for Karteikarten."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Schulfach, Jahrgangsstufe, Lernblock, Karteikarte,
    BenutzerLernblock, BenutzerKarteStatus, BenutzerStatistik,
    Lernergebnis, TagesStatistik
)


@admin.register(Schulfach)
class SchulfachAdmin(admin.ModelAdmin):
    list_display = ['name', 'beschreibung']
    search_fields = ['name']


@admin.register(Jahrgangsstufe)
class JahrgangsstufeAdmin(admin.ModelAdmin):
    list_display = ['stufe', 'bezeichnung']
    ordering = ['stufe']


@admin.register(Lernblock)
class LernblockAdmin(admin.ModelAdmin):
    list_display = ['name', 'schulfach', 'jahrgangsstufe', 'thema', 'bidirektional', 'anzahl_karten']
    list_filter = ['schulfach', 'jahrgangsstufe', 'thema', 'bidirektional']
    search_fields = ['name', 'beschreibung', 'thema']

    def anzahl_karten(self, obj):
        return obj.anzahl_karten
    anzahl_karten.short_description = 'Karten'


@admin.register(Karteikarte)
class KarteikarteAdmin(admin.ModelAdmin):
    list_display = ['begriff', 'lernblock', 'fach', 'naechste_wiederholung']
    list_filter = ['lernblock', 'fach']
    search_fields = ['begriff', 'definition']
    raw_id_fields = ['lernblock']


# =============================================================================
# User-related admin
# =============================================================================

class BenutzerLernblockInline(admin.TabularInline):
    """Inline for user's learning blocks."""
    model = BenutzerLernblock
    extra = 1
    autocomplete_fields = ['lernblock']


class BenutzerStatistikInline(admin.StackedInline):
    """Inline for user statistics."""
    model = BenutzerStatistik
    can_delete = False


# Extend the default User admin
class CustomUserAdmin(UserAdmin):
    """Extended User admin with learning data."""
    inlines = [BenutzerStatistikInline, BenutzerLernblockInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'lernblock_count']

    def lernblock_count(self, obj):
        return obj.lernbloecke.count()
    lernblock_count.short_description = 'Lernblöcke'


# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(BenutzerLernblock)
class BenutzerLernblockAdmin(admin.ModelAdmin):
    list_display = ['benutzer', 'lernblock', 'hinzugefuegt_am']
    list_filter = ['benutzer', 'lernblock']
    autocomplete_fields = ['benutzer', 'lernblock']


@admin.register(BenutzerKarteStatus)
class BenutzerKarteStatusAdmin(admin.ModelAdmin):
    list_display = ['benutzer', 'karte', 'fach', 'naechste_wiederholung']
    list_filter = ['benutzer', 'fach']
    search_fields = ['karte__begriff']
    raw_id_fields = ['benutzer', 'karte']


@admin.register(BenutzerStatistik)
class BenutzerStatistikAdmin(admin.ModelAdmin):
    list_display = ['benutzer', 'streak', 'letzter_lerntag', 'gesamt_gelernt', 'gesamt_richtig', 'erfolgsquote']
    list_filter = ['letzter_lerntag']

    def erfolgsquote(self, obj):
        return f"{obj.erfolgsquote}%"
    erfolgsquote.short_description = 'Erfolgsquote'


@admin.register(Lernergebnis)
class LernergebnisAdmin(admin.ModelAdmin):
    list_display = ['benutzer', 'karte', 'modus', 'richtig', 'zeitstempel']
    list_filter = ['benutzer', 'modus', 'richtig', 'zeitstempel']
    date_hierarchy = 'zeitstempel'


@admin.register(TagesStatistik)
class TagesStatistikAdmin(admin.ModelAdmin):
    list_display = ['benutzer', 'lernblock', 'datum', 'gelernt', 'richtig', 'falsch', 'erfolgsquote']
    list_filter = ['benutzer', 'lernblock', 'datum']
    date_hierarchy = 'datum'
