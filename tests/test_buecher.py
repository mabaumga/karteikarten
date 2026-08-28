"""Tests fuer Buecher, Kapitel und die Baumdarstellung der Blockauswahl.

Die Hierarchie Buch -> Kapitel -> Lernblock gab es im Datenmodell schon; sichtbar
und pflegbar ist sie erst jetzt. Abgesichert ist, dass die Struktur haelt: keine
Dubletten, kein Loeschen unter den Bloecken weg, und nichts faellt aus dem Baum.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from karteikarten.models import (
    BenutzerLernblock,
    Karteikarte,
    Lehrwerk,
    LehrwerkUnit,
    Lernblock,
    Schulfach,
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
def buch(db):
    franzoesisch = Schulfach.objects.create(name="Französisch")
    return Lehrwerk.objects.create(name="À plus !", band="4", schulfach=franzoesisch)


@pytest.fixture
def kapitel(buch):
    return [
        LehrwerkUnit.objects.create(lehrwerk=buch, name=f"Unité {i}", reihenfolge=i)
        for i in (1, 2)
    ]


def _block(name, unit=None, karten=2):
    lernblock = Lernblock.objects.create(name=name, lehrwerk_unit=unit)
    for i in range(karten):
        Karteikarte.objects.create(
            lernblock=lernblock, begriff=f"{name}-{i}", definition=f"Bedeutung {i}"
        )
    return lernblock


@pytest.fixture
def als_verwalter(client, verwalter):
    client.force_login(verwalter)
    return client


@pytest.fixture
def als_schueler(client, schueler):
    client.force_login(schueler)
    return client


# --- Buecher anlegen und pflegen ---------------------------------------------------


def test_buch_anlegen(als_verwalter, db):
    fach = Schulfach.objects.create(name="Französisch")

    antwort = als_verwalter.post(
        reverse("buch_create"),
        {"name": "À plus !", "band": "4", "schulfach": fach.pk},
    )

    lehrwerk = Lehrwerk.objects.get(name="À plus !")
    assert lehrwerk.band == "4"
    assert lehrwerk.schulfach == fach
    assert antwort.url == reverse("buch_detail", args=[lehrwerk.pk])


def test_buch_ohne_namen_wird_abgelehnt(als_verwalter, db):
    als_verwalter.post(reverse("buch_create"), {"name": "   ", "band": "4"})

    assert Lehrwerk.objects.count() == 0


def test_gleiches_buch_mit_gleichem_band_nur_einmal(als_verwalter, buch):
    als_verwalter.post(reverse("buch_create"), {"name": "À plus !", "band": "4"})

    assert Lehrwerk.objects.filter(name="À plus !").count() == 1


def test_gleicher_name_anderer_band_ist_erlaubt(als_verwalter, buch):
    als_verwalter.post(reverse("buch_create"), {"name": "À plus !", "band": "5"})

    assert Lehrwerk.objects.filter(name="À plus !").count() == 2


def test_kapitel_anlegen(als_verwalter, buch):
    als_verwalter.post(
        reverse("kapitel_create", args=[buch.pk]),
        {"name": "Unité 1", "reihenfolge": "1"},
    )

    assert buch.units.get().name == "Unité 1"


def test_kapitel_name_je_buch_eindeutig(als_verwalter, buch, kapitel):
    als_verwalter.post(reverse("kapitel_create", args=[buch.pk]), {"name": "Unité 1"})

    assert buch.units.filter(name="Unité 1").count() == 1


# --- Loeschen nur, wenn nichts daran haengt ----------------------------------------


def test_kapitel_mit_bloecken_wird_nicht_geloescht(als_verwalter, buch, kapitel):
    _block("Wortliste 1", kapitel[0])

    als_verwalter.post(reverse("kapitel_loeschen", args=[kapitel[0].pk]))

    assert LehrwerkUnit.objects.filter(pk=kapitel[0].pk).exists()


def test_leeres_kapitel_darf_weg(als_verwalter, buch, kapitel):
    als_verwalter.post(reverse("kapitel_loeschen", args=[kapitel[0].pk]))

    assert not LehrwerkUnit.objects.filter(pk=kapitel[0].pk).exists()


def test_buch_mit_belegten_kapiteln_bleibt_stehen(als_verwalter, buch, kapitel):
    _block("Wortliste 1", kapitel[0])

    als_verwalter.post(reverse("buch_loeschen", args=[buch.pk]))

    assert Lehrwerk.objects.filter(pk=buch.pk).exists()


# --- Nur Verwalter --------------------------------------------------------------


@pytest.mark.parametrize("seite", ["buecher", "buch_create"])
def test_schueler_kommt_nicht_an_die_buecher(als_schueler, seite):
    antwort = als_schueler.get(reverse(seite))

    assert antwort.status_code == 302
    assert antwort.url == reverse("dashboard")


# --- Baumdarstellung ------------------------------------------------------------


def test_baum_gliedert_nach_buch_und_kapitel(als_schueler, buch, kapitel):
    _block("Wortliste 1", kapitel[0])
    _block("Wortliste 2", kapitel[0])
    _block("Wortliste 3", kapitel[1])

    baum = als_schueler.get(reverse("meine_lernbloecke")).context["baum"]

    assert [b["name"] for b in baum] == ["À plus ! Band 4"]
    assert [k["name"] for k in baum[0]["kapitel"]] == ["Unité 1", "Unité 2"]
    assert baum[0]["kapitel"][0]["anzahl"] == 2
    assert baum[0]["anzahl"] == 3


def test_bloecke_ohne_kapitel_fallen_nicht_raus(als_schueler, buch, kapitel):
    _block("Wortliste 1", kapitel[0])
    _block("Frei schwebend", None)

    baum = als_schueler.get(reverse("meine_lernbloecke")).context["baum"]

    assert [b["name"] for b in baum] == ["À plus ! Band 4", "Ohne Buch"]
    assert baum[-1]["kapitel"][0]["name"] == "Ohne Kapitel"


def test_kapitel_stehen_in_ihrer_reihenfolge(als_schueler, buch):
    spaet = LehrwerkUnit.objects.create(lehrwerk=buch, name="Unité 9", reihenfolge=9)
    frueh = LehrwerkUnit.objects.create(lehrwerk=buch, name="Unité 2", reihenfolge=2)
    _block("a", spaet)
    _block("b", frueh)

    baum = als_schueler.get(reverse("meine_lernbloecke")).context["baum"]

    assert [k["name"] for k in baum[0]["kapitel"]] == ["Unité 2", "Unité 9"]


# --- Auswahl in einem Zug speichern ------------------------------------------------


def test_auswahl_setzt_und_entfernt(als_schueler, schueler, buch, kapitel):
    behalten = _block("Wortliste 1", kapitel[0])
    dazu = _block("Wortliste 2", kapitel[0])
    weg = _block("Wortliste 3", kapitel[1])
    for block in (behalten, weg):
        BenutzerLernblock.objects.create(benutzer=schueler, lernblock=block)

    als_schueler.post(
        reverse("lernbloecke_speichern"),
        {
            "bloecke": [behalten.pk, dazu.pk],
            "sichtbar": [behalten.pk, dazu.pk, weg.pk],
        },
    )

    gewaehlt = set(
        BenutzerLernblock.objects.filter(benutzer=schueler).values_list(
            "lernblock_id", flat=True
        )
    )
    assert gewaehlt == {behalten.pk, dazu.pk}


def test_ausgeblendete_bloecke_bleiben_unberuehrt(
    als_schueler, schueler, buch, kapitel
):
    """Ein aktiver Filter darf nicht abwaehlen, was er gerade versteckt."""
    sichtbar = _block("Wortliste 1", kapitel[0])
    versteckt = _block("Wortliste 9", kapitel[1])
    BenutzerLernblock.objects.create(benutzer=schueler, lernblock=versteckt)

    als_schueler.post(
        reverse("lernbloecke_speichern"),
        {"bloecke": [sichtbar.pk], "sichtbar": [sichtbar.pk]},
    )

    gewaehlt = set(
        BenutzerLernblock.objects.filter(benutzer=schueler).values_list(
            "lernblock_id", flat=True
        )
    )
    assert gewaehlt == {sichtbar.pk, versteckt.pk}


def test_abwaehlen_loescht_den_lernstand_nicht(als_schueler, schueler, buch, kapitel):
    from karteikarten.models import BenutzerKarteStatus

    block = _block("Wortliste 1", kapitel[0])
    BenutzerLernblock.objects.create(benutzer=schueler, lernblock=block)
    karte = block.karten.first()
    status = BenutzerKarteStatus.get_or_create_for_user(schueler, karte)
    status.fach = 4
    status.save()

    als_schueler.post(
        reverse("lernbloecke_speichern"), {"bloecke": [], "sichtbar": [block.pk]}
    )

    assert BenutzerKarteStatus.get_or_create_for_user(schueler, karte).fach == 4
