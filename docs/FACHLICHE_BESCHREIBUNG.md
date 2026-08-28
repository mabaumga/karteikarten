# Karteikarten-App - Fachliche Beschreibung

## 1. Projektübersicht

### 1.1 Zielsetzung
Eine mobile-optimierte Webanwendung zum Lernen mit digitalen Karteikarten. Die App nutzt das bewährte **Leitner-System** für effizientes Lernen durch intelligente Wiederholungsintervalle.

### 1.2 Technische Rahmenbedingungen
- **Framework**: Django (Python)
- **Datenbank**: SQLite (leichtgewichtig, keine separate DB-Installation)
- **Deployment**: Standalone Docker-Container
- **Frontend**: Bootstrap 5 (Mobile-first, responsive)
- **Offline**: Progressive Web App (PWA)
- **Benutzer**: Einzelbenutzer-Anwendung (kein Login erforderlich)

---

## 2. Fachliche Konzepte

### 2.1 Lernblock
Ein **Lernblock** ist eine thematische Sammlung von Karteikarten.

| Attribut | Beschreibung | Beispiel |
|----------|--------------|----------|
| Name | Eindeutiger Name des Lernblocks | "Deutsch - Fremdwörter" |
| Beschreibung | Optionale Beschreibung | "Häufige Fremdwörter im Deutschen" |
| Bidirektional | Auch rückwärts lernen? | Ja/Nein |
| Erstellt am | Erstellungsdatum | 2025-01-15 |

**Beispiele für Lernblöcke:**
- Deutsch - Fremdwörter
- Deutsch - Stilmittel
- Englisch - Vokabeln Lektion 1
- Geschichte - Jahreszahlen
- Medizin - Fachbegriffe

### 2.2 Karteikarte
Eine **Karteikarte** besteht aus Vorderseite (Begriff) und Rückseite (Definition + optionale Zusatzinfos).

| Attribut | Pflicht | Beschreibung | Beispiel |
|----------|---------|--------------|----------|
| Begriff | Ja | Vorderseite der Karte | "Prokrastination" |
| Definition | Ja | Rückseite der Karte | "Das Aufschieben von Aufgaben" |
| Beispiele | Nein | Anwendungsbeispiele | "Er prokrastiniert seit Wochen." |
| Zusatz-Label | Nein | Frei definierbares Feld (Name) | "Herkunft" |
| Zusatz-Wert | Nein | Frei definierbares Feld (Inhalt) | "lat. procrastinare = vertagen" |
| Lernblock | Ja | Zugehöriger Lernblock | "Deutsch - Fremdwörter" |
| Fach | Ja | Aktuelles Leitner-Fach (1-5) | 1 |
| Nächste Wiederholung | Ja | Wann die Karte wieder dran ist | 2025-01-20 |
| Erstellt am | Ja | Erstellungsdatum | 2025-01-15 |

