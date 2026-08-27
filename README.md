# Karteikarten

Lernen mit digitalen Karteikarten nach dem **Leitner-System**: fünf Fächer mit
steigenden Wiederholungsintervallen — 1, 3, 7, 14, 30 Tage. Wer eine Karte
weiß, rückt sie ein Fach vor; wer sie nicht weiß, schickt sie zurück ins erste.

Läuft unter <https://karteikarten.baumgartner.online>.

---

## Was die App ausmacht

**Einzelbenutzer, kein Login.** Die App gehört einem Menschen, und ein
Anmeldebildschirm wäre eine Hürde vor dem, wofür man sie öffnet: fünf Minuten
Wiederholung in der Bahn.

**Mobile zuerst, offline nutzbar.** Als Progressive Web App mit Manifest und
Service Worker — der Ort, an dem man lernt, hat oft kein Netz.

**Karten sind bidirektional.** Vorder- und Rückseite lassen sich tauschen; eine
Vokabel in beide Richtungen zu können ist nicht dasselbe wie in eine.

**Lernblöcke statt eines Stapels.** Karten gehören zu einem Thema, und man lernt
ein Thema, nicht alles.

## Eigenständig, nicht Teil der Portal-Landschaft

Diese App teilt sich mit niemandem einen Einstieg oder eine Anmeldung. Sie hat
eine eigene Domain, kein Mandantenkonzept und bindet den geteilten Rahmen
(`chassis`) bewusst **nicht** ein — der brächte ihr Abhängigkeiten für
Probleme, die sie nicht hat.

Die Unterscheidung ist in `L1-architektur` beschrieben und steht in
`app-info.yml`.

---

## Entwickeln

```
make setup     # venv, Abhängigkeiten, pre-commit-Hooks
make run       # Entwicklungsserver
make check     # Lint, Typcheck, Tests
```

**Stack:** Python 3.12, Django 6, SQLite, Bootstrap 5 + Alpine.js + HTMX.
Ausführlich: `AGENTS.md`.

## Was hier dünn ist

Die Testabdeckung. Neun Testfunktionen auf gut 6.000 Zeilen — das Gate ist
grün, aber es bestätigt vor allem, dass diese neun weiterhin durchlaufen.

Der Vorschlag aus dem Flottenreview vom 27.08.2026: nicht auf Vorrat testen,
sondern beim nächsten Eingriff anfangen. Wer eine Funktion anfasst, schreibt
vorher den Test für das Verhalten, das er erhalten will. Nach fünf Eingriffen
steht ein Netz aus echten Fällen statt aus dem Wunsch nach einer Zahl.
