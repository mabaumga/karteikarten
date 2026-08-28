"""Tests fuer die Neustrukturierung.

Abgesichert ist, was den Umbau ausmacht: ein Weg ins Lernen statt vier Kacheln,
der Modus als Einstellung statt als Weg, Verwaltung ausserhalb des Lernwegs und
ein Reiter, der zur Seite passt.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from karteikarten.models import (
    BenutzerLernblock,
    BenutzerStatistik,
    Karteikarte,
    Lernblock,
)


@pytest.fixture
def schueler(db):
    return User.objects.create_user(username="lina", password="geheim123")


@pytest.fixture
def verwalter(db):
    return User.objects.create_user(
        username="marc", password="geheim123", is_staff=True
    )


@pytest.fixture
def block(db, schueler):
    lernblock = Lernblock.objects.create(name="Unit 4", bidirektional=True)
    for i in range(1, 6):
        Karteikarte.objects.create(
            lernblock=lernblock, begriff=f"wort {i}", definition=f"Wort {i}"
        )
    BenutzerLernblock.objects.create(benutzer=schueler, lernblock=lernblock)
    return lernblock


@pytest.fixture
def angemeldet(client, schueler):
    client.force_login(schueler)
    return client


# --- Ein Weg ins Lernen -------------------------------------------------------------


def test_lernen_startet_im_gewaehlten_modus(angemeldet, block, schueler):
    stats = BenutzerStatistik.get_or_create_for_user(schueler)
    stats.bevorzugter_modus = "multiple_choice"
    stats.save()

    antwort = angemeldet.get(reverse("lernen_starten", args=[block.pk]))

    assert antwort.url == reverse("lernen_multiple_choice", args=[block.pk])


def test_unmoeglicher_modus_faellt_auf_klassisch_zurueck(angemeldet, block, schueler):
    """Ein Block ohne Rueckseite kennt keinen Rueckwaerts-Modus."""
    block.bidirektional = False
    block.save()
    stats = BenutzerStatistik.get_or_create_for_user(schueler)
    stats.bevorzugter_modus = "rueckwaerts"
    stats.save()

    antwort = angemeldet.get(reverse("lernen_starten", args=[block.pk]))

    assert antwort.url == reverse("lernen_klassisch", args=[block.pk])


def test_modus_wird_dauerhaft_gemerkt(angemeldet, block, schueler):
    angemeldet.post(reverse("modus_waehlen", args=[block.pk]), {"modus": "tippen"})

    assert (
        BenutzerStatistik.get_or_create_for_user(schueler).bevorzugter_modus == "tippen"
    )


def test_unbekannter_modus_wird_ignoriert(angemeldet, block, schueler):
    angemeldet.post(reverse("modus_waehlen", args=[block.pk]), {"modus": "quatsch"})

    assert (
        BenutzerStatistik.get_or_create_for_user(schueler).bevorzugter_modus
        == "klassisch"
    )


def test_alles_zusammen_nimmt_die_eigenen_bloecke(angemeldet, block):
    antwort = angemeldet.get(reverse("lernen_alles"))

    assert antwort.status_code == 302
    assert antwort.url == f"{reverse('lernen_kombiniert')}?bloecke={block.pk}"


def test_ohne_bloecke_fuehrt_der_start_zur_blockauswahl(angemeldet):
    antwort = angemeldet.get(reverse("lernen_alles"))

    assert antwort.url == reverse("meine_lernbloecke")


# --- Verwaltung liegt nicht im Lernweg ---------------------------------------------


def test_schueler_sieht_keine_verwaltung(angemeldet, block):
    seiten = [reverse("mehr"), reverse("lernblock_detail", args=[block.pk])]

    for seite in seiten:
        inhalt = angemeldet.get(seite).content.decode()
        assert "Nur f&uuml;r Verwalter" not in inhalt, seite
        assert reverse("benutzer_liste") not in inhalt, seite


def test_verwalter_sieht_die_verwaltung(client, verwalter, block):
    client.force_login(verwalter)

    inhalt = client.get(reverse("mehr")).content.decode()

    assert reverse("benutzer_liste") in inhalt
    assert reverse("backup_liste") in inhalt


# --- Navigation ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "seite, reiter",
    [
        ("dashboard", "start"),
        ("meine_lernbloecke", "bloecke"),
        ("fortschritt", "fortschritt"),
        ("mehr", "mehr"),
        ("profil", "mehr"),
    ],
)
def test_reiter_passt_zur_seite(angemeldet, seite, reiter):
    antwort = angemeldet.get(reverse(seite))

    assert antwort.context["aktiver_reiter"] == reiter


def test_abfrage_laeuft_ohne_navigation(angemeldet, block):
    inhalt = angemeldet.get(
        reverse("lernen_klassisch", args=[block.pk])
    ).content.decode()

    assert 'aria-label="Hauptnavigation"' not in inhalt
    assert "ohne-schiene" in inhalt


def test_normale_seite_zeigt_die_navigation(angemeldet, block):
    inhalt = angemeldet.get(reverse("dashboard")).content.decode()

    assert 'aria-label="Hauptnavigation"' in inhalt