**Beispiel einer vollständigen Karteikarte:**
```
┌─────────────────────────────────────────────────────────────┐
│  VORDERSEITE                                                │
│                                                             │
│                    Prokrastination                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  RÜCKSEITE                                                  │
│                                                             │
│  Definition:   Das Aufschieben von Aufgaben                 │
│                                                             │
│  Beispiele:    "Er prokrastiniert seit Wochen."             │
│                "Prokrastination ist weit verbreitet."       │
│                                                             │
│  Herkunft:     lat. procrastinare = vertagen                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Hinweis zum Zusatz-Feld:**
Das Zusatz-Feld ist frei definierbar und kann je nach Lerninhalt unterschiedlich genutzt werden:
- Bei Fremdwörtern: "Herkunft" (Etymologie)
- Bei Vokabeln: "Aussprache" (IPA)
- Bei Stilmitteln: "Wirkung" (rhetorische Wirkung)
- Bei Geschichte: "Epoche" (zeitliche Einordnung)

### 2.3 Leitner-System
Das **Leitner-System** ist ein Karteikarten-Lernsystem mit 5 Fächern:

```
┌─────────────────────────────────────────────────────────────────┐
│                      LEITNER-SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Fach 1        Fach 2        Fach 3        Fach 4        Fach 5 │
│   ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐│
│   │█████│       │███  │       │██   │       │█    │       │     ││
│   │█████│       │███  │       │██   │       │█    │       │     ││
│   │█████│       │███  │       │     │       │     │       │     ││
│   └─────┘       └─────┘       └─────┘       └─────┘       └─────┘│
│   Täglich       Alle 2        Alle 4        Alle 7        Alle   │
│                 Tage          Tage          Tage          14 Tage│
│                                                                  │
│   ──────────────────────────────────────────────────────────────│
│   RICHTIG: Karte wandert ein Fach nach rechts →                  │
│   FALSCH:  Karte wandert zurück zu Fach 1 ←                      │
└─────────────────────────────────────────────────────────────────┘
```

**Wiederholungsintervalle:**
| Fach | Intervall | Bedeutung |
|------|-----------|-----------|
| 1 | Täglich | Neue oder schwierige Karten |
| 2 | Alle 2 Tage | Erste Festigung |
| 3 | Alle 4 Tage | Mittelfristig gelernt |
| 4 | Alle 7 Tage | Gut gelernt |
| 5 | Alle 14 Tage | Langzeitgedächtnis |

**Regeln:**
- Neue Karten starten in **Fach 1**
- **Richtig beantwortet**: Karte wandert ein Fach nach rechts (max. Fach 5)
- **Falsch beantwortet**: Karte wandert zurück zu **Fach 1**
- Karten in Fach 5 bleiben dort, werden aber weiter abgefragt

### 2.4 Lernstatistik
Pro Lernblock werden folgende Statistiken geführt:

| Statistik | Beschreibung |
|-----------|--------------|
| Gesamtzahl Karten | Anzahl Karten im Lernblock |
| Karten pro Fach | Verteilung auf Fächer 1-5 |
| Heute gelernt | Anzahl heute beantworteter Karten |
| Richtig/Falsch heute | Erfolgsquote des Tages |
| Richtig/Falsch gesamt | Gesamte Erfolgsquote |
| Lernstreak | Anzahl aufeinanderfolgender Lerntage (1 richtige Antwort = 1 Tag) |
| Fällige Karten | Karten, die heute wiederholt werden sollen |

**Streak-Regel:** Ein Tag zählt als "gelernt", sobald mindestens **eine Karte richtig** beantwortet wurde. Der Streak erhöht sich täglich bei Aktivität und wird auf 0 zurückgesetzt, wenn ein Tag ohne richtige Antwort vergeht.

---

## 3. Lernmodi

### 3.1 Klassischer Modus (Vorwärts)
Der traditionelle Karteikarten-Modus:

```
┌────────────────────────────────────┐
│         KARTEIKARTE                │
│                                    │
│                                    │
│         Prokrastination            │
│                                    │
│                                    │
│         [ Auflösen ]               │
│                                    │
└────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────┐
│         KARTEIKARTE                │
│                                    │
│         Prokrastination            │
│         ──────────────             │
│    Das Aufschieben von Aufgaben    │
│                                    │
│    Beispiel:                       │
│    "Er prokrastiniert seit Wochen" │
│                                    │
│    Herkunft:                       │
│    lat. procrastinare = vertagen   │
│                                    │
│    [ Falsch ]      [ Richtig ]     │
│                                    │
└────────────────────────────────────┘
```

**Hinweis:** Beispiele und Zusatzfeld werden nur angezeigt, wenn sie gepflegt sind.

**Ablauf:**
1. Begriff wird angezeigt
2. Nutzer überlegt die Antwort
3. Klick auf "Auflösen" zeigt die Definition
4. Nutzer bewertet sich selbst: "Richtig" oder "Falsch"
5. Leitner-System wird aktualisiert
6. Nächste Karte wird angezeigt

### 3.2 Rückwärts-Modus
Umgekehrte Abfragerichtung (Definition → Begriff):

```
┌────────────────────────────────────┐
│         KARTEIKARTE                │
│                                    │
│                                    │
│    Das Aufschieben von Aufgaben    │
│                                    │
│                                    │
│         [ Auflösen ]               │
│                                    │
└────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────┐
│         KARTEIKARTE                │
│                                    │
│    Das Aufschieben von Aufgaben    │
│         ──────────────             │
│         Prokrastination            │
│                                    │
│    [ Falsch ]      [ Richtig ]     │
│                                    │
└────────────────────────────────────┘
```

**Hinweis:** Dieser Modus ist nur verfügbar, wenn der Lernblock als "bidirektional" markiert ist.

### 3.3 Multiple-Choice-Modus
Vier Antwortmöglichkeiten, eine ist richtig:

```
┌────────────────────────────────────┐
│         KARTEIKARTE                │
│                                    │
│         Prokrastination            │
│                                    │
│  ┌──────────────────────────────┐  │
│  │ A) Das Aufschieben von       │  │
│  │    Aufgaben                  │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ B) Übertriebene Sparsamkeit  │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ C) Selbstüberschätzung       │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ D) Vermenschlichung          │  │
│  └──────────────────────────────┘  │
│                                    │
└────────────────────────────────────┘
```

**Funktionsweise:**
- Die richtige Antwort ist die Definition der aktuellen Karte
- Die 3 falschen Antworten (Distraktoren) werden **automatisch** aus anderen Karten desselben Lernblocks gezogen
- Die Reihenfolge der Antworten ist zufällig
- **Voraussetzung**: Lernblock muss mindestens 4 Karten enthalten

**Nach der Auswahl:**
- Richtige Antwort: Grün markiert, Karte wandert ein Fach nach rechts
- Falsche Antwort: Gewählte Antwort rot, richtige Antwort grün, Karte zu Fach 1

### 3.4 Tippmodus (Eintippen)
Die Antwort wird eingetippt statt nur aufgedeckt. Wer selbst formulieren muss,
behält mehr — Wiedererkennen ist leichter als Erinnern.

```
┌────────────────────────────────────┐
│         KARTEIKARTE                │
│                                    │
│         le chien                   │
│                                    │
│  Definition eintippen              │
│  ┌──────────────────────────────┐  │
│  │ der Hund                     │  │
│  └──────────────────────────────┘  │
│                                    │
│         [ Prüfen ]                 │
│                                    │
└────────────────────────────────────┘
```

**Ablauf:**
1. Vorderseite wird angezeigt
2. Nutzer tippt die Rückseite ein, Enter oder "Prüfen"
3. Die App bewertet — keine Selbsteinschätzung
4. Lösung wird eingeblendet, Enter geht zur nächsten Karte

**Bewertung** (serverseitig, `karteikarten/services/antwortpruefung.py`):

| Ergebnis | Bedeutung | Zählt als |
|---|---|---|
| `richtig` | Antwort stimmt | richtig |
| `fast` | Vokabel gewusst, ein Detail daneben | richtig, mit Hinweis auf die Schreibweise |
| `falsch` | andere Vokabel oder leer | falsch |

Nicht gewertet werden Groß-/Kleinschreibung, Leerzeichen, Satzzeichen am Rand und
Klammerzusätze. Enthält die Lösung Alternativen (`gehen / laufen`, `der Hund, das
Tier`, `eventuell oder vielleicht`), genügt eine davon. Als `fast` gelten fehlende
Akzente (`eleve` statt `élève`) und ein fehlender Artikel (`Hund` statt `der Hund`,
`go` statt `to go`) — auf einer deutschen Handytastatur wäre Strenge hier
frustrierend statt lehrreich.

**Richtung:** Bei bidirektionalen Lernblöcken lässt sich im Modus zwischen
Vorder- und Rückseite umschalten.

---

## 4. Benutzeroberfläche

### 4.0 Aufbau und Navigation

Die App hat **vier Bereiche**, erreichbar über eine beschriftete Navigation. Alles
andere sind Unterseiten davon.

| Reiter | Was dort liegt |
|---|---|
| **Start** | Was heute ansteht — je Lernblock eine Zeile, plus „Alles zusammen üben" |
| **Blöcke** | Welche Lernblöcke auf der Startseite erscheinen, und der Weg in mehrere zugleich |
| **Fortschritt** | Erstversuchsquote, Kartenzustand, Problemkarten, Verlauf |
| **Mehr** | Profil, offline lernen, Passwort — und für Verwalter die Verwaltung |

**Zwei Rollen, ein Aufbau.** Lernende sehen nur den Lernweg. Alles Verwaltende
(Blöcke anlegen, Karten bearbeiten, CSV-Import, Benutzer, Backup) ist mit
`is_staff` bedingt und steht in eigenen, beschrifteten Abschnitten — nie zwischen
den Lernaktionen.

**Abfrageansichten laufen ohne Navigation** (`lernansicht.html`): während einer
Abfrage gibt es eine Aufgabe und einen Ausgang, keine vier Reiter. Die Kopfzeile
trägt dort Modusnamen, Fortschrittsleiste und Abbrechen.

#### Mobile first — dieselbe Struktur auf drei Breiten

| | Handy `< 768` | iPad `≥ 768` | Desktop `≥ 992` |
|---|---|---|---|
| Navigation | unten, vier Reiter | unten, unverändert | links als Schiene |
| Inhaltsbreite | voll, 16 px Rand | max. 720 px | max. 900 px |
| Blocklisten | eine Spalte | zwei Spalten | zwei Spalten |
| Hauptaktion | fest am unteren Rand | fest am unteren Rand | oben neben der Überschrift |
| Abfragekarte | volle Breite | max. 560 px | max. 560 px |

Tippziele bleiben auf allen Breiten mindestens 44 px hoch.

Die Umschaltung läuft über Bootstrap-Klassen (`d-lg-none` für die untere Leiste,
`d-none d-lg-flex` für die Seitenschiene, `col-12 col-md-6` für Listen) — beide
Navigationen stehen im selben Markup, es gibt kein zweites Layout und kein
JavaScript dafür.

**Mehr Platz zeigt mehr auf einmal, nicht dasselbe breiter.** Die Abfragekarte
bleibt bei 560 px gedeckelt: eine über 1000 px breite Vokabelkarte liest sich
schlechter, nicht besser.

### 4.1 Startseite / Dashboard

Jede Zeile sagt **zuerst, was zu tun ist**, dann erst, worum es geht. Rechts ein
Ring mit der Anzahl fälliger Karten.

```
┌─────────────────────────────────────────────────────────────┐
│                        Lina                            📊   │
├─────────────────────────────────────────────────────────────┤
│  [ Alle ] [ Englisch ] [ Französisch ]                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ EN   Heute üben                              ( 15 ) │   │
│  │      Access 3 · Unit 4 – At the market              │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ FR   Heute üben                              (  8 ) │   │
│  │      Découvertes 2 · Unité 2 – La famille           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ DE   Heute geschafft                         ( ✓  ) │   │
│  │      Stilmittel · 32 Karten                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ▶  Alles zusammen üben (23)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│      Modus: Klassisch · 156 Karten insgesamt                │
├─────────────────────────────────────────────────────────────┤
│    Start    │   Blöcke   │  Fortschritt  │      Mehr        │
└─────────────────────────────────────────────────────────────┘
```

Drei Zustände je Zeile, weil sie sich für den Lernenden wirklich unterscheiden:
**Heute üben** (Ring mit Anzahl), **Heute geschafft** (Haken), **In N Tagen
fällig** (gestrichelter Ring mit Uhr).

„Alles zusammen üben" startet **direkt** — welche Blöcke (die eigenen) und welcher
Modus (die Einstellung) stehen bereits fest.


### 4.2 Lernblock-Detailansicht

```
┌─────────────────────────────────────────────────────────────┐
│  ‹            Unit 4 – At the market                        │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                 │
│  │    EN     │ │  ( 15 )   │ │    📊     │                 │
│  │ Access 3  │ │Heute fällig│ │Fortschritt│                 │
│  └───────────┘ └───────────┘ └───────────┘                 │
│                                                             │
│  Zuletzt gelernt: 28. August · 45 Karten insgesamt          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📖  Modus                          Klassisch     ›  │   │
│  │ ▽   Karten                          Alle 45      ›  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ▶  Üben starten (15)                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Ein Weg ins Lernen.** Modus und Kartenumfang sind Einstellungen mit sichtbarem
Wert, keine konkurrierenden Einstiege. Der Knopf tut, was er sagt: er startet die
Abfrage — früher führte „Lernen" zu einer weiteren Auswahl.

