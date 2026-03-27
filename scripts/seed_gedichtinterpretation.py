#!/usr/bin/env python
"""Seed database with Gedichtinterpretation content from PDF."""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from karteikarten.models import Schulfach, Jahrgangsstufe, Lernblock, Karteikarte

# =============================================================================
# Stammdaten
# =============================================================================

SCHULFAECHER = ['Deutsch', 'Mathematik', 'Biologie', 'Englisch', 'Geschichte']
JAHRGANGSSTUFEN = list(range(5, 14))  # 5-13

# =============================================================================
# Lernblöcke für Gedichtinterpretation
# =============================================================================

LERNBLOECKE = [
    {
        "name": "Metrum & Kadenzen",
        "beschreibung": "Versmaße und Kadenzen in der Lyrik",
        "bidirektional": True,
        "karten": [
            {
                "begriff": "Jambus",
                "definition": "Versmaß mit dem Schema: unbetont - betont (xx')",
                "beispiele": "Ge-DICHT, ver-LIEBT",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Aufstrebend, vorwärtsdrängend, natürlicher Sprechrhythmus",
            },
            {
                "begriff": "Trochäus",
                "definition": "Versmaß mit dem Schema: betont - unbetont ('xx)",
                "beispiele": "LIE-be, HIM-mel",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Fallend, ruhig, feierlich",
            },
            {
                "begriff": "Daktylus",
                "definition": "Versmaß mit dem Schema: betont - unbetont - unbetont ('xxx)",
                "beispiele": "WAN-de-rer, KÖ-ni-gin",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Tänzerisch, beschwingt, episch",
            },
            {
                "begriff": "Anapäst",
                "definition": "Versmaß mit dem Schema: unbetont - unbetont - betont (xxx')",
                "beispiele": "Pa-ra-DIES, Me-lo-DIE",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Drängend, beschleunigend, feierlich",
            },
            {
                "begriff": "Hebung",
                "definition": "Betonte Silbe in einem Vers; Anzahl der Hebungen bestimmt das Versmaß",
                "beispiele": "Dreihebiger Jambus = 3 betonte Silben im Jambus-Schema",
                "zusatz_label": "Hinweis",
                "zusatz_wert": "Anzahl der Striche/Betonungen in einem Vers",
            },
            {
                "begriff": "Männliche Kadenz",
                "definition": "Versende mit betonter letzter Silbe",
                "beispiele": "...ver-LIEBT, ...Ge-DICHT",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Härte, Dominanz, Abgeschlossenheit, körperliche Präsenz",
            },
            {
                "begriff": "Weibliche Kadenz",
                "definition": "Versende mit unbetonter letzter Silbe",
                "beispiele": "...LIE-be, ...STI-le",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Weich, offen, klingend, emotionale Wärme",
            },
            {
                "begriff": "Metrum im Expressionismus",
                "definition": "Gebrochene, wechselnde Metren spiegeln Zerfall und innere Zerrissenheit wider",
                "beispiele": "Rhythmisches Metrum wirkt wie Maschinentakt, Puls der Großstadt",
                "zusatz_label": "Kontrast Romantik",
                "zusatz_wert": "Romantik: Regelmäßiges Metrum erzeugt Harmonie, Herzschlag",
            },
        ]
    },
    {
        "name": "Reimformen",
        "beschreibung": "Reimschemata und ihre Wirkung in Lyrik",
        "bidirektional": True,
        "karten": [
            {
                "begriff": "Kreuzreim",
                "definition": "Reimschema a b a b - Verse reimen sich über Kreuz",
                "beispiele": "Vers 1 reimt auf Vers 3, Vers 2 auf Vers 4",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Expressionismus: Zerren zwischen Polen, Spannungsfelder. Romantik: Naturbilder, Wechsel (Traum-Wirklichkeit)",
            },
            {
                "begriff": "Paarreim",
                "definition": "Reimschema aa bb - Aufeinanderfolgende Verse reimen sich",
                "beispiele": "Vers 1+2 reimen, Vers 3+4 reimen",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Expressionismus: Steigende Intensität, 'kein Entkommen'. Romantik: Liedhaftigkeit, Zweisamkeit, Harmonie",
            },
            {
                "begriff": "Umarmender Reim",
                "definition": "Reimschema a bb a - Äußere Verse umrahmen innere",
                "beispiele": "Vers 1+4 reimen, Vers 2+3 reimen",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Expressionismus: Ich im Zwang gefangen, kein Ausweg. Romantik: Geborgenheit, Schutz, Umarmung",
            },
            {
                "begriff": "Binnenreim",
                "definition": "Reim innerhalb eines einzelnen Verses",
                "beispiele": "Er fährt und lacht durch die Nacht",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Beschleunigung, innere Erregung, Hektik; kann Melodie verstärken",
            },
            {
                "begriff": "Waise",
                "definition": "Reimloser Vers in einer sonst gereimten Strophe",
                "beispiele": "Ein Vers ohne Reimpartner",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Expressionismus: 'isolierter Schrei', Vereinzelung. Romantik: Besonders wichtige Aussage markieren",
            },
            {
                "begriff": "Schweifender Reim",
                "definition": "Reimschema aa b cc b - Erweiterte Reimform",
                "beispiele": "Paarreim mit eingeschobenem Kreuzreim",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Überlänge, ausufernde Gefühle; epische, erzählende Momente",
            },
        ]
    },
    {
        "name": "Gedichtformen",
        "beschreibung": "Klassische Gedichtformen und Strukturen",
        "bidirektional": True,
        "karten": [
            {
                "begriff": "Volksliedstrophe",
                "definition": "Typisch romantische Form: 4-6 Verse, Trochäus/Jambus, 3-4 Hebungen, alternierende Kadenzen",
                "beispiele": "Einfache Wortwahl, eingängiger Rhythmus",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Schlicht, eingängig, leicht zu merken; Nähe zum Volk, wirkt authentisch",
            },
            {
                "begriff": "Sonett",
                "definition": "14 Verse in 4 Strophen: 2 Quartette (je 4 Verse) + 2 Terzette (je 3 Verse), fünfhebiger Jambus",
                "beispiele": "Quartette: abba abba oder abab cdcd; Terzette: verschiedene Reimstellungen",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Kompakter Block mit intensiven Erfahrungen; feste Form verstärkt Wucht der Aussagen",
            },
            {
                "begriff": "Zeilenstil / Simultanstil",
                "definition": "Jede Strophe/Zeile zeigt ein anderes Bild, Szene oder Gefühl; oft kein logischer Zusammenhang",
                "beispiele": "Nur Titel oder großes Thema hält alles zusammen",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Dichte, Tempo, Überwältigung; zeigt Momentaufnahmen des lyrischen Ichs",
            },
            {
                "begriff": "Strophenlose Gedichte",
                "definition": "Gedicht ohne Stropheneinteilung",
                "beispiele": "Durchgängiger Textblock",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Durchgängiger Gedankenfluss; Bewegung, Spannung, Unruhe",
            },
        ]
    },
    {
        "name": "Sprachliche Analyse",
        "beschreibung": "Konzepte für die sprachliche Gedichtanalyse",
        "bidirektional": False,
        "karten": [
            {
                "begriff": "Lyrisches Ich",
                "definition": "Die Sprecherfigur im Gedicht - nicht der reale Autor. Analysiere: Wie spricht es? Was fühlt es? Wie sieht es die Welt?",
                "beispiele": "Ich-Form im Gedicht",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Schafft Nähe, macht Emotionen sichtbar, fokussiert die Welt subjektiv",
            },
            {
                "begriff": "Lyrisches Du",
                "definition": "Angesprochene Figur oder Kraft im Gedicht - z.B. geliebte Person, Naturkraft, Zukunft",
                "beispiele": "Du-Anrede im Gedicht",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Erzeugt Spannung, Sehnsucht, Konflikt; persönlicher; Nähe-Distanz-Verhältnis",
            },
            {
                "begriff": "Kein Lyrisches Ich",
                "definition": "Keine individuelle Sprecherfigur (man, sie) - unpersönlich, distanziert, objektiviert",
                "beispiele": "Besonders im Expressionismus",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Entfremdung, Anonymität, Verlust der Individualität",
            },
            {
                "begriff": "Wortfelder",
                "definition": "Gruppe von Wörtern, die thematisch zusammengehören",
                "beispiele": "Wortfeld 'Tod': sterben, Grab, welken, Ende",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Geschlossene Stimmung, verstärkt bestimmtes Thema",
            },
            {
                "begriff": "Farbfelder",
                "definition": "Wiederholte Farben oder Farbwörter im Gedicht",
                "beispiele": "Schwarz, dunkel, Nacht vs. Gold, hell, Licht",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Liefert sofort Stimmung, kann Symbolik aufbauen, macht Gedicht bildhafter",
            },
            {
                "begriff": "Helle Vokale (i, e)",
                "definition": "Vokale mit hoher Klangfarbe",
                "beispiele": "Licht, fliehen, Liebe",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Leicht, hell, hoch; kann fröhlich, scharf oder nervös wirken",
            },
            {
                "begriff": "Dunkle Vokale (a, o, u)",
                "definition": "Vokale mit tiefer Klangfarbe",
                "beispiele": "Tod, Grab, Nacht, Ruh",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Tief, schwer, dumpf; erzeugt Schwere, Bedrohung, Ernst",
            },
            {
                "begriff": "Optische Raumdarstellung",
                "definition": "Sichtbare Eindrücke: Licht, Farben, Formen, Bewegung",
                "beispiele": "Helles Licht, enge Gassen, weite Felder",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Vermittelt Atmosphäre; Weite vs. Enge (Freiheit/Bedrohung)",
            },
            {
                "begriff": "Akustische Raumdarstellung",
                "definition": "Geräusche, Stimmung, Lautstärke im Gedicht",
                "beispiele": "Lärm der Stadt, Stille der Nacht",
                "zusatz_label": "Wirkung",
                "zusatz_wert": "Lärm = Hektik, Angst; Stille = Einsamkeit, Frieden, Leere",
            },
        ]
    },
    {
        "name": "Epochen",
        "beschreibung": "Romantik und Expressionismus - Merkmale und Motive",
        "bidirektional": True,
        "karten": [
            # Romantik
            {
                "begriff": "Epoche der Romantik",
                "definition": "Literaturepoche 1794-1835 (Frühromantik, Hochromantik, Spätromantik)",
                "beispiele": "Gegenbewegung zu Aufklärung und Weimarer Klassik",
                "zusatz_label": "Merkmale",
                "zusatz_wert": "Betonung des Individuellen, Natur als Freiheitsort, Gefühl vor Vernunft, Interesse an Übernatürlichem",
            },
            {
                "begriff": "Motiv: Nacht (Romantik)",
                "definition": "Nacht oft mit Mond verbunden - Symbol für Sehnsucht, unerreichbare Liebe, das Unendliche",
                "beispiele": "Mondnacht, Sternenhimmel",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Die dunkle, geheimnisvolle Seite der Natur; Verwandlung",
            },
            {
                "begriff": "Motiv: Wandern (Romantik)",
                "definition": "Reisen und Wandern als Streben nach Freiheit und dem Unbekannten",
                "beispiele": "Wanderer, Reisende, Fahrende",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Ablehnung des einförmigen bürgerlichen Lebens/Alltags",
            },
            {
                "begriff": "Motiv: Natur (Romantik)",
                "definition": "Natur als Ort des Friedens und der Weisheit - man kann sich ihr öffnen",
                "beispiele": "Wald, Fluss, Berg, Blume",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Natur gibt Nutzen und Hoffnung, ist immer da",
            },
            {
                "begriff": "Motiv: Sehnsucht (Romantik)",
                "definition": "Zentrales Motiv - Leiden an unerfüllter Sehnsucht",
                "beispiele": "Sehnsucht nach Ferne, Liebe, Vergangenheit",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Romantisches Grundgefühl; Streben nach dem Unerreichbaren",
            },
            {
                "begriff": "Die blaue Blume",
                "definition": "Zentrales Symbol der Romantik - verkörpert Sehnsucht nach dem Unendlichen",
                "beispiele": "Novalis: Heinrich von Ofterdingen",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Verbindung von Natur, Poesie und dem Absoluten",
            },
            # Expressionismus
            {
                "begriff": "Epoche des Expressionismus",
                "definition": "Literaturepoche 1910-1925 - Zeit des kulturellen Umbruchs",
                "beispiele": "Reaktion auf Industrialisierung und gesellschaftliche Spannungen",
                "zusatz_label": "Historischer Kontext",
                "zusatz_wert": "Kulturelle Werte nicht mehr tragfähig; junge Generation verunsichert; Weltuntergangsstimmung",
            },
            {
                "begriff": "Weltuntergangsstimmung (Expressionismus)",
                "definition": "Zeit nach 1900 geprägt von Unruhe und Weltmüdigkeit",
                "beispiele": "Halley'scher Komet 1911, Titanic 1912, Erdbeben San Francisco 1906",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Ereignisse als 'Vorboten einer nahenden Apokalypse' aufgefasst",
            },
            {
                "begriff": "Großstadt (Expressionismus)",
                "definition": "Die Großstadt als zentrales Thema - Industrialisierung und Urbanisierung",
                "beispiele": "Enge, Lärm, Menschenmassen, Fabriken",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Reizüberflutung, Anonymität, Bildung von Armenghettos",
            },
            {
                "begriff": "Ich-Verlust (Expressionismus)",
                "definition": "Der Mensch beherrscht nicht die Dinge - er wird von ihnen beherrscht",
                "beispiele": "Orientierungslosigkeit, Identitätsverlust",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Das Ich verliert seine Orientierung und letztlich sich selbst",
            },
            {
                "begriff": "Verdinglichung (Expressionismus)",
                "definition": "Der Mensch wird zur Ware, austauschbar durch die Dominanz der Maschine",
                "beispiele": "Fließbandarbeit, 'nur noch ein Handgriff'",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Entfremdung des Menschen von seiner Arbeit",
            },
            {
                "begriff": "Ästhetik des Hässlichen",
                "definition": "Bewusste Darstellung von Hässlichem, Tod und Zerfall",
                "beispiele": "Gedichte über Leichen, Verwesung, Krankheit",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Bruch mit traditionellen Wert- und Moralvorstellungen; Darstellung der ganzen Wirklichkeit",
            },
            {
                "begriff": "Natur im Expressionismus",
                "definition": "Natur nicht realistisch, sondern subjektiv und emotional dargestellt",
                "beispiele": "Apokalyptische Landschaften, verzerrte Natur",
                "zusatz_label": "Bedeutung",
                "zusatz_wert": "Visualisierung innerer Erlebnisse; Spiegel des inneren Verfalls",
            },
            {
                "begriff": "Ziele des Expressionismus",
                "definition": "Darstellung der Innenwelten des Menschen - Gefühle und Reaktionen auf die Sinnkrise",
                "beispiele": "Gesellschaftskritik, Anstoß zur Gesellschaftsänderung",
                "zusatz_label": "Frage",
                "zusatz_wert": "Wie wirkt die Wirklichkeit auf das Innere des Menschen?",
            },
        ]
    },
    {
        "name": "Aufbau & Formulierungen",
        "beschreibung": "Struktur der Gedichtinterpretation und Formulierungshilfen",
        "bidirektional": False,
        "karten": [
            {
                "begriff": "Aufbau Gedichtinterpretation",
                "definition": "1) Einleitung 2) Inhalt jeder Strophe 3) Formale Analyse 4) Sprachliche Analyse 5) Epocheneinordnung 6) Fazit",
                "beispiele": "",
                "zusatz_label": "Hinweis",
                "zusatz_wert": "Im Fazit: Bezug auf heute herstellen",
            },
            {
                "begriff": "Aufbau Gedichtvergleich",
                "definition": "1) Einleitung 2) Kurze Zusammenfassung des 'neuen' Gedichts 3) Vergleich der Aspekte 4) Schluss",
                "beispiele": "",
                "zusatz_label": "Hinweis",
                "zusatz_wert": "Im Schluss: Epocheneinordnung + Welches ist zeitgemäßer?",
            },
            {
                "begriff": "Einleitung (Inhalt)",
                "definition": "Gedichtform, Titel, Autor, Thema, Epoche, Erscheinungsjahr",
                "beispiele": "Das Gedicht '[Titel]' von [Autor], erschienen [Jahr], lässt sich der Epoche [Epoche] zuordnen",
                "zusatz_label": "Formulierung",
                "zusatz_wert": "...und thematisiert [Thema]. Es zeigt/verdeutlicht/problematisiert [Kernaussage].",
            },
            {
                "begriff": "Inhaltsangabe Strophen",
                "definition": "Jede Strophe in 1-2 Sätzen wiedergeben",
                "beispiele": "In der ersten Strophe wird ... dargestellt. Die zweite Strophe zeigt ...",
                "zusatz_label": "Typische Verben",
                "zusatz_wert": "beschreibt, schildert, entwickelt, deutet an, kontrastiert, intensiviert, steigert",
            },
            {
                "begriff": "Formale Analyse (Elemente)",
                "definition": "Metrum, Kadenzen, Reimschema, Strophenform, Versanzahl",
                "beispiele": "Das Gedicht besteht aus [X] Strophen zu je [Y] Versen im [Reimschema]",
                "zusatz_label": "Hinweis",
                "zusatz_wert": "Immer Wirkung der formalen Elemente beschreiben!",
            },
            {
                "begriff": "Sprachliche Analyse (Elemente)",
                "definition": "1) Stilmittel 2) Lyrisches Ich/Du 3) Titel 4) Wortfelder/Farbfelder 5) Vokale 6) Raumdarstellung",
                "beispiele": "",
                "zusatz_label": "Hinweis",
                "zusatz_wert": "Stilmittel immer mit Textstelle und Wirkung belegen",
            },
            {
                "begriff": "Titel analysieren",
                "definition": "Was sagt der Titel wörtlich? Zentrale Aussage? Verbindet er einzelne Bilder? Welche Erwartung erzeugt er?",
                "beispiele": "Der Titel weist auf... / lässt erwarten... / verbindet...",
                "zusatz_label": "Aspekte",
                "zusatz_wert": "Ort, Person, Gefühl, Gegenstand, Stimmung, Thema, Perspektive",
            },
        ]
    },
]


