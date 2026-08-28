"""Tests fuer die Fortschritts-Auswertung.

Die interessante Zahl ist die Erstversuchsquote: die laufende Erfolgsquote steigt
zwangslaeufig, weil jede Karte so lange wiederkommt, bis sie sitzt. Genau diese
Unterscheidung sichern die Tests hier ab.
"""

from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from karteikarten.models import (
    BenutzerKarteStatus,
    Karteikarte,
    Lernblock,
    Lernergebnis,
    TagesStatistik,
)
from karteikarten.services.statistik import block_fortschritt, gesamt_fortschritt


@pytest.fixture
def benutzer(db):
    return User.objects.create_user(username="lina", password="geheim123")


@pytest.fixture
def block(db):
    lernblock = Lernblock.objects.create(name="Unit 4")
    for i in range(1, 5):
        Karteikarte.objects.create(
            lernblock=lernblock, begriff=f"wort {i}", definition=f"Wort {i}"
        )
    return lernblock


def _antwort(benutzer, karte, richtig, vor_minuten=0):
    ergebnis = Lernergebnis.objects.create(
        benutzer=benutzer, karte=karte, modus="klassisch", richtig=richtig
    )
    if vor_minuten:
        Lernergebnis.objects.filter(pk=ergebnis.pk).update(
            zeitstempel=timezone.now() - timedelta(minutes=vor_minuten)
        )
    return ergebnis


# --- Erstversuch -------------------------------------------------------------------


def test_spaetere_wiederholung_verbessert_den_erstversuch_nicht(benutzer, block):
    karte = block.karten.first()
    _antwort(benutzer, karte, richtig=False, vor_minuten=10)
    _antwort(benutzer, karte, richtig=True)
    _antwort(benutzer, karte, richtig=True)

    auswertung = block_fortschritt(benutzer, block)

    assert auswertung["erstversuch_gesamt"] == 1
    assert auswertung["erstversuch_richtig"] == 0
    assert auswertung["erstversuch_quote"] == 0


def test_erstversuch_zaehlt_nur_beantwortete_karten(benutzer, block):
    karten = list(block.karten.all())
    _antwort(benutzer, karten[0], richtig=True)
    _antwort(benutzer, karten[1], richtig=False)

    auswertung = block_fortschritt(benutzer, block)

    assert auswertung["erstversuch_gesamt"] == 2
    assert auswertung["erstversuch_quote"] == 50
    assert auswertung["anzahl_karten"] == 4


def test_ohne_antworten_bleibt_die_quote_null(benutzer, block):
    auswertung = block_fortschritt(benutzer, block)

    assert auswertung["erstversuch_gesamt"] == 0
    assert auswertung["erstversuch_quote"] == 0


def test_fremde_antworten_zaehlen_nicht(benutzer, block, db):
    fremder = User.objects.create_user(username="max", password="geheim123")
    _antwort(fremder, block.karten.first(), richtig=True)

    auswertung = block_fortschritt(benutzer, block)

    assert auswertung["erstversuch_gesamt"] == 0


# --- Kartenzustand -----------------------------------------------------------------


def test_angezeigte_aber_unbeantwortete_karte_gilt_als_nie_geuebt(benutzer, block):
    """Ein Status entsteht schon beim Anzeigen — das ist noch kein Ueben."""
    karte = block.karten.first()
    BenutzerKarteStatus.get_or_create_for_user(benutzer, karte)

    auswertung = block_fortschritt(benutzer, block)

    assert auswertung["nie_geuebt"] == 4
    assert auswertung["in_arbeit"] == 0


def test_kartenzustand_trennt_sitzt_und_in_arbeit(benutzer, block):
    karten = list(block.karten.all())

    status = BenutzerKarteStatus.get_or_create_for_user(benutzer, karten[0])
    status.fach = 5
    status.save()
    _antwort(benutzer, karten[0], richtig=True)

    status = BenutzerKarteStatus.get_or_create_for_user(benutzer, karten[1])
    status.fach = 2
    status.save()
    _antwort(benutzer, karten[1], richtig=True)

    auswertung = block_fortschritt(benutzer, block)

    assert auswertung["sitzt"] == 1
    assert auswertung["in_arbeit"] == 1
    assert auswertung["nie_geuebt"] == 2


# --- Problemkarten und Verlauf ------------------------------------------------------


def test_problemkarten_stehen_nach_haeufigkeit(benutzer, block):
    karten = list(block.karten.all())
    for _ in range(3):
        _antwort(benutzer, karten[0], richtig=False)
    _antwort(benutzer, karten[1], richtig=False)
    _antwort(benutzer, karten[2], richtig=True)

    problem = block_fortschritt(benutzer, block)["problemkarten"]

    assert [eintrag["karte"].pk for eintrag in problem] == [karten[0].pk, karten[1].pk]
    assert problem[0]["falsch"] == 3


def test_verlauf_deckt_sieben_tage_ab_und_fuellt_luecken(benutzer, block):
    TagesStatistik.objects.create(
        benutzer=benutzer,
        lernblock=block,
        datum=date.today(),
        gelernt=10,
        richtig=8,
        falsch=2,
    )

    verlauf = block_fortschritt(benutzer, block)["verlauf"]

    assert len(verlauf) == 7
    assert verlauf[-1]["datum"] == date.today()
    assert verlauf[-1]["gelernt"] == 10
    assert verlauf[-1]["anteil_richtig"] == 80
    assert verlauf[0]["gelernt"] == 0


# --- Zusammenfassung ueber mehrere Bloecke -----------------------------------------


def test_gesamt_summiert_ueber_bloecke(benutzer, block, db):
    zweiter = Lernblock.objects.create(name="Unit 5")
    karte = Karteikarte.objects.create(
        lernblock=zweiter, begriff="dog", definition="Hund"
    )
    _antwort(benutzer, block.karten.first(), richtig=True)
    _antwort(benutzer, karte, richtig=False)

    auswertung = gesamt_fortschritt(benutzer, [block, zweiter])

    assert auswertung["anzahl_karten"] == 5
    assert auswertung["erstversuch_gesamt"] == 2
    assert auswertung["erstversuch_quote"] == 50
    assert len(auswertung["bloecke"]) == 2