Der Modus gilt **für alle Blöcke** und hält über die Sitzung hinaus
(`BenutzerStatistik.bevorzugter_modus`). Passt er zu einem Block nicht — Rückwärts
ohne bidirektionalen Block, Multiple Choice unter vier Karten — fällt die Abfrage
still auf „Klassisch" zurück, statt eine Fehlermeldung zu zeigen.


### 4.3 Karten-Verwaltung
```
┌─────────────────────────────────────────────────────────────┐
│  ← Zurück              Karten verwalten                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔍 [ Suchen... ]                     [ ➕ Neue Karte ]     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Prokrastination                              Fach 2 │   │
│  │ Das Aufschieben von Aufgaben                        │   │
│  │                                          [ ✏️ ] [ 🗑️ ] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Eloquent                                     Fach 1 │   │
│  │ Redegewandt, sprachgewandt                          │   │
│  │                                          [ ✏️ ] [ 🗑️ ] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Ambivalent                                   Fach 3 │   │
│  │ Zwiespältig, in sich widersprüchlich                │   │
│  │                                          [ ✏️ ] [ 🗑️ ] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                    [ Seite 1 von 5 ]                        │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 CSV-Import
```
┌─────────────────────────────────────────────────────────────┐
│  ← Zurück               CSV Import                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📄 CSV-Datei hochladen                                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │      [ 📁 Datei auswählen ]                        │   │
│  │                                                     │   │
│  │      oder Datei hierher ziehen                     │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📋 Erwartetes Format:                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Begriff;Definition                                  │   │
│  │ Prokrastination;Das Aufschieben von Aufgaben       │   │
│  │ Eloquent;Redegewandt, sprachgewandt                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ⚙️ Optionen:                                               │
│  [x] Erste Zeile ist Kopfzeile                             │
│  [ ] Trennzeichen: [;] (Semikolon)                         │
│                                                             │
│                              [ Importieren ]                │
└─────────────────────────────────────────────────────────────┘
```

---

### 4.5 Fortschritt

Zwei Ebenen: der Reiter **Fortschritt** über alle Blöcke, und je Block eine eigene
Ansicht (`/lernblock/<id>/fortschritt/`).

**Beim ersten Versuch richtig** ist die Leitzahl. Die laufende Erfolgsquote steigt
zwangsläufig, weil jede Karte so lange wiederkommt, bis sie sitzt — der erste
Versuch dagegen sagt, was wirklich gelernt wurde. Gezählt wird die früheste
Antwort je Karte; spätere Wiederholungen ändern sie nicht.

| Kennzahl | Woraus | Bedeutung |
|---|---|---|
| Erstversuchsquote | erstes `Lernergebnis` je Karte | Anteil der Karten, die gleich saßen |
| Sitzt sicher | `BenutzerKarteStatus.fach == 5` | durch alle Stufen gelaufen |
| In Arbeit | beantwortet, Stufe 1–4 | angefangen, noch nicht sicher |
| Noch nie geübt | keine Antwort vorhanden | *nicht* am Status abgelesen — ein Status entsteht schon beim Anzeigen |
| Problemkarten | Anzahl `richtig=False` je Karte | die fünf mit den meisten Fehlern, mit Weg ins gezielte Üben |
| Letzte 7 Tage | `TagesStatistik` | Antworten pro Tag, davon richtig; Lücken als Nulltage |

**Gezählt wird nur, was ausgewählt ist.** Grundlage ist immer `BenutzerLernblock`,
nie der Datenbestand: Wer im Februar Unit 1 wählt und im April Unit 2 dazunimmt,
sieht im Februar keine Zahlen zu Unit 2. Ein Ort beantwortet diese Frage
(`_gewaehlte_bloecke`), Startseite und Fortschritt teilen ihn sich.

**Gegliedert nach Schulfach und Lehrbuch.** Die Gesamtquote allein verwischt, was
den Lernenden interessiert: 75 % können 100 % in Französisch und 50 % in Englisch
heißen. Die Ansicht zeigt deshalb drei Ebenen — Gesamt, je Schulfach, je Lehrwerk
— und darin die einzelnen Blöcke. Lehrwerke mit mehreren Blöcken sind eingeklappt
(`<details>`, kein JavaScript).

**Während der Abfrage** steht unter jeder Karte leise, wie weit ihr Block ist
(`kurzfortschritt`: wie viele Karten Stufe 5 erreicht haben). Im kombinierten
Modus gehört die Anzeige zum Block der gerade gezeigten Karte.

Implementierung: `karteikarten/services/statistik.py`. Die Erstversuchs-Auswahl
läuft bewusst in Python — SQLite kennt kein `DISTINCT ON`, und bei diesen
Datenmengen ist die offensichtlich richtige Lösung die bessere.

---

## 5. Progressive Web App (PWA)

### 5.1 PWA-Features
Die App wird als Progressive Web App implementiert:

| Feature | Beschreibung |
|---------|--------------|
| **Installierbar** | "Zum Startbildschirm hinzufügen" auf Smartphone |
| **Offline-fähig** | Lernen ohne Internetverbindung möglich |
| **App-ähnlich** | Vollbild, kein Browser-Rahmen |
| **Schnell** | Service Worker cached statische Ressourcen |

### 5.2 Offline-Strategie
```
┌─────────────────────────────────────────────────────────────┐
│                    OFFLINE-STRATEGIE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ONLINE                           OFFLINE                   │
│  ┌─────────┐                     ┌─────────┐               │
│  │ Server  │◄────Sync────────────│ IndexDB │               │
│  │ SQLite  │                     │ (lokal) │               │
│  └─────────┘                     └─────────┘               │
│       │                               │                     │
│       │                               │                     │
│       ▼                               ▼                     │
│  Lernblöcke werden             Lernergebnisse werden       │
│  heruntergeladen               lokal gespeichert           │
│                                                             │
│  Bei Reconnect: Automatische Synchronisation               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Datenmodell

