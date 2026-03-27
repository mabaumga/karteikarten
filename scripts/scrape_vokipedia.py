#!/usr/bin/env python
"""
Scraper für Vokipedia - Extrahiert Vokabeln aus À plus! Seiten
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser


class VokipediaParser(HTMLParser):
    """Parser für Vokipedia HTML-Tabellen"""

    def __init__(self):
        super().__init__()
        self.vokabeln = []
        self.current_unite = None
        self.current_volet = None
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_row = []
        self.current_cell = ""
        self.in_heading = False
        self.current_heading = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag in ('td', 'th') and self.in_row:
            self.in_cell = True
            self.current_cell = ""
        elif tag in ('h2', 'h3'):
            self.in_heading = True
            self.current_heading = ""

    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'tr' and self.in_row:
            self.in_row = False
            if len(self.current_row) >= 2:
                # Vokabelzeile gefunden
                fr = self.current_row[0].strip()
                de = self.current_row[1].strip() if len(self.current_row) > 1 else ""
                beispiel_fr = self.current_row[2].strip() if len(self.current_row) > 2 else ""
                beispiel_de = self.current_row[3].strip() if len(self.current_row) > 3 else ""

                if fr and de and not fr.startswith('Französisch'):
                    self.vokabeln.append({
                        "unite": self.current_unite,
                        "volet": self.current_volet,
                        "franzoesisch": fr,
                        "deutsch": de,
                        "beispiel_fr": beispiel_fr if beispiel_fr else None,
                        "beispiel_de": beispiel_de if beispiel_de else None
                    })
        elif tag in ('td', 'th') and self.in_cell:
            self.in_cell = False
            self.current_row.append(self.current_cell)
        elif tag in ('h2', 'h3') and self.in_heading:
            self.in_heading = False
            heading = self.current_heading.strip()
            # Parse heading für Unité/Volet
            if 'Unité' in heading or 'Unite' in heading:
                match = re.search(r'Unit[ée]\s*(\d+)', heading, re.IGNORECASE)
                if match:
                    self.current_unite = int(match.group(1))
            if 'Volet' in heading:
                match = re.search(r'Volet\s*(\d+)', heading, re.IGNORECASE)
                if match:
                    self.current_volet = int(match.group(1))
                else:
                    self.current_volet = heading
            elif 'français en classe' in heading.lower():
                self.current_volet = "Le français en classe"
            elif 'Körper' in heading or 'corps' in heading.lower():
                self.current_unite = 0
                self.current_volet = "Der Körper"
            elif 'Module' in heading:
                self.current_unite = 0
                self.current_volet = heading

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data
        elif self.in_heading:
            self.current_heading += data


def fetch_url(url):
    """Fetch URL content"""
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; VokabelBot/1.0)'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8')


def scrape_vokipedia_page(url, buch_name, band):
    """Scrape eine Vokipedia-Seite"""
    print(f"  Fetching {url}...")
    html = fetch_url(url)

    parser = VokipediaParser()
    parser.feed(html)

    result = {
        "meta": {
            "buch": buch_name,
            "band": band,
            "sprache": "Französisch-Deutsch",
            "quelle": url
        },
        "vokabeln": parser.vokabeln
    }

    print(f"    -> {len(parser.vokabeln)} Vokabeln gefunden")
    return result


def main():
    print("=" * 60)
    print("Vokipedia Scraper - À plus! Vokabeln")
    print("=" * 60)

    pages = [
        {
            "url": "http://www.vokipedia.de/index.php?title=DEU:Franz%C3%B6sisch:%C3%80_plus_2_nouvelle_edition",
            "buch": "À plus! Nouvelle édition",
            "band": 2,
            "output": "/home/marc/git/karteikarten/docs/input/a_plus_2/vokabeln.json"
        },
        {
            "url": "https://www.vokipedia.de/index.php?title=DEU:Franz%C3%B6sisch:%C3%80_plus_3_Nouvelle_%C3%A9dition",
            "buch": "À plus! Nouvelle édition",
            "band": 3,
            "output": "/home/marc/git/karteikarten/docs/input/a_plus_3/vokabeln.json"
        },
        {
            "url": "http://www.vokipedia.de/index.php?title=DEU:Franz%C3%B6sisch:%C3%80_plus!_4_Nouvelle_%C3%A9dition",
            "buch": "À plus! Nouvelle édition",
            "band": 4,
            "output": "/home/marc/git/karteikarten/docs/input/a_plus_4/vokabeln.json"
        }
    ]

    for page in pages:
        print(f"\nScraping {page['buch']} Band {page['band']}...")
        try:
            data = scrape_vokipedia_page(page['url'], page['buch'], page['band'])

            with open(page['output'], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"    -> Gespeichert: {page['output']}")
        except Exception as e:
            print(f"    FEHLER: {e}")

    print("\n" + "=" * 60)
    print("Fertig!")
    print("=" * 60)


if __name__ == '__main__':
    main()
