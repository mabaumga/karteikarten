"""Auswertung des Lernfortschritts.

Alle Zahlen stammen aus Daten, die ohnehin anfallen: ``Lernergebnis`` haelt jede
einzelne Antwort mit Zeitstempel, ``BenutzerKarteStatus`` den Stand je Karte,
``TagesStatistik`` die Tagessummen.

Die aussagekraeftigste Zahl ist die **Erstversuchsquote**: der Anteil der Karten,
die beim allerersten Mal richtig beantwortet wurden. Die laufende Erfolgsquote
steigt zwangslaeufig, weil jede Karte so lange wiederkommt, bis sie sitzt — der
erste Versuch dagegen sagt, was wirklich gelernt wurde.
"""

from collections import Counter
from datetime import date, timedelta

from django.db.models import Count, Max

from ..models import BenutzerKarteStatus, Lernergebnis, TagesStatistik

HOECHSTE_STUFE = 5
VERLAUF_TAGE = 7
PROBLEMKARTEN = 5


def _quote(teil, gesamt):
    return round(teil / gesamt * 100) if gesamt else 0


def erste_antwort_je_karte(benutzer, karten_ids):
    """Die jeweils *erste* Antwort je Karte als ``{karte_id: richtig}``.

    SQLite kennt kein ``DISTINCT ON``; die Auswahl laeuft deshalb in Python ueber
    die nach Zeit sortierten Ergebnisse. Bei den Datenmengen dieser App ist das
    unkritisch und dafuer offensichtlich richtig.
    """
    erste = {}
    ergebnisse = (
        Lernergebnis.objects.filter(benutzer=benutzer, karte_id__in=karten_ids)
        .order_by("zeitstempel", "pk")
        .values_list("karte_id", "richtig")
    )
    for karte_id, richtig in ergebnisse:
        erste.setdefault(karte_id, richtig)
    return erste


def _kartenzustand(benutzer, karten, beantwortet):
    """Wie die Karten des Blocks stehen: sitzt, in Arbeit, noch nie geuebt.

    "Nie geuebt" haengt an ``beantwortet`` (den Karten mit mindestens einer
    Antwort), nicht am Status: ein Status entsteht schon, sobald eine Karte
    einmal angezeigt wurde — auch wenn die Sitzung danach abgebrochen wurde.
    """
    verteilung = {stufe: 0 for stufe in range(1, HOECHSTE_STUFE + 1)}
    sitzt = 0
    in_arbeit = 0
    nie_geuebt = 0
    faellig = 0

    vorhanden = {
        status.karte_id: status
        for status in BenutzerKarteStatus.objects.filter(
            benutzer=benutzer, karte__in=karten
        )
    }
    for karte in karten:
        status = vorhanden.get(karte.pk)
        stufe = status.fach if status else 1
        verteilung[stufe] += 1
        if status is None or status.ist_faellig:
            faellig += 1

        if karte.pk not in beantwortet:
            nie_geuebt += 1
        elif stufe >= HOECHSTE_STUFE:
            sitzt += 1
        else:
            in_arbeit += 1

    return {
        "verteilung": verteilung,
        "sitzt": sitzt,
        "in_arbeit": in_arbeit,
        "nie_geuebt": nie_geuebt,
        "faellig": faellig,
    }


def _problemkarten(benutzer, karten):
    """Karten mit den meisten falschen Antworten, absteigend."""
    je_karte = Counter(
        dict(
            Lernergebnis.objects.filter(
                benutzer=benutzer, karte__in=karten, richtig=False
            )
            .values_list("karte_id")
            .annotate(anzahl=Count("pk"))
        )
    )
    nach_id = {karte.pk: karte for karte in karten}
    return [
        {"karte": nach_id[karte_id], "falsch": anzahl}
        for karte_id, anzahl in je_karte.most_common(PROBLEMKARTEN)
    ]


def _verlauf(benutzer, lernblock):
    """Die letzten sieben Tage, Luecken als Nulltage."""
    von = date.today() - timedelta(days=VERLAUF_TAGE - 1)
    gebucht = {
        eintrag.datum: eintrag
        for eintrag in TagesStatistik.objects.filter(
            benutzer=benutzer, lernblock=lernblock, datum__gte=von
        )
    }
    tage = []
    hoechstwert = 0
    for versatz in range(VERLAUF_TAGE):
        tag = von + timedelta(days=versatz)
        eintrag = gebucht.get(tag)
        gelernt = eintrag.gelernt if eintrag else 0
        richtig = eintrag.richtig if eintrag else 0
        hoechstwert = max(hoechstwert, gelernt)
        tage.append({"datum": tag, "gelernt": gelernt, "richtig": richtig})

    # Balkenhoehen als Prozent des besten Tages — sonst braeuchte das Template Mathematik.
    for tag in tage:
        tag["hoehe"] = _quote(tag["gelernt"], hoechstwert)
        tag["anteil_richtig"] = _quote(tag["richtig"], tag["gelernt"])
    return tage


