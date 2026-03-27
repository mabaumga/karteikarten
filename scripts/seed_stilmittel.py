#!/usr/bin/env python
"""Seed database with Stilmittel from PDF."""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from karteikarten.models import Lernblock, Karteikarte

STILMITTEL = [
    {
        "begriff": "Alliteration",
        "definition": "Wiederholung des Anfangslauts bei aufeinanderfolgenden Wörtern",
        "beispiele": "Milch macht müde Männer munter",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Erzeugt Klangbindung; hebt Wörter hervor; wirkt einprägsam oder rhythmisch",
    },
    {
        "begriff": "Anapher",
        "definition": "Wiederholung eines Wortes oder einer Wortgruppe am Versanfang",
        "beispiele": "Ich fühle... / Ich weiß...",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Verstärkt Aussagen; schafft Struktur",
    },
    {
        "begriff": "Antithese",
        "definition": "Gegenüberstellung von Gegensätzen",
        "beispiele": "Himmel und Hölle",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Betont Konflikte; zeigt Spannung; schärft Bedeutungsgegensätze",
    },
    {
        "begriff": "Chiasmus",
        "definition": "Überkreuzstellung von Satzgliedern (syntaktische Spiegelung)",
        "beispiele": "Ich liebe die Sprache, die Sprache liebt mich",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Schafft starke Gegenüberstellung",
    },
    {
        "begriff": "Correctio",
        "definition": "Selbstkorrektur des Gesagten",
        "beispiele": "Es war schlecht, nein katastrophal",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Verstärkt innere Bewegung oder Unsicherheit",
    },
    {
        "begriff": "Ellipse",
        "definition": "Grammatikalisch unvollständiger Satz (Auslassung)",
        "beispiele": "Keine Zeit. Keine Ruhe.",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Beschleunigt, erzeugt Druck, wirkt unmittelbar",
    },
    {
        "begriff": "Enjambement",
        "definition": "Satz geht über das Versende hinaus in die nächste Zeile",
        "beispiele": "Ich gehe fort / und suche weiter",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Erzeugt Spannung und Bewegung",
    },
    {
        "begriff": "Epipher",
        "definition": "Wiederholung eines Wortes oder einer Wortgruppe am Versende",
        "beispiele": "Ich will das. Du liebst das.",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Verbindung und markiert zentrale Begriffe",
    },
    {
        "begriff": "Euphemismus",
        "definition": "Beschönigung eines unangenehmen Sachverhalts",
        "beispiele": "Er ist von uns gegangen (statt: Er ist gestorben)",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Verharmlost, mildert Härte",
    },
    {
        "begriff": "Hyperbel",
        "definition": "Starke Übertreibung",
        "beispiele": "Es dauert 1000 Jahre",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Verstärkt Gefühle, macht Intensität, dramatisiert",
    },
    {
        "begriff": "Inversion",
        "definition": "Umstellung der normalen Satzstellung",
        "beispiele": "Unendlich ist die Liebe",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Verleiht dichterischen Klang",
    },
    {
        "begriff": "Ironie",
        "definition": "Das Gegenteil des Gemeinten wird gesagt",
        "beispiele": "Na toll, wieder Regen",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Erzeugt Humor oder Kritik",
    },
    {
        "begriff": "Klimax",
        "definition": "Steigerung von Wörtern oder Satzteilen",
        "beispiele": "Ich kam, sah und siegte",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Erhöht Spannung, macht Aussage stärker",
    },
    {
        "begriff": "Metapher",
        "definition": "Bildhafte Übertragung (verkürzter Vergleich ohne 'wie')",
        "beispiele": "Das Herz brennt",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Macht Abstraktes anschaulich",
    },
    {
        "begriff": "Neologismus",
        "definition": "Wortneuschöpfung",
        "beispiele": "Seelenflimmern",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Schafft neue Bedeutungsebenen",
    },
    {
        "begriff": "Paradoxon",
        "definition": "Scheinbar widersprüchliche Aussage",
        "beispiele": "Ich weiß, dass ich nichts weiß",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Regt zum Nachdenken an",
    },
    {
        "begriff": "Parallelismus",
        "definition": "Gleicher Satzbau in aufeinanderfolgenden Sätzen",
        "beispiele": "Er lacht laut, sie weint leise",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Betont Gegensätze oder Zusammenhänge",
    },
    {
        "begriff": "Parataxe",
        "definition": "Aneinanderreihung von Hauptsätzen (Satzreihe)",
        "beispiele": "Er kam. Er sah. Er ging.",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Tempo, Härte, Sachlichkeit",
    },
    {
        "begriff": "Parenthese",
        "definition": "Einschub in einen Satz",
        "beispiele": "Ich gehe, wie immer, zu spät",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Wirkt kommentierend, nachdenklich",
    },
    {
        "begriff": "Personifikation",
        "definition": "Vermenschlichung von Dingen oder abstrakten Begriffen",
        "beispiele": "Die Nacht umarmt mich",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Emotionalisiert, macht Dinge lebendig",
    },
    {
        "begriff": "Rhetorische Frage",
        "definition": "Frage, auf die keine Antwort erwartet wird (Aussage als Frage)",
        "beispiele": "Wer konnte das vergessen?",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Verstärkt die Aussage",
    },
    {
        "begriff": "Symbol",
        "definition": "Zeichen mit tieferer, übertragener Bedeutung",
        "beispiele": "Herz = Liebe, Taube = Frieden",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Macht Wahrnehmung intensiver",
    },
    {
        "begriff": "Synästhesie",
        "definition": "Verbindung mehrerer Sinneseindrücke",
        "beispiele": "Warmer Klang, schreiende Farben",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Gibt Aussage Gewicht, intensiviert Wahrnehmung",
    },
    {
        "begriff": "Tautologie",
        "definition": "Wiederholung mit gleichem oder ähnlichem Sinn",
        "beispiele": "Weißer Schimmel, immer und ewig",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Gibt Aussage Gewicht, Verstärkung",
    },
    {
        "begriff": "Verniedlichung (Diminutiv)",
        "definition": "Verkleinerungsform eines Wortes",
        "beispiele": "Häuschen, Blümchen, Kindchen",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Wirkt zart, niedlich, manchmal ironisch",
    },
    {
        "begriff": "Vergleich",
        "definition": "Verbindung zweier Bereiche mit 'wie' oder 'als'",
        "beispiele": "Stark wie ein Löwe",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Macht Bilder anschaulich, lenkt Fokus",
    },
    {
        "begriff": "Wiederholung (Repetitio)",
        "definition": "Wiederholung eines Wortes oder Ausdrucks",
        "beispiele": "Nie, nie vergesse ich das",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Lenkt Fokus, erzeugt Dringlichkeit",
    },
]


def main():
    # Create or get Lernblock
    lernblock, created = Lernblock.objects.get_or_create(
        name="Deutsch - Stilmittel",
        defaults={
            "beschreibung": "Rhetorische Stilmittel für die Gedichtinterpretation",
            "bidirektional": True,
        }
    )

    if created:
        print(f"Lernblock '{lernblock.name}' erstellt.")
    else:
        print(f"Lernblock '{lernblock.name}' existiert bereits.")

    # Add cards
    created_count = 0
    for stilmittel in STILMITTEL:
        karte, created = Karteikarte.objects.get_or_create(
            lernblock=lernblock,
            begriff=stilmittel["begriff"],
            defaults={
                "definition": stilmittel["definition"],
                "beispiele": stilmittel["beispiele"],
                "zusatz_label": stilmittel["zusatz_label"],
                "zusatz_wert": stilmittel["zusatz_wert"],
            }
        )
        if created:
            created_count += 1
            print(f"  + {stilmittel['begriff']}")
        else:
            print(f"  ~ {stilmittel['begriff']} (existiert bereits)")

    print(f"\n{created_count} neue Karten erstellt.")
    print(f"Gesamt: {lernblock.anzahl_karten} Karten im Lernblock.")


if __name__ == "__main__":
    main()
