"""Prueft eingetippte Antworten gegen die Loesung einer Karteikarte.

Getippt wird meist auf dem Handy und oft in einer Fremdsprache. Die Pruefung ist
deshalb bewusst nachsichtig bei allem, was kein Vokabelwissen ist — Gross- und
Kleinschreibung, Leerzeichen, Satzzeichen am Rand, Klammerzusaetze — und streng bei
allem anderen.

Zwei Sonderfaelle sind bewusst eingebaut:

* **Alternativen.** Loesungen listen haeufig mehrere Bedeutungen ("gehen, laufen"
  oder "der Hund / das Tier"). Jede davon zaehlt fuer sich.
* **Akzente und Artikel.** Wer auf einer deutschen Tastatur `eleve` statt `eleve`
  mit Akzenten tippt oder `Hund` statt `der Hund`, kann die Vokabel — es fehlt nur
  ein Detail. Das zaehlt als richtig, die UI zeigt aber die genaue Loesung. Sonst
  waere der Modus auf dem Handy frustrierend statt lehrreich.
"""

import re
import unicodedata

RICHTIG = "richtig"
FAST = "fast"
FALSCH = "falsch"

# Artikel der drei Unterrichtssprachen. Fehlt der Artikel, ist die Vokabel trotzdem
# gewusst — das Ergebnis ist FAST, nicht FALSCH.
_ARTIKEL = frozenset(
    {
        "der",
        "die",
        "das",
        "ein",
        "eine",  # Deutsch
        "le",
        "la",
        "les",
        "l",
        "un",
        "une",
        "des",  # Franzoesisch
        "the",
        "a",
        "an",  # Englisch
        "to",  # Englischer Infinitiv
    }
)

_TRENNER = re.compile(r"\s*(?:[/;,]|\boder\b)\s*")
_KLAMMERZUSATZ = re.compile(r"\([^)]*\)")
_MEHRFACH_LEER = re.compile(r"\s+")
# Apostroph als Worttrenner: so wird aus "l'eleve" ein abtrennbarer Artikel,
# und wer statt des Apostrophs ein Leerzeichen tippt, liegt trotzdem richtig.
_APOSTROPH = re.compile(r"[\u0027\u2019\u02bc]")
_RAND = re.compile(r"^[^\w]+|[^\w]+$")


def _normalisieren(text: str) -> str:
    """Auf das reduzieren, was die Vokabel ausmacht."""
    ohne_apostroph = _APOSTROPH.sub(" ", text or "")
    ohne_klammern = _KLAMMERZUSATZ.sub(" ", ohne_apostroph)
    kompakt = _MEHRFACH_LEER.sub(" ", ohne_klammern).strip()
    return _RAND.sub("", kompakt).casefold()


def _ohne_akzente(text: str) -> str:
    zerlegt = unicodedata.normalize("NFKD", text)
    return "".join(zeichen for zeichen in zerlegt if not unicodedata.combining(zeichen))


def _varianten(loesung: str) -> set[str]:
    """Alle akzeptierten Schreibweisen: die ganze Loesung und ihre Alternativen."""
    ganze = _normalisieren(loesung)
    teile = (_normalisieren(teil) for teil in _TRENNER.split(loesung or ""))
    return {variante for variante in (ganze, *teile) if variante}


def _ohne_artikel(text: str) -> str:
    erstes, _, rest = text.partition(" ")
    return rest if rest and erstes in _ARTIKEL else text


def _kern(text: str) -> str:
    """Die Vokabel ohne die Details, die den Sinn nicht aendern."""
    return _ohne_artikel(_ohne_akzente(text))


def pruefe_antwort(eingabe: str, loesung: str) -> str:
    """Vergleicht Eingabe und Loesung: RICHTIG, FAST (Detail daneben) oder FALSCH."""
    eingegeben = _normalisieren(eingabe)
    if not eingegeben:
        return FALSCH

    varianten = _varianten(loesung)
    if eingegeben in varianten:
        return RICHTIG
    if _kern(eingegeben) in {_kern(variante) for variante in varianten}:
        return FAST
    return FALSCH
