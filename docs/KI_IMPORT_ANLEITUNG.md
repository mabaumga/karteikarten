# Lerninhalte mit KI aus Dokumenten generieren

## Ueberblick

Mit einer KI (z.B. Claude) lassen sich aus PDFs, Fotos oder anderen Dokumenten automatisch Import-Dateien fuer die Karteikarten-App erzeugen. Die KI liest das Dokument, extrahiert die Lerninhalte und gibt eine JSON-Datei im korrekten Format aus.

---

## Voraussetzungen

- Zugang zu einer KI mit Dokumenten-Verarbeitung (Claude, ChatGPT, etc.)
- Das Quelldokument als PDF, Foto oder Text
- Das JSON-Schema: `docs/input/json/schema/lerninhalt_schema.json`

---

## Schritt-fuer-Schritt-Anleitung

### 1. Dokument vorbereiten

- **PDF**: Direkt hochladen (Claude kann PDFs lesen)
- **Foto/Scan**: Als Bild hochladen (Lehrbuchseiten, Arbeitsblatt)
- **Text**: Kopieren und in den Chat einfuegen
- **Webseite**: URL angeben oder Inhalt kopieren

### 2. Prompt an die KI

Den folgenden Prompt verwenden und anpassen:

---

**Prompt-Vorlage:**

```
Ich habe eine Karteikarten-App mit JSON-Import. Erstelle aus dem angehaengten
Dokument eine Import-Datei im folgenden Format.

**JSON-Schema:**

{
  "meta": {
    "fach": "<Schulfach>",
    "lehrwerk": "<Name des Buches/der Quelle>",
    "band": <Bandnummer oder weglassen>,
    "klasse": <Jahrgangsstufe oder weglassen>,
    "sprachen": ["<Fremdsprache>", "Deutsch"],
    "version": "1.0"
  },
  "inhalt": [
    {
      "name": "<Unit/Kapitel-Name>",
      "bloecke": [
        {
          "name": "<Lernblock-Name>",
          "bidirektional": true,
          "karten": [
            {
              "vorne": "<Begriff/Fremdsprache>",
              "hinten": "<Definition/Uebersetzung>",
              "beispiel": "<Beispielsatz (optional)>",
              "tags": ["<Tag1>", "<Tag2>"]
            }
          ]
        }
      ]
    }
  ]
}

**Regeln:**
- "vorne" und "hinten" sind Pflichtfelder
- Beispielsaetze wenn moeglich als Objekt: {"fr": "...", "de": "..."}
- Tags fuer Wortarten, Themen oder Schwierigkeitsgrad
- Bloecke mit max. 30-50 Karten (bei mehr aufteilen)
- Seitenzahlen im "seite"-Feld wenn vorhanden
- Zusatzinfos (Wortart, Konjugation, Herkunft) ins "zusatz"-Objekt

Gib NUR die JSON-Datei aus, ohne Erklaerungen.
```

---

### 3. Beispiele fuer verschiedene Faecher

#### Vokabeln (Franzoesisch, Englisch, etc.)

```
Erstelle Karteikarten aus den Vokabeln auf den angehaengten Seiten.
Fach: Franzoesisch, Lehrwerk: "A plus! Nouvelle edition", Band 2, Klasse 7.
Jede Vokabel bekommt einen Beispielsatz auf Franzoesisch und Deutsch.
Tags: Wortart (Verb, Nomen, Adjektiv, etc.)
```

#### Fachbegriffe (Chemie, Biologie, etc.)

```
Erstelle Karteikarten aus den Fachbegriffen im angehaengten Dokument.
Fach: Chemie, Thema: "Saeure-Base-Reaktionen".
Vorne: Fachbegriff, Hinten: Definition.
Zusatz: Formel (falls vorhanden).
Tags: Themengebiet.
```

#### Geschichte (Jahreszahlen, Ereignisse)

```
Erstelle Karteikarten aus dem Geschichtstext.
Vorne: Jahreszahl oder Ereignis, Hinten: Beschreibung.
Tags: Epoche, Region.
Bloecke nach Zeitabschnitten gruppieren.
```

#### Formeln (Mathematik, Physik)

```
Erstelle Karteikarten aus den Formeln.
Vorne: Formelname, Hinten: Formel + kurze Erklaerung.
Zusatz: Einheiten, Anwendungsbeispiel.
Tags: Themengebiet.
```

### 4. Ergebnis pruefen und importieren

1. **JSON validieren**: Die KI-Ausgabe in einen JSON-Validator kopieren (z.B. jsonlint.com)
2. **Stichproben pruefen**: Stimmen die Uebersetzungen/Definitionen?
3. **Als Datei speichern**: z.B. `franzoesisch_band2_unite1.json`
4. **Importieren**:
   ```bash
   python manage.py import_json franzoesisch_band2_unite1.json
   ```

---

## Tipps fuer bessere Ergebnisse

### Dokument-Qualitaet
- **Klare Scans**: Hohe Aufloesung, gerade ausgerichtet
- **Wenige Seiten**: Lieber 2-3 Seiten auf einmal als ein ganzes Buch
- **Kontext geben**: Fach, Klasse, Lehrwerk — die KI liefert bessere Ergebnisse

### Prompt-Optimierung
- **Beispiel mitgeben**: Ein fertiges JSON-Beispiel als Referenz anhaengen
- **Sprache explizit**: Bei Vokabeln immer Quell- und Zielsprache angeben
- **Bloeckgroesse**: "Maximal 30 Karten pro Block" verhindert zu grosse Bloecke
- **Rueckfragen erlauben**: "Frage nach, wenn etwas unklar ist"

### Nachbearbeitung
- Fehlerhafte Karten im App-UI korrigieren (einfacher als JSON editieren)
- Fehlende Beispielsaetze manuell ergaenzen
- Tags vereinheitlichen (z.B. immer "Verb" statt "verb" oder "Verben")

---

## Beispiel: Kompletter Workflow

```
1. Lehrbuchseite fotografieren (Vokabelliste Franzoesisch)
2. Foto in Claude hochladen
3. Prompt: "Erstelle Karteikarten-JSON aus diesen Vokabeln.
   Fach: Franzoesisch, Lehrwerk: A plus Band 2, Klasse 7.
   Format: siehe Schema. Beispielsaetze auf FR und DE."
4. JSON-Ausgabe kopieren → franzoesisch_unite3.json speichern
5. python manage.py import_json franzoesisch_unite3.json
6. In der App pruefen und ggf. korrigieren
```

---

## Referenz

- **JSON-Schema**: `docs/input/json/schema/lerninhalt_schema.json`
- **Beispiel Franzoesisch**: `docs/input/json/schema/beispiel_franzoesisch.json`
- **Beispiel Chemie**: `docs/input/json/schema/beispiel_chemie.json`
