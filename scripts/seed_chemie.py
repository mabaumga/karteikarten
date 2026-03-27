#!/usr/bin/env python
"""Seed database with Chemistry flashcards for Jahrgangsstufe 13."""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from karteikarten.models import Lernblock, Karteikarte, Schulfach, Jahrgangsstufe

# =============================================================================
# Block 1: Fette und Seifen
# =============================================================================
FETTE_UND_SEIFEN = [
    # Aufbau von Fetten
    {
        "begriff": "Fett (chemischer Aufbau)",
        "definition": "Ester aus Glycerin (dreiwertiger Alkohol) und drei Fettsaeure-Molekuelen",
        "beispiele": "Triglycerid = Glycerin + 3 Fettsaeuren",
        "zusatz_label": "Merke",
        "zusatz_wert": "Fette sind Triacylglycerine (Triglyceride)",
    },
    {
        "begriff": "Glycerin",
        "definition": "Dreiwertiger Alkohol mit drei OH-Gruppen, bildet das Rueckgrat von Fetten",
        "beispiele": "Propan-1,2,3-triol: CH2OH-CHOH-CH2OH",
        "zusatz_label": "Funktion",
        "zusatz_wert": "Verknuepft drei Fettsaeuren ueber Esterbindungen",
    },
    {
        "begriff": "Fettsaeure",
        "definition": "Langkettige Carbonsaeure mit einer Carboxylgruppe (-COOH) am Ende",
        "beispiele": "Palmitinsaeure (C16), Oelsaeure (C18:1), Stearinsaeure (C18)",
        "zusatz_label": "Kettenlänge",
        "zusatz_wert": "Meist 12-24 C-Atome",
    },
    {
        "begriff": "Gesaettigte Fettsaeure",
        "definition": "Fettsaeure ohne Doppelbindungen in der Kohlenstoffkette",
        "beispiele": "Palmitinsaeure (C16:0), Stearinsaeure (C18:0)",
        "zusatz_label": "Eigenschaft",
        "zusatz_wert": "Hoher Schmelzpunkt, bei Raumtemperatur oft fest (tierische Fette)",
    },
    {
        "begriff": "Ungesaettigte Fettsaeure",
        "definition": "Fettsaeure mit einer oder mehreren Doppelbindungen in der Kohlenstoffkette",
        "beispiele": "Oelsaeure (C18:1), Linolsaeure (C18:2), Linolensaeure (C18:3)",
        "zusatz_label": "Eigenschaft",
        "zusatz_wert": "Niedriger Schmelzpunkt, meist fluessig (pflanzliche Oele)",
    },
    {
        "begriff": "cis-/trans-Isomerie bei Fettsaeuren",
        "definition": "Raeumliche Anordnung an der Doppelbindung: cis (gleiche Seite) oder trans (gegenueber)",
        "beispiele": "cis-Oelsaeure (natuerlich) vs. trans-Fettsaeuren (gehaertet)",
        "zusatz_label": "Bedeutung",
        "zusatz_wert": "cis-Form erzeugt Knick in der Kette, trans-Form ist gestreckter",
    },
    {
        "begriff": "Esterbindung",
        "definition": "Chemische Bindung zwischen Saeure und Alkohol unter Wasserabspaltung",
        "beispiele": "R-COOH + HO-R' -> R-COO-R' + H2O",
        "zusatz_label": "Im Fett",
        "zusatz_wert": "Drei Esterbindungen pro Triglycerid-Molekuel",
    },
    # Reaktionen von Fetten
    {
        "begriff": "Veresterung",
        "definition": "Reaktion von Alkohol und Saeure zu Ester unter Wasserabspaltung (Kondensation)",
        "beispiele": "Glycerin + 3 Fettsaeuren -> Fett + 3 H2O",
        "zusatz_label": "Katalyse",
        "zusatz_wert": "Saeurekatalysiert, reversible Gleichgewichtsreaktion",
    },
    {
        "begriff": "Verseifung",
        "definition": "Alkalische Hydrolyse von Fetten zu Glycerin und Fettsaeuresalzen (Seifen)",
        "beispiele": "Fett + 3 NaOH -> Glycerin + 3 Natriumsalze der Fettsaeuren",
        "zusatz_label": "Unterschied",
        "zusatz_wert": "Irreversibel (im Gegensatz zur sauren Hydrolyse)",
    },
    {
        "begriff": "Hydrolyse von Fetten",
        "definition": "Spaltung der Esterbindungen durch Wasser, Rueckreaktion der Veresterung",
        "beispiele": "Fett + 3 H2O -> Glycerin + 3 Fettsaeuren",
        "zusatz_label": "Arten",
        "zusatz_wert": "Sauer (reversibel) oder alkalisch/Verseifung (irreversibel)",
    },
    {
        "begriff": "Fetthaertung",
        "definition": "Katalytische Hydrierung von ungesaettigten Fettsaeuren zu gesaettigten",
        "beispiele": "Pflanzliches Oel + H2 (Ni-Katalysator) -> festes Fett",
        "zusatz_label": "Anwendung",
        "zusatz_wert": "Herstellung von Margarine, Problem: trans-Fettsaeuren",
    },
    # Seifen und Tenside
    {
        "begriff": "Seife",
        "definition": "Natriumsalz oder Kaliumsalz einer langkettigen Fettsaeure",
        "beispiele": "Natriumstearat (C17H35COO-Na+), Natriumoleat",
        "zusatz_label": "Herstellung",
        "zusatz_wert": "Durch Verseifung von Fetten mit NaOH oder KOH",
    },
    {
        "begriff": "Tensid",
        "definition": "Grenzflaechenaktive Substanz mit hydrophilem Kopf und hydrophobem Schwanz",
        "beispiele": "Seifen, Alkylsulfate (SDS), Alkylbenzolsulfonate",
        "zusatz_label": "Funktion",
        "zusatz_wert": "Setzen Oberflaechenspannung herab, emulgieren Fette",
    },
    {
        "begriff": "Hydrophil",
        "definition": "Wasserliebend/wasseranziehend, meist polare oder ionische Gruppen",
        "beispiele": "Carboxylat-Gruppe (-COO-), Sulfat-Gruppe (-OSO3-)",
        "zusatz_label": "Bei Tensiden",
        "zusatz_wert": "Der polare Kopf der Tensidmolekuele",
    },
    {
        "begriff": "Hydrophob (lipophil)",
        "definition": "Wasserabstossend/fettliebend, meist unpolare Kohlenwasserstoffketten",
        "beispiele": "Lange Alkylketten wie -C17H35",
        "zusatz_label": "Bei Tensiden",
        "zusatz_wert": "Der unpolare Schwanz der Tensidmolekuele",
    },
    {
        "begriff": "Micelle",
        "definition": "Kugelfoermige Anordnung von Tensidmolekuelen in Wasser mit Fett im Inneren",
        "beispiele": "Seifenmicelle umschliesst Schmutzpartikel",
        "zusatz_label": "Aufbau",
        "zusatz_wert": "Hydrophobe Schwaenze nach innen, hydrophile Koepfe nach aussen",
    },
    {
        "begriff": "Waschwirkung von Seifen",
        "definition": "Emulgierung von Fetten durch Micellenbildung und Herabsetzung der Oberflaechenspannung",
        "beispiele": "Schmutz wird in Micellen eingeschlossen und weggewaschen",
        "zusatz_label": "Schritte",
        "zusatz_wert": "1. Benetzung, 2. Abloesung, 3. Emulgierung, 4. Abtransport",
    },
    {
        "begriff": "Kalkseife",
        "definition": "Schwerloesliche Calciumsalze von Fettsaeuren, die in hartem Wasser entstehen",
        "beispiele": "2 R-COO-Na + Ca2+ -> (R-COO)2Ca + 2 Na+",
        "zusatz_label": "Problem",
        "zusatz_wert": "Graue Ablagerungen, reduzierte Waschwirkung",
    },
    {
        "begriff": "Emulsion",
        "definition": "Fein verteilte Mischung zweier nicht mischbarer Fluessigkeiten",
        "beispiele": "Milch (Fett in Wasser), Mayonnaise (Oel in Wasser)",
        "zusatz_label": "Stabilisierung",
        "zusatz_wert": "Durch Emulgatoren (Tenside) stabilisiert",
    },
]

