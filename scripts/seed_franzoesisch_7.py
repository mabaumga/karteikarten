#!/usr/bin/env python
"""
Seed-Skript für Französisch-Vokabeln Klasse 7 (À plus!)

Erstellt Lernblöcke basierend auf den Unités und Modulen des Lehrbuchs.
"""

import os
import sys
import json
import django

# Django Setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from karteikarten.models import Lernblock, Karteikarte, Schulfach, Jahrgangsstufe


def load_vokabeln():
    """Lade Vokabeln aus der JSON-Datei."""
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'docs', 'input', '7', 'a plus', 'vokabeln.json'
    )
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_or_create_schulfach():
    """Hole oder erstelle das Schulfach Französisch."""
    schulfach, created = Schulfach.objects.get_or_create(
        name='Französisch',
        defaults={'beschreibung': 'Französisch als Fremdsprache'}
    )
    if created:
        print(f"✓ Schulfach 'Französisch' erstellt")
    return schulfach


def get_jahrgangsstufe():
    """Hole Jahrgangsstufe 7."""
    return Jahrgangsstufe.objects.get(stufe=7)


def gruppiere_vokabeln(vokabeln):
    """
    Gruppiere Vokabeln in sinnvolle Lernblöcke.

    Struktur:
    - Pro Unité einen Block (Vocabulaire thématique + alle Volets)
    - Module als separate Blöcke
    """
    bloecke = {}

    for vok in vokabeln:
        unite = vok['unite']
        volet = vok['volet']

        # Bestimme Block-Schlüssel
        if volet and isinstance(volet, str) and volet.startswith('Module'):
            # Module als separater Block
            key = f"module_{unite}"
            block_name = f"Französisch 7 - {volet}"
            thema = volet
        else:
            # Unité-Block (Vocabulaire + alle Volets)
            key = f"unite_{unite}"
            block_name = f"Französisch 7 - Unité {unite}"
            thema = f"Unité {unite}"

        if key not in bloecke:
            bloecke[key] = {
                'name': block_name,
                'thema': thema,
                'vokabeln': []
            }

        bloecke[key]['vokabeln'].append(vok)

    return bloecke


def erstelle_lernbloecke(bloecke, schulfach, jahrgangsstufe):
    """Erstelle Lernblöcke und Karteikarten in der Datenbank."""

    # Sortiere Blöcke nach Reihenfolge (Unités vor Modulen)
    sorted_keys = sorted(bloecke.keys(), key=lambda k: (
        0 if k.startswith('unite') else 1,
        int(k.split('_')[1])
    ))

    gesamt_karten = 0

    for key in sorted_keys:
        block_data = bloecke[key]

        # Erstelle oder aktualisiere Lernblock
        lernblock, created = Lernblock.objects.get_or_create(
            name=block_data['name'],
            defaults={
                'beschreibung': f"Vokabeln aus À plus! Klasse 7 - {block_data['thema']}",
                'thema': block_data['thema'],
                'schulfach': schulfach,
                'jahrgangsstufe': jahrgangsstufe,
                'bidirektional': True,  # Vokabeln in beide Richtungen lernen
                'lehrbuch': 'À plus! 3 (Cornelsen)'
            }
        )

        if not created:
            # Block existiert bereits - lösche alte Karten
            alte_karten = lernblock.karteikarten.count()
            lernblock.karteikarten.all().delete()
            print(f"  → {alte_karten} alte Karten gelöscht")

        # Erstelle Karteikarten
        karten_erstellt = 0
        for vok in block_data['vokabeln']:
            # Bestimme Volet-Info für Zusatzfeld
            volet = vok['volet']
            if volet is None:
                volet_info = "Vocabulaire thématique"
            elif isinstance(volet, int):
                volet_info = f"Volet {volet}"
            else:
                volet_info = volet

            Karteikarte.objects.create(
                lernblock=lernblock,
                begriff=vok['franzoesisch'],
                definition=vok['deutsch'],
                beispiele=vok['beispiel'] or '',
                zusatz_label='Abschnitt',
                zusatz_wert=volet_info
            )
            karten_erstellt += 1

        action = "erstellt" if created else "aktualisiert"
        print(f"✓ Lernblock '{block_data['name']}' {action}: {karten_erstellt} Karten")
        gesamt_karten += karten_erstellt

    return gesamt_karten


def main():
    print("=" * 60)
    print("Französisch-Vokabeln À plus! Klasse 7 importieren")
    print("=" * 60)
    print()

    # Lade Vokabeln
    print("Lade Vokabeln aus JSON-Datei...")
    data = load_vokabeln()
    vokabeln = data['vokabeln']
    print(f"  → {len(vokabeln)} Vokabeln gefunden")
    print()

    # Hole/erstelle Schulfach und Jahrgangsstufe
    print("Bereite Datenbank vor...")
    schulfach = get_or_create_schulfach()
    jahrgangsstufe = get_jahrgangsstufe()
    print(f"  → Schulfach: {schulfach.name}")
    print(f"  → Jahrgangsstufe: {jahrgangsstufe.stufe}")
    print()

    # Gruppiere Vokabeln
    print("Gruppiere Vokabeln in Lernblöcke...")
    bloecke = gruppiere_vokabeln(vokabeln)
    print(f"  → {len(bloecke)} Lernblöcke werden erstellt")
    print()

    # Zeige Übersicht
    print("Lernblock-Übersicht:")
    print("-" * 40)
    for key in sorted(bloecke.keys(), key=lambda k: (0 if k.startswith('unite') else 1, int(k.split('_')[1]))):
        block = bloecke[key]
        print(f"  {block['name']}: {len(block['vokabeln'])} Vokabeln")
    print("-" * 40)
    print()

    # Erstelle Lernblöcke
    print("Erstelle Lernblöcke und Karteikarten...")
    gesamt = erstelle_lernbloecke(bloecke, schulfach, jahrgangsstufe)
    print()

    print("=" * 60)
    print(f"Import abgeschlossen: {gesamt} Karteikarten in {len(bloecke)} Lernblöcken")
    print("=" * 60)


if __name__ == '__main__':
    main()
