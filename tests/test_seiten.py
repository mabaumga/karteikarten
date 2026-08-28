"""Rauchtest: jede Seite muss sich rendern lassen."""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from karteikarten.models import BenutzerLernblock, Karteikarte, Lernblock


@pytest.fixture
def benutzer(db):
    return User.objects.create_user(
        username="lina", password="geheim123", is_staff=True, first_name="Lina"
    )


@pytest.fixture
def block(db, benutzer):
    lernblock = Lernblock.objects.create(name="Unit 4", bidirektional=True)
    for i in range(1, 6):
        Karteikarte.objects.create(
            lernblock=lernblock, begriff=f"wort {i}", definition=f"Wort {i}"
        )
    BenutzerLernblock.objects.create(benutzer=benutzer, lernblock=lernblock)
    return lernblock


@pytest.fixture
def angemeldet(client, benutzer):
    client.force_login(benutzer)
    return client


@pytest.mark.parametrize(
    "name, braucht_block",
    [
        ("dashboard", False),
        ("fortschritt", False),
        ("mehr", False),
        ("meine_lernbloecke", False),
        ("profil", False),
        ("lernen_kombiniert_auswahl", False),
        ("lernblock_detail", True),
        ("lernblock_fortschritt", True),
        ("modus_waehlen", True),
        ("kartenauswahl", True),
        ("karten_liste", True),
        ("lernen_klassisch", True),
        ("lernen_rueckwaerts", True),
        ("lernen_multiple_choice", True),
        ("lernen_tippen", True),
    ],
)
def test_seite_rendert(angemeldet, block, name, braucht_block):
    url = reverse(name, args=[block.pk]) if braucht_block else reverse(name)
    antwort = angemeldet.get(url)
    assert antwort.status_code == 200, f"{name}: {antwort.status_code}"


def test_kombinierte_ansichten_rendern(angemeldet, block):
    for name in (
        "lernen_kombiniert",
        "lernen_kombiniert_mc",
        "lernen_kombiniert_tippen",
    ):
        antwort = angemeldet.get(reverse(name), {"bloecke": str(block.pk)})
        assert antwort.status_code == 200, f"{name}: {antwort.status_code}"


def test_lernen_starten_fuehrt_in_den_gewaehlten_modus(angemeldet, block, benutzer):
    from karteikarten.models import BenutzerStatistik

    stats = BenutzerStatistik.get_or_create_for_user(benutzer)
    stats.bevorzugter_modus = "tippen"
    stats.save()

    antwort = angemeldet.get(reverse("lernen_starten", args=[block.pk]))
    assert antwort.status_code == 302
    assert antwort.url == reverse("lernen_tippen", args=[block.pk])