### 6.1 Entity-Relationship-Diagramm
```
┌─────────────────┐         ┌─────────────────┐
│   Lernblock     │         │   Karteikarte   │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │────────<│ id (PK)         │
│ name            │         │ lernblock_id(FK)│
│ beschreibung    │         │ begriff         │
│ bidirektional   │         │ definition      │
│ erstellt_am     │         │ beispiele       │
│ aktualisiert_am │         │ zusatz_label    │
└─────────────────┘         │ zusatz_wert     │
                            │ fach (1-5)      │
                            │ naechste_wdh    │
                            │ erstellt_am     │
                            │ aktualisiert_am │
                            └─────────────────┘
                                    │
                                    │
                            ┌───────┴───────┐
                            │               │
                    ┌───────▼─────┐ ┌───────▼─────┐
                    │ Lernergebnis│ │  Statistik  │
                    ├─────────────┤ ├─────────────┤
                    │ id (PK)     │ │ id (PK)     │
                    │ karte_id(FK)│ │ block_id(FK)│
                    │ modus       │ │ datum       │
                    │ richtung    │ │ gelernt     │
                    │ richtig     │ │ richtig     │
                    │ zeitstempel │ │ falsch      │
                    └─────────────┘ │ streak      │
                                    └─────────────┘
```

