"""Tests fuer die Pruefung eingetippter Antworten.

Die Pruefung soll nachsichtig sein, wo es nicht um Vokabelwissen geht, und streng,
wo es darum geht. Diese Grenze zieht die Testdatei nach.
"""

import pytest

from karteikarten.services.antwortpruefung import FALSCH, FAST, RICHTIG, pruefe_antwort


@pytest.mark.parametrize(
    "eingabe, loesung",
    [
        ("der Hund", "der Hund"),
        ("der hund", "der Hund"),  # Grossschreibung
        ("  der Hund  ", "der Hund"),  # Rand-Leerzeichen
        ("der  Hund", "der Hund"),  # doppeltes Leerzeichen
        ("der Hund.", "der Hund"),  # Satzzeichen am Rand
        ("strasse", "Straße"),  # ss/ß (casefold)
        ("gehen", "gehen (zu Fuß)"),  # Klammerzusatz
        ("laufen", "gehen / laufen"),  # Alternative
        ("das Tier", "der Hund, das Tier"),  # Alternative mit Komma
        ("vielleicht", "eventuell oder vielleicht"),  # Alternative mit "oder"
    ],
)
def test_richtig(eingabe, loesung):
    assert pruefe_antwort(eingabe, loesung) == RICHTIG


@pytest.mark.parametrize(
    "eingabe, loesung",
    [
        ("eleve", "élève"),  # Akzente fehlen
        ("Hund", "der Hund"),  # Artikel fehlt
        ("go", "to go"),  # englischer Infinitiv
        ("l eleve", "l'élève"),  # Apostroph als Leerzeichen getippt
        ("eleve", "l'élève"),  # elidierter Artikel fehlt
    ],
)
def test_fast_richtig(eingabe, loesung):
    """Vokabel gewusst, ein Detail daneben — zaehlt als richtig, mit Hinweis."""
    assert pruefe_antwort(eingabe, loesung) == FAST


@pytest.mark.parametrize(
    "eingabe, loesung",
    [
        ("die Katze", "der Hund"),  # andere Vokabel
        ("Katze", "der Hund"),
        ("", "der Hund"),  # nichts eingetippt
        ("   ", "der Hund"),
        (".", "der Hund"),  # nur Satzzeichen
        ("der Hunde", "der Hund"),  # Endung daneben
    ],
)
def test_falsch(eingabe, loesung):
    assert pruefe_antwort(eingabe, loesung) == FALSCH