# =============================================================================
# Block 2: Protolysegleichgewichte
# =============================================================================
PROTOLYSEGLEICHGEWICHTE = [
    # Grundlagen Saeuren und Basen
    {
        "begriff": "Saeure (nach Broensted)",
        "definition": "Protonendonator - Teilchen, das Protonen (H+) abgeben kann",
        "beispiele": "HCl, H2SO4, CH3COOH, H3O+",
        "zusatz_label": "Reaktion",
        "zusatz_wert": "HA -> A- + H+",
    },
    {
        "begriff": "Base (nach Broensted)",
        "definition": "Protonenakzeptor - Teilchen, das Protonen (H+) aufnehmen kann",
        "beispiele": "NaOH, NH3, CH3COO-, OH-",
        "zusatz_label": "Reaktion",
        "zusatz_wert": "B + H+ -> BH+",
    },
    {
        "begriff": "Protolyse",
        "definition": "Protonenuebertragungsreaktion zwischen Saeure und Base",
        "beispiele": "HCl + H2O -> Cl- + H3O+",
        "zusatz_label": "Merke",
        "zusatz_wert": "Immer zwei konjugierte Saeure-Base-Paare beteiligt",
    },
    {
        "begriff": "Konjugiertes Saeure-Base-Paar",
        "definition": "Saeure und Base, die sich nur um ein Proton unterscheiden",
        "beispiele": "HCl/Cl-, NH4+/NH3, H2O/OH-, H3O+/H2O",
        "zusatz_label": "Zusammenhang",
        "zusatz_wert": "Starke Saeure -> schwache konjugierte Base und umgekehrt",
    },
    {
        "begriff": "Ampholyt",
        "definition": "Teilchen, das sowohl als Saeure als auch als Base reagieren kann",
        "beispiele": "H2O, HCO3-, HSO4-, Aminosaeuren",
        "zusatz_label": "Wasser",
        "zusatz_wert": "H2O kann H+ abgeben (Saeure) oder aufnehmen (Base)",
    },
    {
        "begriff": "Starke Saeure",
        "definition": "Saeure, die in Wasser vollstaendig dissoziiert (praktisch irreversibel)",
        "beispiele": "HCl, HNO3, H2SO4, HClO4",
        "zusatz_label": "pKs-Wert",
        "zusatz_wert": "pKs < 0 (sehr kleine Ks)",
    },
    {
        "begriff": "Schwache Saeure",
        "definition": "Saeure, die in Wasser nur teilweise dissoziiert (Gleichgewicht)",
        "beispiele": "CH3COOH (Essigsaeure), H2CO3, HF, H2S",
        "zusatz_label": "pKs-Wert",
        "zusatz_wert": "pKs > 0 (messbare Gleichgewichtskonstante)",
    },
    # pH-Wert und Berechnungen
    {
        "begriff": "pH-Wert",
        "definition": "Negativer dekadischer Logarithmus der Hydroniumionen-Konzentration",
        "beispiele": "pH = -lg[H3O+]; pH 7 = neutral, pH < 7 = sauer, pH > 7 = basisch",
        "zusatz_label": "Formel",
        "zusatz_wert": "pH = -lg(c(H3O+))",
    },
    {
        "begriff": "pOH-Wert",
        "definition": "Negativer dekadischer Logarithmus der Hydroxidionen-Konzentration",
        "beispiele": "pOH = -lg[OH-]",
        "zusatz_label": "Zusammenhang",
        "zusatz_wert": "pH + pOH = 14 (bei 25 Grad C)",
    },
    {
        "begriff": "Autoprotolyse des Wassers",
        "definition": "Reaktion von Wassermolekuelen untereinander zu H3O+ und OH-",
        "beispiele": "2 H2O <-> H3O+ + OH-",
        "zusatz_label": "Ionenprodukt",
        "zusatz_wert": "Kw = [H3O+] * [OH-] = 10^-14 mol2/L2 (bei 25 Grad C)",
    },
    {
        "begriff": "Ionenprodukt des Wassers (Kw)",
        "definition": "Produkt der Konzentrationen von H3O+ und OH- im Gleichgewicht",
        "beispiele": "Kw = 10^-14 mol2/L2 bei 25 Grad C",
        "zusatz_label": "Anwendung",
        "zusatz_wert": "Berechnung von pH oder pOH, wenn einer bekannt ist",
    },
    {
        "begriff": "Saeurestaerkekonstante Ks",
        "definition": "Gleichgewichtskonstante fuer die Protolysereaktion einer Saeure",
        "beispiele": "HA + H2O <-> A- + H3O+; Ks = [A-][H3O+]/[HA]",
        "zusatz_label": "Bedeutung",
        "zusatz_wert": "Je groesser Ks, desto staerker die Saeure",
    },
    {
        "begriff": "pKs-Wert",
        "definition": "Negativer dekadischer Logarithmus der Saeurestaerkekonstante",
        "beispiele": "pKs(Essigsaeure) = 4,76; pKs(HCl) < 0",
        "zusatz_label": "Formel",
        "zusatz_wert": "pKs = -lg(Ks); je kleiner pKs, desto staerker die Saeure",
    },
    {
        "begriff": "pKb-Wert",
        "definition": "Negativer dekadischer Logarithmus der Basenstaerkekonstante",
        "beispiele": "pKb(NH3) = 4,75",
        "zusatz_label": "Zusammenhang",
        "zusatz_wert": "pKs + pKb = 14 (fuer konjugiertes Paar bei 25 Grad C)",
    },
    {
        "begriff": "pH-Berechnung starke Saeure",
        "definition": "pH = -lg(c0) bei vollstaendiger Dissoziation",
        "beispiele": "0,01 mol/L HCl: pH = -lg(0,01) = 2",
        "zusatz_label": "Voraussetzung",
        "zusatz_wert": "Gilt nur fuer starke Saeuren wie HCl, HNO3",
    },
    {
        "begriff": "pH-Berechnung schwache Saeure",
        "definition": "pH = 0,5 * (pKs - lg(c0)) fuer einprotonige schwache Saeuren",
        "beispiele": "0,1 mol/L Essigsaeure: pH = 0,5 * (4,76 - lg(0,1)) = 2,88",
        "zusatz_label": "Alternative",
        "zusatz_wert": "Auch ueber Ks und quadratische Gleichung loesbar",
    },
    # Puffer und Titration
    {
        "begriff": "Pufferloesung",
        "definition": "Loesung aus schwacher Saeure und ihrer konjugierten Base, die pH-Aenderungen abfaengt",
        "beispiele": "Acetatpuffer (CH3COOH/CH3COO-), Phosphatpuffer",
        "zusatz_label": "Wirkung",
        "zusatz_wert": "Faengt zugefuegte H+ oder OH- Ionen ab",
    },
    {
        "begriff": "Henderson-Hasselbalch-Gleichung",
        "definition": "pH = pKs + lg([A-]/[HA]) fuer Pufferloesungen",
        "beispiele": "Wenn [A-] = [HA]: pH = pKs",
        "zusatz_label": "Anwendung",
        "zusatz_wert": "Berechnung des pH-Werts von Pufferloesungen",
    },
    {
        "begriff": "Pufferkapazitaet",
        "definition": "Mass fuer die Menge an Saeure/Base, die ein Puffer abfangen kann",
        "beispiele": "Hohe Kapazitaet bei hoher Konzentration und [HA] ungefaehr [A-]",
        "zusatz_label": "Maximum",
        "zusatz_wert": "Beste Pufferwirkung bei pH = pKs (+/- 1)",
    },
    {
        "begriff": "Titration",
        "definition": "Quantitative Analysemethode durch kontrollierte Zugabe einer Massloesung",
        "beispiele": "Saeure-Base-Titration: NaOH-Loesung zu HCl-Loesung",
        "zusatz_label": "Ziel",
        "zusatz_wert": "Bestimmung der unbekannten Konzentration",
    },
    {
        "begriff": "Aequivalenzpunkt",
        "definition": "Punkt der Titration, an dem Stoffmengen von Saeure und Base gleich sind",
        "beispiele": "n(Saeure) = n(Base) bzw. c1*V1 = c2*V2",
        "zusatz_label": "pH-Wert",
        "zusatz_wert": "pH = 7 (starke S + starke B), pH != 7 bei schwachen Saeuren/Basen",
    },
    {
        "begriff": "Titrationskurve",
        "definition": "Graphische Darstellung des pH-Werts gegen das zugegebene Volumen der Massloesung",
        "beispiele": "S-foermiger Verlauf mit steilem Anstieg am Aequivalenzpunkt",
        "zusatz_label": "Auswertung",
        "zusatz_wert": "Ablesen von Aequivalenzpunkt, Halbaeqivalenzpunkt, pKs",
    },
    {
        "begriff": "Halbaeqivalenzpunkt",
        "definition": "Punkt, an dem die Haelfte der Saeure neutralisiert ist",
        "beispiele": "[HA] = [A-]",
        "zusatz_label": "Besonderheit",
        "zusatz_wert": "pH = pKs (direkte Bestimmung des pKs-Wertes)",
    },
    {
        "begriff": "Indikator",
        "definition": "Schwache Saeure oder Base, die je nach pH-Wert ihre Farbe aendert",
        "beispiele": "Phenolphthalein (farblos->pink), Methylorange (rot->gelb)",
        "zusatz_label": "Wahl",
        "zusatz_wert": "Umschlagsbereich muss im Bereich des Aequivalenzpunkts liegen",
    },
    # Gleichgewichte
    {
        "begriff": "Chemisches Gleichgewicht",
        "definition": "Zustand, in dem Hin- und Rueckreaktion gleich schnell ablaufen",
        "beispiele": "HA + H2O <-> A- + H3O+ (dynamisches Gleichgewicht)",
        "zusatz_label": "Merkmal",
        "zusatz_wert": "Konzentrationen bleiben konstant, aber Reaktionen laufen weiter",
    },
    {
        "begriff": "Prinzip von Le Chatelier",
        "definition": "Ein System im Gleichgewicht weicht einem aeusseren Zwang aus",
        "beispiele": "Zugabe von H+ verschiebt HA <-> A- + H+ nach links",
        "zusatz_label": "Anwendung",
        "zusatz_wert": "Vorhersage der Gleichgewichtsverschiebung bei Stoerungen",
    },
    {
        "begriff": "Massenwirkungsgesetz (MWG)",
        "definition": "Im Gleichgewicht ist der Quotient aus Produkten und Edukten konstant",
        "beispiele": "aA + bB <-> cC + dD; K = [C]^c[D]^d / [A]^a[B]^b",
        "zusatz_label": "Fuer Protolyse",
        "zusatz_wert": "Ks = [A-][H3O+]/[HA] (Wasser nicht im MWG)",
    },
    {
        "begriff": "Neutralisation",
        "definition": "Reaktion von Saeure und Base zu Wasser und Salz",
        "beispiele": "HCl + NaOH -> NaCl + H2O; H3O+ + OH- -> 2 H2O",
        "zusatz_label": "Energie",
        "zusatz_wert": "Exotherme Reaktion (Neutralisationswaerme)",
    },
    {
        "begriff": "Mehrprotonige Saeure",
        "definition": "Saeure, die mehr als ein Proton abgeben kann (stufenweise Dissoziation)",
        "beispiele": "H2SO4 (2 Protonen), H3PO4 (3 Protonen)",
        "zusatz_label": "Besonderheit",
        "zusatz_wert": "Jede Stufe hat eigenen pKs-Wert, pKs1 < pKs2 < pKs3",
    },
]