def kartenmenge_fortschritt(benutzer, karten, verlauf_fuer=None):
    """Auswertung einer beliebigen Kartenmenge.

    Woher die Karten stammen, spielt keine Rolle — ein Lernblock oder ein frei
    zusammengestellter Test. Nur der Tagesverlauf haengt an einem Block: die
    Tagessummen werden je Block gefuehrt, fuer eine gemischte Menge gibt es
    keinen. Dann bleibt der Verlauf leer, statt eine falsche Kurve zu zeichnen.
    """
    erste = erste_antwort_je_karte(benutzer, [karte.pk for karte in karten])
    richtig = sum(1 for wert in erste.values() if wert)

    zuletzt = Lernergebnis.objects.filter(
        benutzer=benutzer, karte__in=karten
    ).aggregate(zeitpunkt=Max("zeitstempel"))["zeitpunkt"]

    return {
        "anzahl_karten": len(karten),
        "erstversuch_richtig": richtig,
        "erstversuch_gesamt": len(erste),
        "erstversuch_quote": _quote(richtig, len(erste)),
        "problemkarten": _problemkarten(benutzer, karten),
        "verlauf": _verlauf(benutzer, verlauf_fuer) if verlauf_fuer else [],
        "zuletzt_gelernt": zuletzt,
        **_kartenzustand(benutzer, karten, set(erste)),
    }


def block_fortschritt(benutzer, lernblock):
    """Vollstaendige Auswertung eines Lernblocks fuer einen Benutzer."""
    karten = list(lernblock.karten.all())
    return {
        "lernblock": lernblock,
        **kartenmenge_fortschritt(benutzer, karten, verlauf_fuer=lernblock),
    }


def _summe(auswertungen):
    """Mehrere Auswertungen zu einer zusammenziehen."""
    richtig = sum(eintrag["erstversuch_richtig"] for eintrag in auswertungen)
    gesamt = sum(eintrag["erstversuch_gesamt"] for eintrag in auswertungen)
    return {
        "anzahl_karten": sum(eintrag["anzahl_karten"] for eintrag in auswertungen),
        "erstversuch_richtig": richtig,
        "erstversuch_gesamt": gesamt,
        "erstversuch_quote": _quote(richtig, gesamt),
        "sitzt": sum(eintrag["sitzt"] for eintrag in auswertungen),
        "in_arbeit": sum(eintrag["in_arbeit"] for eintrag in auswertungen),
        "nie_geuebt": sum(eintrag["nie_geuebt"] for eintrag in auswertungen),
        "faellig": sum(eintrag["faellig"] for eintrag in auswertungen),
    }


def _gruppieren(auswertungen, schluessel):
    """Nach einem Merkmal buendeln, Reihenfolge des ersten Auftretens erhalten."""
    gruppen = {}
    for auswertung in auswertungen:
        gruppen.setdefault(schluessel(auswertung["lernblock"]), []).append(auswertung)
    return gruppen


def gegliederter_fortschritt(benutzer, lernbloecke):
    """Fortschritt nach Schulfach und Lehrwerk gegliedert.

    Ein Schueler lernt selten "irgendwelche Karten", sondern Englisch und
    Franzoesisch, und darin ein Lehrbuch nach dem anderen. Die Gesamtquote allein
    verwischt genau das: 75 Prozent koennen 100 in Franzoesisch und 50 in Englisch
    heissen. Deshalb wird auf beiden Ebenen zusammengezaehlt.

    Gezaehlt wird ausschliesslich, was der Benutzer sich ausgesucht hat — die
    Bloecke kommen bereits gefiltert herein.
    """
    je_block = [block_fortschritt(benutzer, block) for block in lernbloecke]

    schulfaecher = []
    nach_fach = _gruppieren(je_block, lambda block: block.display_schulfach)
    for fach in sorted(nach_fach, key=lambda f: (f is None, f.name if f else "")):
        bloecke_des_fachs = nach_fach[fach]

        lehrwerke = []
        nach_lehrwerk = _gruppieren(
            bloecke_des_fachs,
            lambda block: block.lehrwerk_unit.lehrwerk if block.lehrwerk_unit else None,
        )
        for lehrwerk in sorted(
            nach_lehrwerk, key=lambda lw: (lw is None, str(lw) if lw else "")
        ):
            gruppe = nach_lehrwerk[lehrwerk]
            lehrwerke.append(
                {
                    "lehrwerk": lehrwerk,
                    "name": str(lehrwerk) if lehrwerk else "Ohne Lehrwerk",
                    "bloecke": gruppe,
                    **_summe(gruppe),
                }
            )

        schulfaecher.append(
            {
                "schulfach": fach,
                "name": fach.name if fach else "Ohne Schulfach",
                "lehrwerke": lehrwerke,
                **_summe(bloecke_des_fachs),
            }
        )

    return {
        "bloecke": je_block,
        "schulfaecher": schulfaecher,
        **_summe(je_block),
    }


def kurzfortschritt(benutzer, lernblock):
    """Wie viel eines Blocks sicher sitzt — die kleine Zeile waehrend der Abfrage.

    Absichtlich schmal gehalten: waehrend des Lernens zaehlt eine Zahl, nicht die
    ganze Auswertung. Zwei Abfragen statt eines Durchlaufs ueber alle Karten.
    """
    anzahl = lernblock.karten.count()
    sitzt = BenutzerKarteStatus.objects.filter(
        benutzer=benutzer, karte__lernblock=lernblock, fach=HOECHSTE_STUFE
    ).count()
    return {
        "lernblock": lernblock,
        "sitzt": sitzt,
        "anzahl": anzahl,
        "prozent": _quote(sitzt, anzahl),
    }