### 6.2 Tabellenstruktur

**Lernblock**
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | Integer, PK | Primärschlüssel |
| name | String(100) | Eindeutiger Name |
| beschreibung | Text, optional | Beschreibung |
| bidirektional | Boolean | Rückwärts-Modus erlaubt? |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

**Karteikarte**
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | Integer, PK | Primärschlüssel |
| lernblock_id | FK → Lernblock | Zugehöriger Block |
| begriff | String(200) | Vorderseite |
| definition | Text | Rückseite |
| beispiele | Text, optional | Anwendungsbeispiele |
| zusatz_label | String(50), optional | Name des Zusatzfeldes |
| zusatz_wert | Text, optional | Inhalt des Zusatzfeldes |
| fach | Integer (1-5) | Aktuelles Leitner-Fach |
| naechste_wiederholung | Date | Nächste Fälligkeit |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

**Lernergebnis** (für detaillierte Auswertungen)
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | Integer, PK | Primärschlüssel |
| karte_id | FK → Karteikarte | Gelernte Karte |
| modus | String | 'klassisch', 'rueckwaerts', 'multiple_choice', 'tippen' |
| richtung | String | 'vorwaerts', 'rueckwaerts' |
| richtig | Boolean | Richtig beantwortet? |
| zeitstempel | DateTime | Wann gelernt |

