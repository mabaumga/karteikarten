"""Tests fuer die Reihenfolge der Abfrage.

Die Lernansichten laden sich nach jeder Antwort neu und ziehen dabei erneut eine
Karte. Genau deshalb darf die Reihenfolge nicht deterministisch sein: sonst gewinnt
immer dieselbe Karte — allen voran die gerade falsch beantwortete, die zurueck in
Fach 1 faellt und damit sofort wieder faellig ist. Abgesichert ist hier, dass die
Auswahl zufaellig ist, das Leitner-Fach trotzdem Vorrang behaelt und dieselbe Karte
nicht zweimal hintereinander drankommt.
"""

import random
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
    for i in range(1, 11):
        Karteikarte.objects.create(
            lernblock=lernblock,
            begriff=f"Begriff {i:02d}",
            definition=f"Definition {i:02d}",
        )
    return lernblock


@pytest.fixture
def angemeldet(client, benutzer):
    client.force_login(benutzer)
    return client


@pytest.fixture(autouse=True)
def fester_zufall():
    """Fester Seed — der Test soll die Streuung pruefen, nicht wuerfeln."""
    random.seed(20260828)


def _abgefragte_karten(client, block, runden):
    """Begriffe aus `runden` aufeinanderfolgenden Aufrufen der Lernansicht."""
    begriffe = []
    for _ in range(runden):
        antwort = client.get(reverse("lernen_klassisch", args=[block.pk]))
        begriffe.append(antwort.context["karte"].begriff)
    return begriffe


def test_die_abfrage_streut_ueber_die_faelligen_karten(angemeldet, block):
    begriffe = _abgefragte_karten(angemeldet, block, runden=12)

    assert len(set(begriffe)) >= 3, begriffe


def test_dieselbe_karte_kommt_nicht_zweimal_hintereinander(angemeldet, block):
    begriffe = _abgefragte_karten(angemeldet, block, runden=12)

    wiederholungen = [a for a, b in zip(begriffe, begriffe[1:]) if a == b]
    assert wiederholungen == []


def test_falsch_beantwortete_karte_kommt_nicht_sofort_wieder(angemeldet, block):
    lernen = reverse("lernen_klassisch", args=[block.pk])
    erste = angemeldet.get(lernen).context["karte"]

    angemeldet.post(
        reverse("karte_antwort", args=[erste.pk]),
        {"richtig": "false", "modus": "klassisch"},
    )
    zweite = angemeldet.get(lernen).context["karte"]

    assert zweite.pk != erste.pk


def test_niedriges_fach_hat_trotz_zufall_vorrang(angemeldet, block, benutzer):
    """Der Zufall wirkt innerhalb eines Fachs, nicht ueber die Faecher hinweg.

    Ein einzelner Nachzuegler in Fach 1 kommt dadurch in jeder zweiten Runde dran —
    dazwischen greift die Sperre gegen sofortige Wiederholung, die bewusst ueber der
    Fach-Prioritaet steht. Zwei Karten im Wechsel sind besser als eine im Dauerlauf.
    """
    karten = list(block.karten.all())
    for karte in karten[1:]:
        status = BenutzerKarteStatus.get_or_create_for_user(benutzer, karte)
        status.fach = 3
        status.save()
    nachzuegler = karten[0]

    begriffe = _abgefragte_karten(angemeldet, block, runden=6)

    assert begriffe.count(nachzuegler.begriff) == 3
    assert begriffe[0] == nachzuegler.begriff


def test_einzige_faellige_karte_kommt_trotz_sperre_dran(angemeldet, block, benutzer):
    """Die Sperre darf die Abfrage nicht leerlaufen lassen."""
    karten = list(block.karten.all())
    for karte in karten[1:]:
        status = BenutzerKarteStatus.get_or_create_for_user(benutzer, karte)
        status.naechste_wiederholung = date.today() + timedelta(days=3)
        status.save()

    begriffe = _abgefragte_karten(angemeldet, block, runden=3)

    assert set(begriffe) == {karten[0].begriff}