def main():
    # Get or create Schulfach "Chemie"
    chemie, _ = Schulfach.objects.get_or_create(
        name="Chemie",
        defaults={"beschreibung": "Naturwissenschaft der Stoffe und ihrer Umwandlungen"}
    )
    print(f"Schulfach: {chemie}")

    # Get or create Jahrgangsstufe 13
    stufe13, _ = Jahrgangsstufe.objects.get_or_create(
        stufe=13,
        defaults={"bezeichnung": "Q3/Q4"}
    )
    print(f"Jahrgangsstufe: {stufe13}")

    # =========================================================================
    # Block 1: Fette und Seifen
    # =========================================================================
    block1, created = Lernblock.objects.get_or_create(
        name="Chemie - Fette und Seifen",
        defaults={
            "beschreibung": "Aufbau, Reaktionen und Eigenschaften von Fetten, Seifen und Tensiden",
            "thema": "Chemie Q3",
            "schulfach": chemie,
            "jahrgangsstufe": stufe13,
            "bidirektional": True,
        }
    )

    if created:
        print(f"\nLernblock '{block1.name}' erstellt.")
    else:
        print(f"\nLernblock '{block1.name}' existiert bereits.")
        # Update metadata if block already exists
        block1.schulfach = chemie
        block1.jahrgangsstufe = stufe13
        block1.save()

    # Add cards
    created_count = 0
    for card_data in FETTE_UND_SEIFEN:
        karte, created = Karteikarte.objects.get_or_create(
            lernblock=block1,
            begriff=card_data["begriff"],
            defaults={
                "definition": card_data["definition"],
                "beispiele": card_data["beispiele"],
                "zusatz_label": card_data["zusatz_label"],
                "zusatz_wert": card_data["zusatz_wert"],
            }
        )
        if created:
            created_count += 1
            print(f"  + {card_data['begriff']}")
        else:
            print(f"  ~ {card_data['begriff']} (existiert bereits)")

    print(f"\n{created_count} neue Karten erstellt.")
    print(f"Gesamt: {block1.anzahl_karten} Karten im Lernblock '{block1.name}'.")

    # =========================================================================
    # Block 2: Protolysegleichgewichte
    # =========================================================================
    block2, created = Lernblock.objects.get_or_create(
        name="Chemie - Protolysegleichgewichte",
        defaults={
            "beschreibung": "Saeuren, Basen, pH-Wert, Puffer und Titration",
            "thema": "Chemie Q3",
            "schulfach": chemie,
            "jahrgangsstufe": stufe13,
            "bidirektional": True,
        }
    )

    if created:
        print(f"\nLernblock '{block2.name}' erstellt.")
    else:
        print(f"\nLernblock '{block2.name}' existiert bereits.")
        # Update metadata if block already exists
        block2.schulfach = chemie
        block2.jahrgangsstufe = stufe13
        block2.save()

    # Add cards
    created_count = 0
    for card_data in PROTOLYSEGLEICHGEWICHTE:
        karte, created = Karteikarte.objects.get_or_create(
            lernblock=block2,
            begriff=card_data["begriff"],
            defaults={
                "definition": card_data["definition"],
                "beispiele": card_data["beispiele"],
                "zusatz_label": card_data["zusatz_label"],
                "zusatz_wert": card_data["zusatz_wert"],
            }
        )
        if created:
            created_count += 1
            print(f"  + {card_data['begriff']}")
        else:
            print(f"  ~ {card_data['begriff']} (existiert bereits)")

    print(f"\n{created_count} neue Karten erstellt.")
    print(f"Gesamt: {block2.anzahl_karten} Karten im Lernblock '{block2.name}'.")

    # Summary
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Block 1: '{block1.name}' - {block1.anzahl_karten} Karten")
    print(f"Block 2: '{block2.name}' - {block2.anzahl_karten} Karten")


if __name__ == "__main__":
    main()