def main():
    print("Erstelle Stammdaten...")

    # Create Schulfächer
    for name in SCHULFAECHER:
        Schulfach.objects.get_or_create(name=name)
    print(f"  {len(SCHULFAECHER)} Schulfächer erstellt/aktualisiert")

    # Create Jahrgangsstufen
    for stufe in JAHRGANGSSTUFEN:
        Jahrgangsstufe.objects.get_or_create(stufe=stufe)
    print(f"  {len(JAHRGANGSSTUFEN)} Jahrgangsstufen erstellt/aktualisiert")

    # Get Deutsch and Klasse 13
    deutsch = Schulfach.objects.get(name='Deutsch')
    klasse_13 = Jahrgangsstufe.objects.get(stufe=13)

    print("\nErstelle Lernblöcke...")

    for block_data in LERNBLOECKE:
        lernblock, created = Lernblock.objects.get_or_create(
            name=block_data["name"],
            defaults={
                "beschreibung": block_data["beschreibung"],
                "bidirektional": block_data["bidirektional"],
                "thema": "Gedichtsinterpretation",
                "schulfach": deutsch,
                "jahrgangsstufe": klasse_13,
            }
        )

        if not created:
            # Update existing block with category info
            lernblock.thema = "Gedichtsinterpretation"
            lernblock.schulfach = deutsch
            lernblock.jahrgangsstufe = klasse_13
            lernblock.save()

        status = "erstellt" if created else "aktualisiert"
        print(f"\n  Lernblock '{block_data['name']}' {status}")

        # Create cards
        created_count = 0
        for karte_data in block_data["karten"]:
            karte, card_created = Karteikarte.objects.get_or_create(
                lernblock=lernblock,
                begriff=karte_data["begriff"],
                defaults={
                    "definition": karte_data["definition"],
                    "beispiele": karte_data.get("beispiele", ""),
                    "zusatz_label": karte_data.get("zusatz_label", ""),
                    "zusatz_wert": karte_data.get("zusatz_wert", ""),
                }
            )
            if card_created:
                created_count += 1

        print(f"    {created_count} neue Karten, gesamt: {lernblock.anzahl_karten}")

    # Update existing Stilmittel block with categories
    try:
        stilmittel = Lernblock.objects.get(name="Deutsch - Stilmittel")
        stilmittel.thema = "Gedichtsinterpretation"
        stilmittel.schulfach = deutsch
        stilmittel.jahrgangsstufe = klasse_13
        stilmittel.save()
        print(f"\n  Lernblock 'Deutsch - Stilmittel' kategorisiert")
    except Lernblock.DoesNotExist:
        pass

    print("\n" + "=" * 50)
    print("Zusammenfassung:")
    print(f"  Schulfächer: {Schulfach.objects.count()}")
    print(f"  Jahrgangsstufen: {Jahrgangsstufe.objects.count()}")
    print(f"  Lernblöcke: {Lernblock.objects.count()}")
    print(f"  Karteikarten: {Karteikarte.objects.count()}")


if __name__ == "__main__":
    main()
