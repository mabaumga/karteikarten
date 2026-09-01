"""Tests fuer den Test — das frei zusammengestellte Uebungsset.

Der Kern: ein Test verweist auf Karten, er kopiert sie nicht. Eine Antwort im
Test stellt dieselbe Leitner-Stufe weiter wie eine Antwort im Herkunftsblock,
und ein geloeschter Test nimmt keine Karte mit.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from karteikarten.models import (
    BenutzerKarteStatus,
    BenutzerStatistik,
    Karteikarte,
    Lernblock,
    Test,
)


@pytest.fixture
def schueler(db):
    return User.objects.create_user(username="lina", password="geheim123")


@pytest.fixture
def angemeldet(client, schueler):
    client.force_login(schueler)
    return client


def _block(name, anzahl=4, bidirektional=True):
    lernblock = Lernblock.objects.create(name=name, bidirektional=bidirektional)
    for i in range(anzahl):
        Karteikarte.objects.create(
            lernblock=lernblock, begriff=f"{name}-{i}", definition=f"Bedeutung {i}"
        )
    return lernblock


@pytest.fixture
def block(db):
    return _block("Unité 1")


@pytest.fixture
def test_mit_karten(schueler, block):
    pruefung = Test.objects.create(benutzer=schueler, name="Klassenarbeit")
    pruefung.karten.add(*block.karten.all())
    return pruefung


# --- Anlegen und Zuschnitt ----------------------------------------------------------


def test_test_anlegen(angemeldet, schueler):
    antwort = angemeldet.post(reverse("test_create"), {"name": "Klassenarbeit"})

    pruefung = Test.objects.get(benutzer=schueler, name="Klassenarbeit")
    assert antwort.url == reverse("test_detail", args=[pruefung.pk])


def test_gleicher_name_nur_einmal_je_person(angemeldet, schueler, test_mit_karten):
    angemeldet.post(reverse("test_create"), {"name": "Klassenarbeit"})

    assert Test.objects.filter(benutzer=schueler, name="Klassenarbeit").count() == 1


def test_fremde_tests_bleiben_unsichtbar(angemeldet, db, test_mit_karten):
    fremder = User.objects.create_user(username="max", password="geheim123")
    fremd = Test.objects.create(benutzer=fremder, name="Fremd")

    assert angemeldet.get(reverse("test_detail", args=[fremd.pk])).status_code == 404


def test_karten_aus_einem_block_uebernehmen(angemeldet, schueler, block):
    pruefung = Test.objects.create(benutzer=schueler, name="Klassenarbeit")
    karten = list(block.karten.all())[:2]

    angemeldet.post(
        reverse("test_karten_uebernehmen", args=[block.pk]),
        {"karten": [k.pk for k in karten], "test": pruefung.pk},
    )

    assert set(pruefung.karten.all()) == set(karten)


def test_uebernehmen_kann_einen_neuen_test_anlegen(angemeldet, schueler, block):
    karte = block.karten.first()

    angemeldet.post(
        reverse("test_karten_uebernehmen", args=[block.pk]),
        {"karten": [karte.pk], "test": "neu", "neuer_name": "Vokabeltest Freitag"},
    )

    pruefung = Test.objects.get(benutzer=schueler, name="Vokabeltest Freitag")
    assert list(pruefung.karten.all()) == [karte]


def test_test_sammelt_ueber_bloecke_hinweg(angemeldet, schueler, block, db):
    zweiter = _block("Unit 4")
    pruefung = Test.objects.create(benutzer=schueler, name="Gemischt")

    for quelle in (block, zweiter):
        angemeldet.post(
            reverse("test_karten_uebernehmen", args=[quelle.pk]),
            {"karten": [quelle.karten.first().pk], "test": pruefung.pk},
        )

    assert pruefung.anzahl_karten == 2
    assert list(pruefung.herkunft) == sorted([block, zweiter], key=lambda b: b.name)


def test_karte_aus_dem_test_nehmen_laesst_die_karte_leben(
    angemeldet, test_mit_karten, block
):
    karte = block.karten.first()

    angemeldet.post(
        reverse("test_karte_entfernen", args=[test_mit_karten.pk, karte.pk])
    )

    assert test_mit_karten.anzahl_karten == 3
    assert Karteikarte.objects.filter(pk=karte.pk).exists()


def test_geloeschter_test_nimmt_keine_karte_mit(angemeldet, test_mit_karten, block):
    angemeldet.post(reverse("test_loeschen", args=[test_mit_karten.pk]))

    assert not Test.objects.filter(pk=test_mit_karten.pk).exists()
    assert block.karten.count() == 4


# --- Abfrage -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "modus, vorlage",
    [
        ("klassisch", "karteikarten/lernen_karte.html"),
        ("rueckwaerts", "karteikarten/lernen_karte.html"),
        ("multiple_choice", "karteikarten/lernen_multiple_choice.html"),
        ("tippen", "karteikarten/lernen_tippen.html"),
    ],
)
def test_alle_modi_laufen_auch_fuer_einen_test(
    angemeldet, test_mit_karten, modus, vorlage
):
    antwort = angemeldet.get(
        reverse("test_lernen_modus", args=[test_mit_karten.pk, modus])
    )

    assert antwort.status_code == 200
    assert antwort.templates[0].name == vorlage


def test_lernen_startet_im_gewaehlten_modus(angemeldet, schueler, test_mit_karten):
    stats = BenutzerStatistik.get_or_create_for_user(schueler)
    stats.bevorzugter_modus = "tippen"
    stats.save()

    antwort = angemeldet.get(reverse("test_lernen", args=[test_mit_karten.pk]))

    assert antwort.url == reverse(
        "test_lernen_modus", args=[test_mit_karten.pk, "tippen"]
    )


def test_rueckwaerts_nur_wenn_alle_karten_es_hergeben(angemeldet, schueler, block, db):
    einseitig = _block("Einseitig", bidirektional=False)
    pruefung = Test.objects.create(benutzer=schueler, name="Gemischt")
    pruefung.karten.add(block.karten.first(), einseitig.karten.first())

    antwort = angemeldet.get(
        reverse("test_lernen_modus", args=[pruefung.pk, "rueckwaerts"])
    )

    assert antwort.url == reverse("test_lernen_modus", args=[pruefung.pk, "klassisch"])


def test_multiple_choice_braucht_vier_karten(angemeldet, schueler, block):
    klein = Test.objects.create(benutzer=schueler, name="Klein")
    klein.karten.add(block.karten.first())

    antwort = angemeldet.get(
        reverse("test_lernen_modus", args=[klein.pk, "multiple_choice"])
    )

    assert antwort.templates[0].name == "karteikarten/lernen_fertig.html"
    assert "4 Karten" in antwort.context["error"]


def test_antwort_im_test_stellt_die_stufe_der_karte_weiter(
    angemeldet, schueler, test_mit_karten, block
):
    """Karten werden verwiesen, nicht kopiert — es gibt nur einen Lernstand."""
    karte = block.karten.first()

    angemeldet.post(
        reverse("karte_antwort", args=[karte.pk]),
        {"richtig": "true", "modus": "klassisch"},
    )

    assert BenutzerKarteStatus.get_or_create_for_user(schueler, karte).fach == 2


def test_abfrage_endet_wenn_nichts_faellig_ist(angemeldet, schueler, test_mit_karten):
    for karte in test_mit_karten.karten.all():
        status = BenutzerKarteStatus.get_or_create_for_user(schueler, karte)
        status.richtig_beantwortet()

    antwort = angemeldet.get(
        reverse("test_lernen_modus", args=[test_mit_karten.pk, "klassisch"])
    )

    assert antwort.templates[0].name == "karteikarten/lernen_fertig.html"
    assert antwort.context["quelle_name"] == test_mit_karten.name


def test_zuruecksetzen_macht_alles_wieder_faellig(
    angemeldet, schueler, test_mit_karten
):
    for karte in test_mit_karten.karten.all():
        BenutzerKarteStatus.get_or_create_for_user(
            schueler, karte
        ).richtig_beantwortet()

    angemeldet.post(reverse("test_zuruecksetzen", args=[test_mit_karten.pk]))

    antwort = angemeldet.get(
        reverse("test_lernen_modus", args=[test_mit_karten.pk, "klassisch"])
    )
    assert antwort.context["verbleibend"] == 4


# --- Statistik -----------------------------------------------------------------------


def test_fortschritt_eines_tests(angemeldet, schueler, test_mit_karten, block):
    karten = list(block.karten.all())
    angemeldet.post(
        reverse("karte_antwort", args=[karten[0].pk]),
        {"richtig": "true", "modus": "klassisch"},
    )
    angemeldet.post(
        reverse("karte_antwort", args=[karten[1].pk]),
        {"richtig": "false", "modus": "klassisch"},
    )

    auswertung = angemeldet.get(
        reverse("test_fortschritt", args=[test_mit_karten.pk])
    ).context["auswertung"]

    assert auswertung["anzahl_karten"] == 4
    assert auswertung["erstversuch_gesamt"] == 2
    assert auswertung["erstversuch_quote"] == 50
    assert auswertung["verlauf"] == []
