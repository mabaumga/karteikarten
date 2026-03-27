"""
JSON Exporter Service for Karteikarten.

Exports learning content to JSON files following the lerninhalt schema.
This creates backups that can be re-imported using the JSONImporter.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from django.conf import settings

from karteikarten.models import Lehrwerk, LehrwerkUnit, Lernblock, Karteikarte

logger = logging.getLogger(__name__)


class JSONExporter:
    """
    Exports learning content to JSON files.

    Features:
    - Exports by Lehrwerk, Unit, or all content
    - Uses same schema as importer for round-trip compatibility
    - Creates timestamped backup files
    """

    def __init__(self, backup_dir: str = None):
        """
        Initialize exporter.

        Args:
            backup_dir: Directory for backup files
        """
        self.backup_dir = Path(backup_dir) if backup_dir else self._get_default_backup_dir()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _get_default_backup_dir(self) -> Path:
        """Get default backup directory from settings or environment."""
        return Path(
            os.environ.get('KARTEIKARTEN_BACKUP_DIR', '') or
            getattr(settings, 'KARTEIKARTEN_BACKUP_DIR', '') or
            settings.BASE_DIR / 'data' / 'backup'
        )

    def _karte_to_dict(self, karte: Karteikarte) -> dict:
        """Convert a Karteikarte to dictionary format."""
        result = {
            "vorne": karte.begriff,
            "hinten": karte.definition,
        }

        # Add beispiel if present
        if karte.beispiel_json:
            result["beispiel"] = karte.beispiel_json
        elif karte.beispiele:
            result["beispiel"] = karte.beispiele

        # Add zusatz if present
        if karte.zusatz_json:
            result["zusatz"] = karte.zusatz_json
        elif karte.zusatz_label and karte.zusatz_wert:
            result["zusatz"] = {karte.zusatz_label: karte.zusatz_wert}

        # Add tags if present
        if karte.tags:
            result["tags"] = karte.tags

        # Add page reference if present
        if karte.seite:
            result["seite"] = karte.seite

        return result

    def _block_to_dict(self, block: Lernblock) -> dict:
        """Convert a Lernblock to dictionary format."""
        karten = [self._karte_to_dict(k) for k in block.karten.all()]

        return {
            "name": block.name,
            "beschreibung": block.beschreibung or None,
            "bidirektional": block.bidirektional,
            "karten": karten,
        }

    def _unit_to_dict(self, unit: LehrwerkUnit) -> dict:
        """Convert a LehrwerkUnit to dictionary format."""
        bloecke = [self._block_to_dict(b) for b in unit.lernbloecke.all()]

        return {
            "name": unit.name,
            "beschreibung": unit.beschreibung or None,
            "bloecke": bloecke,
        }

    def export_lehrwerk(self, lehrwerk: Lehrwerk) -> dict:
        """
        Export a complete Lehrwerk to dictionary format.

        Args:
            lehrwerk: The Lehrwerk to export

        Returns:
            Dictionary in lerninhalt schema format
        """
        # Build meta
        meta = {
            "fach": lehrwerk.schulfach.name if lehrwerk.schulfach else "",
            "lehrwerk": lehrwerk.name,
            "verlag": lehrwerk.verlag or "",
            "sprachen": lehrwerk.sprachen or [],
            "version": "1.0",
            "quelle": "Karteikarten-Backup",
            "export_datum": datetime.now().isoformat(),
        }

        if lehrwerk.band:
            meta["band"] = lehrwerk.band

        if lehrwerk.jahrgangsstufe:
            meta["klasse"] = lehrwerk.jahrgangsstufe.stufe

        # Build felder from first block's configuration (if available)
        felder = {}
        first_unit = lehrwerk.units.first()
        if first_unit:
            first_block = first_unit.lernbloecke.first()
            if first_block and first_block.feld_konfiguration:
                felder = first_block.feld_konfiguration

        # Build inhalt
        inhalt = [self._unit_to_dict(u) for u in lehrwerk.units.all()]

        # Remove None values from beschreibung
        for unit in inhalt:
            if unit.get("beschreibung") is None:
                del unit["beschreibung"]
            for block in unit.get("bloecke", []):
                if block.get("beschreibung") is None:
                    del block["beschreibung"]

        return {
            "meta": meta,
            "felder": felder,
            "inhalt": inhalt,
        }

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as filename."""
        # Replace problematic characters
        replacements = {
            ' ': '_',
            '/': '_',
            '\\': '_',
            ':': '_',
            '!': '',
            '?': '',
            '+': 'plus',
            'ä': 'ae',
            'ö': 'oe',
            'ü': 'ue',
            'ß': 'ss',
            'Ä': 'Ae',
            'Ö': 'Oe',
            'Ü': 'Ue',
            'é': 'e',
            'è': 'e',
            'ê': 'e',
            'à': 'a',
            'â': 'a',
            'ô': 'o',
            'î': 'i',
            'ç': 'c',
        }
        result = name
        for old, new in replacements.items():
            result = result.replace(old, new)
        # Remove any remaining problematic characters
        result = ''.join(c for c in result if c.isalnum() or c in '_-')
        return result.lower()

    def backup_lehrwerk(self, lehrwerk: Lehrwerk, include_timestamp: bool = True) -> Path:
        """
        Backup a single Lehrwerk to a JSON file.

        Args:
            lehrwerk: The Lehrwerk to backup
            include_timestamp: Whether to include timestamp in filename

        Returns:
            Path to the created backup file
        """
        data = self.export_lehrwerk(lehrwerk)

        # Generate filename
        name_parts = [self._sanitize_filename(lehrwerk.name)]
        if lehrwerk.band:
            name_parts.append(f"band{lehrwerk.band}")
        if lehrwerk.jahrgangsstufe:
            name_parts.append(f"klasse{lehrwerk.jahrgangsstufe.stufe}")

        filename = "_".join(name_parts)

        if include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{filename}_{timestamp}"

        filepath = self.backup_dir / f"{filename}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Count cards
        total_cards = sum(
            len(b['karten'])
            for u in data['inhalt']
            for b in u['bloecke']
        )

        logger.info(f"Backed up {lehrwerk}: {len(data['inhalt'])} units, {total_cards} cards -> {filepath}")

        return filepath

    def backup_all(self, include_timestamp: bool = True) -> list[Path]:
        """
        Backup all Lehrwerke to JSON files.

        Args:
            include_timestamp: Whether to include timestamp in filenames

        Returns:
            List of paths to created backup files
        """
        results = []

        for lehrwerk in Lehrwerk.objects.all():
            # Skip empty Lehrwerke
            if lehrwerk.anzahl_karten == 0:
                logger.info(f"Skipping empty Lehrwerk: {lehrwerk}")
                continue

            try:
                filepath = self.backup_lehrwerk(lehrwerk, include_timestamp)
                results.append(filepath)
            except Exception as e:
                logger.error(f"Error backing up {lehrwerk}: {e}")

        return results

    def backup_all_to_single_file(self, filename: str = None) -> Path:
        """
        Backup all content to a single JSON file with multiple Lehrwerke.

        Args:
            filename: Optional filename (without extension)

        Returns:
            Path to the created backup file
        """
        all_data = []

        for lehrwerk in Lehrwerk.objects.all():
            if lehrwerk.anzahl_karten == 0:
                continue
            all_data.append(self.export_lehrwerk(lehrwerk))

        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"karteikarten_komplett_{timestamp}"

        filepath = self.backup_dir / f"{filename}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        total_cards = sum(
            len(b['karten'])
            for lw in all_data
            for u in lw['inhalt']
            for b in u['bloecke']
        )

        logger.info(f"Backed up all: {len(all_data)} Lehrwerke, {total_cards} cards -> {filepath}")

        return filepath

    def list_backups(self) -> list[dict]:
        """List all backup files."""
        files = []
        for filepath in self.backup_dir.glob('*.json'):
            stat = filepath.stat()
            files.append({
                'name': filepath.name,
                'path': str(filepath),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
            })
        return sorted(files, key=lambda x: x['modified'], reverse=True)
