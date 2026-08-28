"""Tests fuer die temporaere Kartenauswahl ("Subblock").

Die Auswahl lebt in der Session und darf den Lernblock nicht anfassen. Genau das ist
hier abgesichert: was drankommt, was zurueckgesetzt wird, und dass eine vollstaendige
Auswahl gar keine Auswahl ist.
"""

from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from karteikarten.models import BenutzerKarteStatus, Karteikarte, Lernblock


@pytest.fixture
def benutzer(db):
    return User.objects.create_user(username="schueler", password="geheim123")


@pytest.fixture
def block(db):
    lernblock = Lernblock.objects.create(name="Unit 1")
    for i in range(1, 5):
        Karteikarte.objects.create(
            lernblock=lernblock,
            begriff=f"Begriff {i}",
            definition=f"Definition {i}",
        )
    return lernblock


@pytest.fixture
def angemeldet(client, benutzer):
    client.force_login(benutzer)
    return client


def _auswaehlen(client, block, karten):
    return client.post(
        reverse("kartenauswahl", args=[block.pk]),
        {"karten": [k.pk for k in karten]},
    )


# --- Was drankommt -----------------------------------------------------------------


def test_ohne_auswahl_kommt_der_ganze_block_dran(angemeldet, block):
    antwort = angemeldet.get(reverse("lernen_klassisch", args=[block.pk]))

    assert antwort.context["verbleibend"] == 4
    assert antwort.context["auswahl_aktiv"] is False


def test_auswahl_reduziert_die_karten(angemeldet, block):
    karten = list(block.karten.all())

    _auswaehlen(angemeldet, block, karten[:2])
    antwort = angemeldet.get(reverse("lernen_klassisch", args=[block.pk]))

    assert antwort.context["verbleibend"] == 2
    assert antwort.context["auswahl_aktiv"] is True
    assert antwort.context["auswahl_anzahl"] == 2
    assert antwort.context["karte"].pk in {karten[0].pk, karten[1].pk}


def test_auswahl_gilt_auch_rueckwaerts_und_fuer_multiple_choice(angemeldet, block):
    block.bidirektional = True
    block.save()
    karten = list(block.karten.all())

    _auswaehlen(angemeldet, block, karten[:2])

    for modus in ("lernen_rueckwaerts", "lernen_multiple_choice"):
        antwort = angemeldet.get(reverse(modus, args=[block.pk]))
        assert antwort.context["verbleibend"] == 2, modus


def test_abgewaehlte_karten_bekommen_keinen_status(angemeldet, block, benutzer):
    karten = list(block.karten.all())

    _auswaehlen(angemeldet, block, karten[:1])
    angemeldet.get(reverse("lernen_klassisch", args=[block.pk]))

    beruehrt = set(
        BenutzerKarteStatus.objects.filter(benutzer=benutzer).values_list(
            "karte_id", flat=True
        )
    )
    assert beruehrt == {karten[0].pk}


# --- Auswahl setzen, aufheben, Grenzfaelle -----------------------------------------


def test_vollstaendige_auswahl_ist_keine_auswahl(angemeldet, block):
    _auswaehlen(angemeldet, block, list(block.karten.all()))

    antwort = angemeldet.get(reverse("lernblock_detail", args=[block.pk]))
    assert antwort.context["auswahl_aktiv"] is False


def test_leere_auswahl_laesst_die_bestehende_stehen(angemeldet, block):
    karten = list(block.karten.all())
    _auswaehlen(angemeldet, block, karten[:1])

    angemeldet.post(reverse("kartenauswahl", args=[block.pk]), {"karten": []})

    antwort = angemeldet.get(reverse("lernblock_detail", args=[block.pk]))
    assert antwort.context["auswahl_aktiv"] is True
    assert antwort.context["auswahl_anzahl"] == 1


def test_auswahl_aufheben(angemeldet, block):
    karten = list(block.karten.all())
    _auswaehlen(angemeldet, block, karten[:1])

    angemeldet.post(reverse("kartenauswahl_aufheben", args=[block.pk]))

    antwort = angemeldet.get(reverse("lernblock_detail", args=[block.pk]))
    assert antwort.context["auswahl_aktiv"] is False


def test_auswahl_veraendert_den_lernblock_nicht(angemeldet, block):
    karten = list(block.karten.all())
    vorher = block.aktualisiert_am

    _auswaehlen(angemeldet, block, karten[:1])

    block.refresh_from_db()
    assert block.aktualisiert_am == vorher
    assert block.karten.count() == 4


# --- Zuruecksetzen respektiert die Auswahl -----------------------------------------


def test_zuruecksetzen_trifft_nur_die_auswahl(angemeldet, block, benutzer):
    karten = list(block.karten.all())
    spaeter = date.today() + timedelta(days=3)
    for karte in karten:
        status = BenutzerKarteStatus.get_or_create_for_user(benutzer, karte)
        status.naechste_wiederholung = spaeter
        status.save()

    _auswaehlen(angemeldet, block, karten[:1])
    angemeldet.post(
        reverse("karten_zuruecksetzen", args=[block.pk]), {"modus": "klassisch"}
    )

    def faellig_am(karte):
        return BenutzerKarteStatus.objects.get(
            benutzer=benutzer, karte=karte
        ).naechste_wiederholung

    assert faellig_am(karten[0]) == date.today()
    assert all(faellig_am(karte) == spaeter for karte in karten[1:])
