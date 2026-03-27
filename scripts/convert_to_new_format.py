#!/usr/bin/env python3
"""
Convert old vocabulary JSON formats to the new lerninhalt schema.
"""
import json
import os
from pathlib import Path
from collections import defaultdict


def convert_a_plus_vokipedia(input_file: Path, output_file: Path, band: int, klasse: int):
    """Convert Vokipedia À plus format to new schema."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('meta', {})
    vokabeln = data.get('vokabeln', [])

    # Filter out metadata entries (those without unite or with metadata-like content)
    real_vokabeln = [
        v for v in vokabeln
        if v.get('unite') is not None
        or (v.get('franzoesisch') and not any(
            keyword in v.get('franzoesisch', '').lower()
            for keyword in ['name des', 'sprache 1', 'sprache 2', 'inhalt', 'fremdsprache', 'sachgebiet']
        ))
    ]

    # Group by unite
    by_unite = defaultdict(list)
    for v in real_vokabeln:
        unite = v.get('unite') or 'Sonstige'
        by_unite[unite].append(v)

    # Build new structure
    inhalt = []
    for unite in sorted(by_unite.keys(), key=lambda x: (isinstance(x, str), x)):
        unite_name = f"Unité {unite}" if isinstance(unite, int) else str(unite)

        # Group by volet within unite
        by_volet = defaultdict(list)
        for v in by_unite[unite]:
            volet = v.get('volet')
            by_volet[volet].append(v)

        bloecke = []
        for volet in sorted(by_volet.keys(), key=lambda x: (x is None, str(x) if x else '')):
            volet_name = f"Volet {volet}" if volet else "Allgemein"

            karten = []
            for v in by_volet[volet]:
                karte = {
                    "vorne": v.get('franzoesisch', ''),
                    "hinten": v.get('deutsch', '')
                }
                # Add example if present
                beispiel = v.get('beispiel') or v.get('beispiel_fr')
                if beispiel:
                    beispiel_de = v.get('beispiel_de')
                    if beispiel_de:
                        karte["beispiel"] = {"fr": beispiel, "de": beispiel_de}
                    else:
                        karte["beispiel"] = beispiel

                if karte["vorne"] and karte["hinten"]:
                    karten.append(karte)

            if karten:
                bloecke.append({
                    "name": volet_name,
                    "bidirektional": True,
                    "karten": karten
                })

        if bloecke:
            inhalt.append({
                "name": unite_name,
                "bloecke": bloecke
            })

    result = {
        "meta": {
            "fach": "Französisch",
            "lehrwerk": "À plus! Nouvelle édition",
            "band": band,
            "klasse": klasse,
            "verlag": "Cornelsen",
            "sprachen": ["Französisch", "Deutsch"],
            "version": "1.0",
            "quelle": meta.get('quelle', 'Vokipedia')
        },
        "felder": {
            "vorderseite": "Français",
            "rueckseite": "Deutsch"
        },
        "inhalt": inhalt
    }

    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Count cards
    total_cards = sum(len(b['karten']) for u in inhalt for b in u['bloecke'])
    print(f"Converted {input_file.name}: {len(inhalt)} units, {total_cards} cards -> {output_file}")


def convert_a_plus_manual(input_file: Path, output_file: Path, band: int, klasse: int):
    """Convert manually extracted À plus vocabulary to new schema."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('meta', {})
    vokabeln = data.get('vokabeln', [])

    # Group by unite
    by_unite = defaultdict(list)
    for v in vokabeln:
        unite = v.get('unite') or 'Sonstige'
        by_unite[unite].append(v)

    # Build new structure
    inhalt = []
    for unite in sorted(by_unite.keys(), key=lambda x: (isinstance(x, str), x)):
        unite_name = f"Unité {unite}" if isinstance(unite, int) else str(unite)

        # Group by volet within unite
        by_volet = defaultdict(list)
        for v in by_unite[unite]:
            volet = v.get('volet')
            by_volet[volet].append(v)

        bloecke = []
        for volet in sorted(by_volet.keys(), key=lambda x: (x is None, str(x) if x else '')):
            volet_name = f"Volet {volet}" if volet else "Allgemein"

            karten = []
            for v in by_volet[volet]:
                karte = {
                    "vorne": v.get('franzoesisch', ''),
                    "hinten": v.get('deutsch', '')
                }
                beispiel = v.get('beispiel')
                if beispiel:
                    karte["beispiel"] = beispiel

                if karte["vorne"] and karte["hinten"]:
                    karten.append(karte)

            if karten:
                bloecke.append({
                    "name": volet_name,
                    "bidirektional": True,
                    "karten": karten
                })

        if bloecke:
            inhalt.append({
                "name": unite_name,
                "bloecke": bloecke
            })

    result = {
        "meta": {
            "fach": "Französisch",
            "lehrwerk": "À plus! Nouvelle édition",
            "band": band,
            "klasse": klasse,
            "verlag": "Cornelsen",
            "sprachen": ["Französisch", "Deutsch"],
            "version": "1.0",
            "quelle": "Lehrbuch (manuell erfasst)"
        },
        "felder": {
            "vorderseite": "Français",
            "rueckseite": "Deutsch"
        },
        "inhalt": inhalt
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total_cards = sum(len(b['karten']) for u in inhalt for b in u['bloecke'])
    print(f"Converted {input_file.name}: {len(inhalt)} units, {total_cards} cards -> {output_file}")


def convert_emotions(input_file: Path, output_file: Path):
    """Convert emotions vocabulary to new schema (already done, just copy)."""
    import shutil
    output_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(input_file, output_file)
    print(f"Copied {input_file.name} -> {output_file}")


def convert_old_vokabeln(input_file: Path, output_dir: Path):
    """Convert old vokabeln_neu.json format."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('meta', {})

    # Access 3 Unit 4 vocabulary
    if 'vokabeln' in data:
        vokabeln = data['vokabeln']

        # Group by chapter
        by_chapter = defaultdict(list)
        for v in vokabeln:
            chapter = v.get('chapter', 1)
            by_chapter[chapter].append(v)

        bloecke = []
        for chapter in sorted(by_chapter.keys()):
            karten = []
            for v in by_chapter[chapter]:
                karte = {
                    "vorne": v.get('englisch', ''),
                    "hinten": v.get('deutsch', '')
                }
                if v.get('page'):
                    karte["seite"] = str(v['page'])
                if karte["vorne"] and karte["hinten"]:
                    karten.append(karte)

            if karten:
                bloecke.append({
                    "name": f"Part {chapter}",
                    "bidirektional": True,
                    "karten": karten
                })

        if bloecke:
            result = {
                "meta": {
                    "fach": "Englisch",
                    "lehrwerk": meta.get('buch', 'Access'),
                    "band": 3,
                    "klasse": meta.get('klasse', 7),
                    "verlag": "Cornelsen",
                    "sprachen": ["Englisch", "Deutsch"],
                    "version": "1.0"
                },
                "felder": {
                    "vorderseite": "English",
                    "rueckseite": "Deutsch"
                },
                "inhalt": [{
                    "name": f"Unit {meta.get('unit', 4)}",
                    "bloecke": bloecke
                }]
            }

            output_file = output_dir / "englisch" / "access_3_unit4.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            total_cards = sum(len(b['karten']) for b in bloecke)
            print(f"Converted vokabeln (Access): {total_cards} cards -> {output_file}")


def main():
    base_dir = Path("/home/marc/git/karteikarten/docs/input")
    output_dir = Path("/home/marc/git/karteikarten/docs/input/converted")

    # À plus Band 1 (Klasse 6) - from 7/a plus (manual)
    # Note: The folder "7/a plus" contains À plus Band 1 für Klasse 7
    input_file = base_dir / "7" / "a plus" / "vokabeln.json"
    if input_file.exists():
        convert_a_plus_manual(
            input_file,
            output_dir / "franzoesisch" / "a_plus_band1_klasse7.json",
            band=1,
            klasse=7
        )

    # À plus Band 2 (Klasse 7) - from Vokipedia
    input_file = base_dir / "a_plus_2" / "vokabeln.json"
    if input_file.exists():
        convert_a_plus_vokipedia(
            input_file,
            output_dir / "franzoesisch" / "a_plus_band2_klasse7.json",
            band=2,
            klasse=7
        )

    # À plus Band 3 (Klasse 8) - from Vokipedia
    input_file = base_dir / "a_plus_3" / "vokabeln.json"
    if input_file.exists():
        convert_a_plus_vokipedia(
            input_file,
            output_dir / "franzoesisch" / "a_plus_band3_klasse8.json",
            band=3,
            klasse=8
        )

    # À plus Band 4 (Klasse 9) - from Vokipedia
    input_file = base_dir / "a_plus_4" / "vokabeln.json"
    if input_file.exists():
        convert_a_plus_vokipedia(
            input_file,
            output_dir / "franzoesisch" / "a_plus_band4_klasse9.json",
            band=4,
            klasse=9
        )

    # Emotions - already in new format
    input_file = base_dir / "emotions_klasse7.json"
    if input_file.exists():
        convert_emotions(
            input_file,
            output_dir / "englisch" / "emotions_klasse7.json"
        )

    # Old vokabeln_neu.json
    input_file = base_dir / "vokabeln_neu.json"
    if input_file.exists():
        convert_old_vokabeln(input_file, output_dir)

    print("\nConversion complete!")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
