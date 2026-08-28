"""Tests fuer den Tippmodus.

Der Modus verlangt die Antwort als Eingabe statt als Selbsteinschaetzung. Geprueft
wird hier das Zusammenspiel: was gefragt wird, was als richtig durchgeht und dass
das Leitner-Fach dabei genauso weiterzaehlt wie in den anderen Modi.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from karteikarten.models import (
    BenutzerKarteStatus,
    BenutzerLernblock,
    Karteikarte,
    Lernblock,
    Lernergebnis,
)


@pytest.fixture
def benutzer(db):
    return User.objects.create_user(username="schueler", password="geheim123")


@pytest.fixture
def block(db):
    lernblock = Lernblock.objects.create(name="Unit 1", bidirektional=True)
    Karteikarte.objects.create(
        lernblock=lernblock, begriff="le chien", definition="der Hund"
    )
    return lernblock


@pytest.fixture
def karte(block):
    return block.karten.get()


@pytest.fixture
def angemeldet(client, benutzer):
    client.force_login(benutzer)
    return client


def _tippen(client, karte, eingabe, richtung=""):
    return client.post(
        reverse("karte_tippen_antwort", args=[karte.pk]),
        {"eingabe": eingabe, "richtung": richtung},
    ).json()


# --- Was gefragt wird --------------------------------------------------------------


def test_vorwaerts_wird_die_rueckseite_gefragt(angemeldet, block, karte):
    antwort = angemeldet.get(reverse("lernen_tippen", args=[block.pk]))

    assert antwort.context["frage"] == karte.begriff
    assert antwort.context["gefragt_label"] == block.rueckseite_label


def test_rueckwaerts_wird_die_vorderseite_gefragt(angemeldet, block, karte):
    antwort = angemeldet.get(
        reverse("lernen_tippen", args=[block.pk]), {"richtung": "rueckwaerts"}
    )

    assert antwort.context["frage"] == karte.definition
    assert antwort.context["gefragt_label"] == block.vorderseite_label


def test_einseitiger_block_kennt_keine_rueckrichtung(angemeldet, block):
    block.bidirektional = False
    block.save()

    antwort = angemeldet.get(
        reverse("lernen_tippen", args=[block.pk]), {"richtung": "rueckwaerts"}
    )

    assert antwort.context["richtung"] == ""


def test_ohne_faellige_karten_ist_schluss(angemeldet, block, karte, benutzer):
    status = BenutzerKarteStatus.get_or_create_for_user(benutzer, karte)
    status.richtig_beantwortet()

    antwort = angemeldet.get(reverse("lernen_tippen", args=[block.pk]))

    assert antwort.templates[0].name == "karteikarten/lernen_fertig.html"


# --- Was als richtig durchgeht -----------------------------------------------------


def test_richtige_eingabe_zaehlt_und_stuft_hoch(angemeldet, karte, benutzer):
    daten = _tippen(angemeldet, karte, "der Hund")

    assert daten["ergebnis"] == "richtig"
    assert daten["richtig"] is True
    assert daten["loesung"] == "der Hund"
    assert BenutzerKarteStatus.get_or_create_for_user(benutzer, karte).fach == 2


def test_fast_richtige_eingabe_zaehlt_als_richtig(angemeldet, karte, benutzer):
    """Artikel vergessen — die Vokabel sass trotzdem."""
    daten = _tippen(angemeldet, karte, "Hund")

    assert daten["ergebnis"] == "fast"
    assert daten["richtig"] is True
    assert BenutzerKarteStatus.get_or_create_for_user(benutzer, karte).fach == 2


def test_falsche_eingabe_faellt_zurueck_in_fach_eins(angemeldet, karte, benutzer):
    status = BenutzerKarteStatus.get_or_create_for_user(benutzer, karte)
    status.fach = 4
    status.save()

    daten = _tippen(angemeldet, karte, "die Katze")

    assert daten["richtig"] is False
    assert daten["loesung"] == "der Hund"
    assert BenutzerKarteStatus.get_or_create_for_user(benutzer, karte).fach == 1


def test_rueckwaerts_wird_gegen_die_vorderseite_geprueft(angemeldet, karte):
    daten = _tippen(angemeldet, karte, "le chien", richtung="rueckwaerts")

    assert daten["ergebnis"] == "richtig"
    assert daten["loesung"] == "le chien"


def test_ergebnis_wird_als_tippen_verbucht(angemeldet, karte, benutzer):
    _tippen(angemeldet, karte, "der Hund")

    ergebnis = Lernergebnis.objects.get(benutzer=benutzer, karte=karte)
    assert ergebnis.modus == "tippen"
    assert ergebnis.richtig is True


# --- Kombinierter Tippmodus --------------------------------------------------------


def test_kombiniert_fragt_ueber_mehrere_bloecke(angemeldet, block, benutzer):
    zweiter = Lernblock.objects.create(name="Unit 2")
    Karteikarte.objects.create(
        lernblock=zweiter, begriff="le chat", definition="die Katze"
    )
    for lernblock in (block, zweiter):
        BenutzerLernblock.objects.create(benutzer=benutzer, lernblock=lernblock)

    antwort = angemeldet.get(
        reverse("lernen_kombiniert_tippen"),
        {"bloecke": f"{block.pk},{zweiter.pk}"},
    )

    assert antwort.context["verbleibend"] == 2
    assert antwort.context["modus"] == "tippen"


def test_kombiniert_ohne_bloecke_fuehrt_zur_auswahl(angemeldet):
    antwort = angemeldet.get(reverse("lernen_kombiniert_tippen"))

    assert antwort.status_code == 302
    assert antwort.url == reverse("lernen_kombiniert_auswahl")
