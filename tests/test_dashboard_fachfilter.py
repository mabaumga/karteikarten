"""Tests fuer den Schulfach-Filter auf dem Dashboard.

Gemeint ist das Schulfach (Englisch, Franzoesisch), nicht das Leitner-Fach 1-5.
Der Filter laeuft in Python, weil display_schulfach der Lehrwerk-Hierarchie folgt
und keine Spalte ist — deshalb ist hier auch der Weg ueber das Lehrwerk abgedeckt.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from karteikarten.models import (
    BenutzerLernblock,
    BenutzerStatistik,
    Karteikarte,
    Lehrwerk,
    LehrwerkUnit,
    Lernblock,
    Lernergebnis,
    Schulfach,
)


@pytest.fixture
def benutzer(db):
    return User.objects.create_user(username="schueler", password="geheim123")


@pytest.fixture
def angemeldet(client, benutzer):
    client.force_login(benutzer)
    return client


@pytest.fixture
def faecher(db):
    return {
        "englisch": Schulfach.objects.create(name="Englisch"),
        "franzoesisch": Schulfach.objects.create(name="Franzoesisch"),
    }


def _block(benutzer, name, karten=1, **kwargs):
    """Lernblock anlegen, dem Benutzer zuordnen und mit Karten fuellen."""
    lernblock = Lernblock.objects.create(name=name, **kwargs)
    BenutzerLernblock.objects.create(benutzer=benutzer, lernblock=lernblock)
    for i in range(karten):
        Karteikarte.objects.create(
            lernblock=lernblock, begriff=f"{name}-{i}", definition=f"Definition {i}"
        )
    return lernblock


def _bloecke(antwort):
    return [item["lernblock"] for item in antwort.context["bloecke_mit_status"]]


# --- Filtern -----------------------------------------------------------------------


def test_ohne_filter_erscheinen_alle_bloecke(angemeldet, benutzer, faecher):
    _block(benutzer, "Unit 1", schulfach=faecher["englisch"])
    _block(benutzer, "Unite 1", schulfach=faecher["franzoesisch"])

    antwort = angemeldet.get(reverse("dashboard"))

    assert len(_bloecke(antwort)) == 2
    assert antwort.context["filter_fach"] == ""


def test_filter_zeigt_nur_das_gewaehlte_fach(angemeldet, benutzer, faecher):
    englisch = _block(benutzer, "Unit 1", schulfach=faecher["englisch"])
    _block(benutzer, "Unite 1", schulfach=faecher["franzoesisch"])

    antwort = angemeldet.get(reverse("dashboard"), {"fach": faecher["englisch"].pk})

    assert _bloecke(antwort) == [englisch]


def test_auswahlliste_bleibt_vollstaendig_wenn_gefiltert_wird(
    angemeldet, benutzer, faecher
):
    _block(benutzer, "Unit 1", schulfach=faecher["englisch"])
    _block(benutzer, "Unite 1", schulfach=faecher["franzoesisch"])

    antwort = angemeldet.get(reverse("dashboard"), {"fach": faecher["englisch"].pk})

    # Sonst koennte man nach dem ersten Filtern nicht mehr zurueckwechseln.
    assert [f.name for f in antwort.context["schulfaecher"]] == [
        "Englisch",
        "Franzoesisch",
    ]


def test_fach_aus_der_lehrwerk_hierarchie_wird_erkannt(angemeldet, benutzer, faecher):
    lehrwerk = Lehrwerk.objects.create(name="Green Line", schulfach=faecher["englisch"])
    unit = LehrwerkUnit.objects.create(lehrwerk=lehrwerk, name="Unit 4")
    ueber_lehrwerk = _block(benutzer, "Vokabeln", lehrwerk_unit=unit)
    _block(benutzer, "Unite 1", schulfach=faecher["franzoesisch"])

    antwort = angemeldet.get(reverse("dashboard"), {"fach": faecher["englisch"].pk})

    assert _bloecke(antwort) == [ueber_lehrwerk]


def test_unsinniger_filterwert_wird_ignoriert(angemeldet, benutzer, faecher):
    _block(benutzer, "Unit 1", schulfach=faecher["englisch"])

    antwort = angemeldet.get(reverse("dashboard"), {"fach": "abc"})

    assert len(_bloecke(antwort)) == 1
    assert antwort.context["filter_fach"] == ""


def test_bloecke_ohne_fach_verschwinden_beim_filtern(angemeldet, benutzer, faecher):
    _block(benutzer, "Unit 1", schulfach=faecher["englisch"])
    _block(benutzer, "Sonstiges")

    ohne_filter = angemeldet.get(reverse("dashboard"))
    mit_filter = angemeldet.get(reverse("dashboard"), {"fach": faecher["englisch"].pk})

    assert len(_bloecke(ohne_filter)) == 2
    assert len(_bloecke(mit_filter)) == 1


# --- Kennzahlen folgen dem Filter --------------------------------------------------


def test_kennzahlen_beziehen_sich_auf_den_ausschnitt(angemeldet, benutzer, faecher):
    _block(benutzer, "Unit 1", karten=3, schulfach=faecher["englisch"])
    _block(benutzer, "Unite 1", karten=5, schulfach=faecher["franzoesisch"])

    antwort = angemeldet.get(reverse("dashboard"), {"fach": faecher["englisch"].pk})

    assert antwort.context["total_karten"] == 3
    assert antwort.context["total_faellig"] == 3


def test_heute_zaehlt_nur_das_gefilterte_fach(angemeldet, benutzer, faecher):
    englisch = _block(benutzer, "Unit 1", schulfach=faecher["englisch"])
    franzoesisch = _block(benutzer, "Unite 1", schulfach=faecher["franzoesisch"])
    Lernergebnis.objects.create(
        benutzer=benutzer, karte=englisch.karten.first(), richtig=True
    )
    Lernergebnis.objects.create(
        benutzer=benutzer, karte=franzoesisch.karten.first(), richtig=False
    )

    ohne_filter = angemeldet.get(reverse("dashboard"))
    mit_filter = angemeldet.get(reverse("dashboard"), {"fach": faecher["englisch"].pk})

    assert (
        ohne_filter.context["heute_richtig"],
        ohne_filter.context["heute_falsch"],
    ) == (1, 1)
    assert (
        mit_filter.context["heute_richtig"],
        mit_filter.context["heute_falsch"],
    ) == (1, 0)


def test_streak_bleibt_global(angemeldet, benutzer, faecher):
    _block(benutzer, "Unit 1", schulfach=faecher["englisch"])
    stats = BenutzerStatistik.get_or_create_for_user(benutzer)
    stats.streak = 7
    stats.save()

    antwort = angemeldet.get(reverse("dashboard"), {"fach": faecher["englisch"].pk})

    assert antwort.context["streak"] == 7
