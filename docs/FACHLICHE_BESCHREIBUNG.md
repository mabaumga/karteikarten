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

---

## 4. Benutzeroberfläche

### 4.1 Startseite / Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│  🎴 Karteikarten                                    [PWA ⚡] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Dein Fortschritt                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔥 12 Tage Streak    📚 156 Karten    ✅ 78% Quote │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📋 Heute fällig: 23 Karten                                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📁 Deutsch - Fremdwörter                            │   │
│  │    15 fällig │ 45 Karten │ Fach ▁▂▃▄▅              │   │
│  │    [ Lernen ]                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📁 Deutsch - Stilmittel                             │   │
│  │    8 fällig │ 32 Karten │ Fach ▁▂▃▄▅               │   │
│  │    [ Lernen ]                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ➕ Neuen Lernblock erstellen                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Lernblock-Detailansicht
```
┌─────────────────────────────────────────────────────────────┐
│  ← Zurück          Deutsch - Fremdwörter          ⚙️ ✏️ 🗑️ │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Statistik                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Fach 1: ████████████████ 25                        │   │
│  │  Fach 2: ████████ 12                                │   │
│  │  Fach 3: ████ 5                                     │   │
│  │  Fach 4: ██ 2                                       │   │
│  │  Fach 5: █ 1                                        │   │
│  │                                                     │   │
│  │  Erfolgsquote: 72%    Heute: 8/10 richtig          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🎯 Lernmodus wählen                                        │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐     │
│  │   📖          │ │   🔄          │ │   📝          │     │
│  │  Klassisch    │ │  Rückwärts    │ │   Multiple    │     │
│  │               │ │               │ │   Choice      │     │
│  │  15 fällig    │ │  15 fällig    │ │  15 fällig    │     │
│  └───────────────┘ └───────────────┘ └───────────────┘     │
│                                                             │
│  📚 Karten verwalten                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [ ➕ Neue Karte ] [ 📤 CSV Import ] [ 📋 Alle ]    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

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
| modus | String | 'klassisch', 'rueckwaerts', 'multiple_choice' |
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
| GET | `/lernblock/<id>/lernen/` | Lernmodus-Auswahl |
| GET | `/lernblock/<id>/lernen/klassisch/` | Klassischer Modus |
| GET | `/lernblock/<id>/lernen/rueckwaerts/` | Rückwärts-Modus |
| GET | `/lernblock/<id>/lernen/multiplechoice/` | Multiple-Choice |
| POST | `/api/karte/<id>/antwort/` | Antwort speichern |
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