**TagesStatistik** (für Dashboard)
| Feld | Typ | Beschreibung |
|------|-----|--------------|
| id | Integer, PK | Primärschlüssel |
| lernblock_id | FK → Lernblock | Zugehöriger Block |
| datum | Date | Tag |
| gelernt | Integer | Anzahl gelernte Karten |
| richtig | Integer | Davon richtig |
| falsch | Integer | Davon falsch |

---

## 7. API-Endpunkte

### 7.1 Übersicht
| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/` | Dashboard/Startseite |
| GET | `/lernblock/` | Liste aller Lernblöcke |
| POST | `/lernblock/neu/` | Neuen Lernblock erstellen |
| GET | `/lernblock/<id>/` | Lernblock-Detail |
| POST | `/lernblock/<id>/bearbeiten/` | Lernblock bearbeiten |
| POST | `/lernblock/<id>/loeschen/` | Lernblock löschen |
| GET | `/lernblock/<id>/karten/` | Karten des Lernblocks |
| POST | `/lernblock/<id>/karten/neu/` | Neue Karte erstellen |
| POST | `/lernblock/<id>/karten/import/` | CSV-Import |
| GET | `/fortschritt/` | Fortschritt über alle Blöcke |
| GET | `/mehr/` | Profil, Offline, Verwaltung |
| GET | `/lernblock/<id>/fortschritt/` | Fortschritt eines Blocks |
| GET/POST | `/lernblock/<id>/modus/` | Lernmodus wählen (gilt für alle Blöcke) |
| GET | `/lernblock/<id>/lernen/` | Startet die Abfrage im gewählten Modus |
| GET | `/lernen/alles/` | Alle eigenen Blöcke zusammen, im gewählten Modus |
| GET | `/lernblock/<id>/lernen/klassisch/` | Klassischer Modus |
| GET | `/lernblock/<id>/lernen/rueckwaerts/` | Rückwärts-Modus |
| GET | `/lernblock/<id>/lernen/multiple-choice/` | Multiple-Choice |
| GET | `/lernblock/<id>/lernen/tippen/` | Tippmodus (`?richtung=rueckwaerts`) |
| POST | `/api/karte/<id>/antwort/` | Selbstbewertung speichern |
| POST | `/api/karte/<id>/tippen/` | Eingetippte Antwort prüfen und speichern |
| GET | `/karte/<id>/` | Karte anzeigen |
| POST | `/karte/<id>/bearbeiten/` | Karte bearbeiten |
| POST | `/karte/<id>/loeschen/` | Karte löschen |
| GET | `/statistik/` | Gesamtstatistik |

---

## 8. Nicht-funktionale Anforderungen

### 8.1 Performance
- Seitenaufbau < 1 Sekunde
- Kartenanzeige < 100ms (nach initialem Laden)
- Offline-Lernen ohne merkbare Verzögerung

### 8.2 Usability
- Touch-optimiert für Smartphone
- Große Buttons (min. 44x44 Pixel)
- Wischgesten für Navigation (optional)
- Hochformat-optimiert

### 8.3 Barrierefreiheit
- Ausreichender Farbkontrast
- Skalierbare Schriftgrößen
- Tastatur-Navigation möglich

---

## 9. Abgrenzung (Out of Scope für MVP)

Folgende Features sind **nicht** Teil des MVP:
- [ ] Mehrbenutzer / Login
- [ ] Bilder auf Karteikarten
- [ ] Audio/Aussprache
- [ ] Geteilte Lernblöcke
- [ ] Gamification (Punkte, Badges)
- [ ] Spaced Repetition mit SM-2 Algorithmus
- [ ] Export-Funktion
- [ ] Lernblock-Vorlagen
- [ ] Dark Mode

---

## 10. Glossar

| Begriff | Definition |
|---------|------------|
| **Lernblock** | Thematische Sammlung von Karteikarten |
| **Karteikarte** | Einzelne Lerneinheit mit Begriff und Definition |
| **Leitner-System** | Lernmethode mit 5 Fächern und steigenden Intervallen |
| **Fach** | Position im Leitner-System (1-5) |
| **Fällige Karte** | Karte, deren Wiederholungsdatum erreicht ist |
| **Distraktor** | Falsche Antwortmöglichkeit bei Multiple Choice |
| **Stufe 1–5** | Leitner-Fach in der Oberfläche. Heißt bewusst nicht mehr „Fach" — das meint dort das Schulfach |
| **Schulfach** | Englisch, Französisch, Deutsch … — der Filter auf der Startseite |
| **Erstversuchsquote** | Anteil der Karten, die beim allerersten Mal richtig beantwortet wurden |
| **PWA** | Progressive Web App - installierbare Webanwendung |
| **Streak** | Anzahl aufeinanderfolgender Lerntage |
| **Bidirektional** | Lernen in beide Richtungen (Begriff↔Definition) |

---

## 11. Anhang

### 11.1 CSV-Import-Format

**Minimales Format (nur Pflichtfelder):**
```csv
Begriff;Definition
Prokrastination;Das Aufschieben von Aufgaben
Eloquent;Redegewandt, sprachgewandt
Ambivalent;Zwiespältig, in sich widersprüchlich
```

**Vollständiges Format (mit optionalen Feldern):**
```csv
Begriff;Definition;Beispiele;Zusatz-Label;Zusatz-Wert
Prokrastination;Das Aufschieben von Aufgaben;"Er prokrastiniert seit Wochen.";Herkunft;lat. procrastinare = vertagen
Eloquent;Redegewandt, sprachgewandt;"Eine eloquente Rede";Synonym;wortgewandt
Ambivalent;Zwiespältig, in sich widersprüchlich;;"Gegenteil";eindeutig
```

**Hinweise zum CSV-Format:**
- Trennzeichen: Semikolon (;)
- Optionale Felder können leer gelassen werden
- Bei mehreren Beispielen: Zeilenumbruch innerhalb der Zelle (in Anführungszeichen)
- Anführungszeichen um Felder, die Semikolons oder Zeilenumbrüche enthalten

### 11.2 Farbschema (Vorschlag)
| Element | Farbe | Hex |
|---------|-------|-----|
| Primär | Blau | #3B82F6 |
| Erfolg/Richtig | Grün | #10B981 |
| Fehler/Falsch | Rot | #EF4444 |
| Warnung | Orange | #F59E0B |
| Hintergrund | Hellgrau | #F3F4F6 |
| Karte | Weiß | #FFFFFF |
| Text | Dunkelgrau | #1F2937 |
