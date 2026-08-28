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
from karteikarten.services.statistik import (
    block_fortschritt,
    gegliederter_fortschritt,
    kurzfortschritt,
)


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

    auswertung = gegliederter_fortschritt(benutzer, [block, zweiter])

    assert auswertung["anzahl_karten"] == 5
    assert auswertung["erstversuch_gesamt"] == 2
    assert auswertung["erstversuch_quote"] == 50
    assert len(auswertung["bloecke"]) == 2


def test_nur_uebergebene_bloecke_zaehlen(benutzer, block, db):
    """Was der Benutzer sich nicht ausgesucht hat, taucht nirgends auf."""
    fremd = Lernblock.objects.create(name="Unit 9")
    Karteikarte.objects.create(lernblock=fremd, begriff="cat", definition="Katze")

    auswertung = gegliederter_fortschritt(benutzer, [block])

    assert auswertung["anzahl_karten"] == 4
    assert [e["lernblock"] for e in auswertung["bloecke"]] == [block]


# --- Gliederung nach Schulfach und Lehrwerk ----------------------------------------


@pytest.fixture
def lehrwerke(db):
    """Zwei Sprachen, drei Buecher — wie in einem echten Schuljahr."""
    from karteikarten.models import Lehrwerk, LehrwerkUnit, Schulfach

    englisch = Schulfach.objects.create(name="Englisch")
    franzoesisch = Schulfach.objects.create(name="Französisch")

    gebaut = {}
    for name, fach in (
        ("Camden Town 10", englisch),
        ("Green Line 2", englisch),
        ("À plus 1", franzoesisch),
    ):
        lehrwerk = Lehrwerk.objects.create(name=name, schulfach=fach)
        gebaut[name] = LehrwerkUnit.objects.create(lehrwerk=lehrwerk, name="Unit 1")
    return gebaut


def _block_mit_karten(unit, name, anzahl):
    lernblock = Lernblock.objects.create(name=name, lehrwerk_unit=unit)
    for i in range(anzahl):
        Karteikarte.objects.create(
            lernblock=lernblock, begriff=f"{name}-{i}", definition=f"Bedeutung {i}"
        )
    return lernblock


def test_quoten_je_schulfach_und_lehrwerk(benutzer, lehrwerke):
    """Genau der Fall aus der Praxis: 100 % Französisch, 50 % Englisch, 75 % gesamt."""
    franz = _block_mit_karten(lehrwerke["À plus 1"], "Unité 1", 2)
    engl = _block_mit_karten(lehrwerke["Camden Town 10"], "Wortliste 1", 2)

    for karte in franz.karten.all():
        _antwort(benutzer, karte, richtig=True)
    karten = list(engl.karten.all())
    _antwort(benutzer, karten[0], richtig=True)
    _antwort(benutzer, karten[1], richtig=False)

    auswertung = gegliederter_fortschritt(benutzer, [franz, engl])
    je_fach = {fach["name"]: fach for fach in auswertung["schulfaecher"]}

    assert auswertung["erstversuch_quote"] == 75
    assert je_fach["Französisch"]["erstversuch_quote"] == 100
    assert je_fach["Englisch"]["erstversuch_quote"] == 50


def test_mehrere_lehrwerke_eines_fachs_bleiben_getrennt(benutzer, lehrwerke):
    camden = _block_mit_karten(lehrwerke["Camden Town 10"], "Wortliste 1", 2)
    green = _block_mit_karten(lehrwerke["Green Line 2"], "Unit 1", 2)

    for karte in camden.karten.all():
        _antwort(benutzer, karte, richtig=True)
    for karte in green.karten.all():
        _antwort(benutzer, karte, richtig=False)

    auswertung = gegliederter_fortschritt(benutzer, [camden, green])
    englisch = auswertung["schulfaecher"][0]
    je_buch = {buch["name"]: buch for buch in englisch["lehrwerke"]}

    assert englisch["name"] == "Englisch"
    assert len(englisch["lehrwerke"]) == 2
    assert je_buch["Camden Town 10"]["erstversuch_quote"] == 100
    assert je_buch["Green Line 2"]["erstversuch_quote"] == 0


def test_bloecke_ohne_lehrwerk_bekommen_eigene_gruppen(benutzer, block):
    auswertung = gegliederter_fortschritt(benutzer, [block])

    fach = auswertung["schulfaecher"][0]
    assert fach["name"] == "Ohne Schulfach"
    assert fach["lehrwerke"][0]["name"] == "Ohne Lehrwerk"
    assert fach["lehrwerke"][0]["bloecke"][0]["lernblock"] == block


# --- Kurzfortschritt fuer die Abfrage ----------------------------------------------


def test_kurzfortschritt_zaehlt_die_sicheren_karten(benutzer, block):
    karten = list(block.karten.all())
    for karte in karten[:1]:
        status = BenutzerKarteStatus.get_or_create_for_user(benutzer, karte)
        status.fach = 5
        status.save()

    kurz = kurzfortschritt(benutzer, block)

    assert kurz["sitzt"] == 1
    assert kurz["anzahl"] == 4
    assert kurz["prozent"] == 25


def test_kurzfortschritt_ohne_karten_bleibt_bei_null(benutzer, db):
    leer = Lernblock.objects.create(name="Leer")

    kurz = kurzfortschritt(benutzer, leer)

    assert kurz == {"lernblock": leer, "sitzt": 0, "anzahl": 0, "prozent": 0}
