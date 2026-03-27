#!/usr/bin/env python
"""
Seed-Skript für Englisch-Vokabeln Access 3, Unit 4 (Klasse 7)

Erstellt zwei Lernblöcke:
1. Vokabeln aus Access 3, Unit 4 (Chapter 1-3)
2. Emotionswörter (Inside Out - JOY, ANGER, DISGUST, FEAR, SURPRISE, SADNESS)
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
        'docs', 'input', 'vokabeln_neu.json'
    )
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_or_create_schulfach():
    """Hole oder erstelle das Schulfach Englisch."""
    schulfach, created = Schulfach.objects.get_or_create(
        name='Englisch',
        defaults={'beschreibung': 'Englisch als Fremdsprache'}
    )
    if created:
        print(f"  Schulfach 'Englisch' erstellt")
    return schulfach


def get_jahrgangsstufe():
    """Hole Jahrgangsstufe 7."""
    return Jahrgangsstufe.objects.get(stufe=7)


def erstelle_vokabel_lernblock(data, schulfach, jahrgangsstufe):
    """Erstelle Lernblock für die Vokabeln aus Access 3, Unit 4."""

    meta = data['meta']
    vokabeln = data['vokabeln']

    block_name = f"Englisch 7 - {meta['buch']} Unit {meta['unit']}"

    lernblock, created = Lernblock.objects.get_or_create(
        name=block_name,
        defaults={
            'beschreibung': f"Vokabeln aus {meta['buch']}, Unit {meta['unit']} (Chapter 1-3)",
            'thema': f"Unit {meta['unit']}",
            'schulfach': schulfach,
            'jahrgangsstufe': jahrgangsstufe,
            'bidirektional': True,
            'lehrbuch': f"{meta['buch']} (Cornelsen)"
        }
    )

    if not created:
        alte_karten = lernblock.karteikarten.count()
        lernblock.karteikarten.all().delete()
        print(f"    {alte_karten} alte Karten geloescht")

    karten_erstellt = 0
    for vok in vokabeln:
        Karteikarte.objects.create(
            lernblock=lernblock,
            begriff=vok['englisch'],
            definition=vok['deutsch'],
            beispiele='',
            zusatz_label='Chapter/Page',
            zusatz_wert=f"Chapter {vok['chapter']}, p. {vok['page']}"
        )
        karten_erstellt += 1

    action = "erstellt" if created else "aktualisiert"
    print(f"  Lernblock '{block_name}' {action}: {karten_erstellt} Karten")

    return karten_erstellt


def erstelle_emotionen_lernblock(data, schulfach, jahrgangsstufe):
    """Erstelle Lernblock für die Emotionswörter (Inside Out)."""

    emotionen = data['emotionen']

    block_name = "Englisch 7 - Emotions (Inside Out)"

    lernblock, created = Lernblock.objects.get_or_create(
        name=block_name,
        defaults={
            'beschreibung': 'Gefuehlswoerter nach Kategorien aus dem Film Inside Out',
            'thema': 'Emotions & Feelings',
            'schulfach': schulfach,
            'jahrgangsstufe': jahrgangsstufe,
            'bidirektional': True,
            'lehrbuch': 'Access 3 (Cornelsen)'
        }
    )

    if not created:
        alte_karten = lernblock.karteikarten.count()
        lernblock.karteikarten.all().delete()
        print(f"    {alte_karten} alte Karten geloescht")

    karten_erstellt = 0
    for kategorie in emotionen['kategorien']:
        emotion = kategorie['emotion']
        for wort in kategorie['woerter']:
            Karteikarte.objects.create(
                lernblock=lernblock,
                begriff=wort['englisch'],
                definition=wort['deutsch'],
                beispiele='',
                zusatz_label='Emotion',
                zusatz_wert=emotion
            )
            karten_erstellt += 1

    action = "erstellt" if created else "aktualisiert"
    print(f"  Lernblock '{block_name}' {action}: {karten_erstellt} Karten")

    return karten_erstellt


def main():
    print("=" * 60)
    print("Englisch-Vokabeln Access 3 Unit 4 importieren")
    print("=" * 60)
    print()

    # Lade Vokabeln
    print("Lade Vokabeln aus JSON-Datei...")
    data = load_vokabeln()
    print(f"  {len(data['vokabeln'])} Vokabeln gefunden")

    gesamt_emotionen = sum(len(k['woerter']) for k in data['emotionen']['kategorien'])
    print(f"  {gesamt_emotionen} Emotionswoerter in {len(data['emotionen']['kategorien'])} Kategorien")
    print()

    # Hole/erstelle Schulfach und Jahrgangsstufe
    print("Bereite Datenbank vor...")
    schulfach = get_or_create_schulfach()
    jahrgangsstufe = get_jahrgangsstufe()
    print(f"  Schulfach: {schulfach.name}")
    print(f"  Jahrgangsstufe: {jahrgangsstufe.stufe}")
    print()

    # Erstelle Lernblöcke
    print("Erstelle Lernbloecke und Karteikarten...")
    print()

    karten_vokabeln = erstelle_vokabel_lernblock(data, schulfach, jahrgangsstufe)
    karten_emotionen = erstelle_emotionen_lernblock(data, schulfach, jahrgangsstufe)

    gesamt = karten_vokabeln + karten_emotionen

    print()
    print("=" * 60)
    print(f"Import abgeschlossen: {gesamt} Karteikarten in 2 Lernbloecken")
    print(f"  - Access 3 Unit 4 Vokabeln: {karten_vokabeln} Karten")
    print(f"  - Emotions (Inside Out): {karten_emotionen} Karten")
    print("=" * 60)


if __name__ == '__main__':
    main()
