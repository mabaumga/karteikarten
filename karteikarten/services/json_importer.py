"""
JSON Importer Service for Karteikarten.

Imports vocabulary and learning content from JSON files following the lerninhalt schema.
"""

import hashlib
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import transaction

from karteikarten.models import (
    ImportLog,
    Jahrgangsstufe,
    Karteikarte,
    Lehrwerk,
    LehrwerkUnit,
    Lernblock,
    Schulfach,
)

logger = logging.getLogger(__name__)


class ImportError(Exception):
    """Custom exception for import errors."""
    pass


class JSONImporter:
    """
    Imports learning content from JSON files.

    Features:
    - Validates JSON against schema
    - Creates/updates Lehrwerk, Units, Lernblöcke, Karteikarten
    - Tracks imports via hash to avoid duplicates
    - Archives imported files
    - Logs all import activities
    """

    SCHEMA_VERSION = "1.0"
    MIN_CARDS_PER_BLOCK = 1  # Minimum cards per block

    def __init__(self, import_dir: str = None, archive_dir: str = None):
        """
        Initialize importer.

        Args:
            import_dir: Directory to scan for JSON files
            archive_dir: Directory to move imported files to
        """
        self.import_dir = Path(import_dir) if import_dir else self._get_default_import_dir()
        self.archive_dir = Path(archive_dir) if archive_dir else self._get_default_archive_dir()

        # Ensure directories exist
        self.import_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def _get_default_import_dir(self) -> Path:
        """Get default import directory from settings or environment."""
        return Path(
            os.environ.get('KARTEIKARTEN_IMPORT_DIR', '') or
            getattr(settings, 'KARTEIKARTEN_IMPORT_DIR', '') or
            settings.BASE_DIR / 'data' / 'import'
        )

    def _get_default_archive_dir(self) -> Path:
        """Get default archive directory from settings or environment."""
        return Path(
            os.environ.get('KARTEIKARTEN_ARCHIVE_DIR', '') or
            getattr(settings, 'KARTEIKARTEN_ARCHIVE_DIR', '') or
            settings.BASE_DIR / 'data' / 'archive'
        )

    def calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def is_already_imported(self, file_hash: str) -> bool:
        """Check if a file with this hash was already imported."""
        return ImportLog.objects.filter(
            datei_hash=file_hash,
            status='success'
        ).exists()

    def validate_json(self, data: dict) -> tuple[bool, str]:
        """
        Validate JSON structure against schema.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if 'meta' not in data:
            return False, "Fehlendes 'meta' Feld"

        if 'inhalt' not in data:
            return False, "Fehlendes 'inhalt' Feld"

        meta = data['meta']

        if 'fach' not in meta:
            return False, "Fehlendes 'meta.fach' Feld"

        if 'lehrwerk' not in meta:
            return False, "Fehlendes 'meta.lehrwerk' Feld"

        # Validate content structure
        inhalt = data['inhalt']
        if not isinstance(inhalt, list):
            return False, "'inhalt' muss eine Liste sein"

        if len(inhalt) == 0:
            return False, "'inhalt' darf nicht leer sein"

        for i, unit in enumerate(inhalt):
            if 'name' not in unit:
                return False, f"Unit {i}: Fehlendes 'name' Feld"

            if 'bloecke' not in unit:
                return False, f"Unit {i}: Fehlendes 'bloecke' Feld"

            for j, block in enumerate(unit.get('bloecke', [])):
                if 'name' not in block:
                    return False, f"Unit {i}, Block {j}: Fehlendes 'name' Feld"

                if 'karten' not in block:
                    return False, f"Unit {i}, Block {j}: Fehlendes 'karten' Feld"

                karten = block.get('karten', [])
                if len(karten) < self.MIN_CARDS_PER_BLOCK:
                    return False, f"Unit {i}, Block {j}: Mindestens {self.MIN_CARDS_PER_BLOCK} Karte(n) erforderlich"

                for k, karte in enumerate(karten):
                    if 'vorne' not in karte:
                        return False, f"Unit {i}, Block {j}, Karte {k}: Fehlendes 'vorne' Feld"
                    if 'hinten' not in karte:
                        return False, f"Unit {i}, Block {j}, Karte {k}: Fehlendes 'hinten' Feld"

        return True, ""

    def get_or_create_schulfach(self, name: str) -> Schulfach:
        """Get or create a Schulfach."""
        schulfach, _ = Schulfach.objects.get_or_create(
            name=name,
            defaults={'beschreibung': ''}
        )
        return schulfach

    def get_or_create_jahrgangsstufe(self, klasse: int) -> Jahrgangsstufe:
        """Get or create a Jahrgangsstufe."""
        jahrgangsstufe, _ = Jahrgangsstufe.objects.get_or_create(
            stufe=klasse,
            defaults={'bezeichnung': ''}
        )
        return jahrgangsstufe

    def get_or_create_lehrwerk(self, meta: dict) -> Lehrwerk:
        """Get or create a Lehrwerk from meta information."""
        name = meta['lehrwerk']
        band = str(meta.get('band', '')) if meta.get('band') else ''

        # Get related objects
        schulfach = None
        if meta.get('fach'):
            schulfach = self.get_or_create_schulfach(meta['fach'])

        jahrgangsstufe = None
        if meta.get('klasse'):
            jahrgangsstufe = self.get_or_create_jahrgangsstufe(meta['klasse'])

        lehrwerk, created = Lehrwerk.objects.get_or_create(
            name=name,
            band=band,
            defaults={
                'verlag': meta.get('verlag', ''),
                'schulfach': schulfach,
                'jahrgangsstufe': jahrgangsstufe,
                'sprachen': meta.get('sprachen', []),
            }
        )

        # Update if already exists
        if not created:
            if schulfach:
                lehrwerk.schulfach = schulfach
            if jahrgangsstufe:
                lehrwerk.jahrgangsstufe = jahrgangsstufe
            if meta.get('verlag'):
                lehrwerk.verlag = meta['verlag']
            if meta.get('sprachen'):
                lehrwerk.sprachen = meta['sprachen']
            lehrwerk.save()

        return lehrwerk

    def get_or_create_unit(self, lehrwerk: Lehrwerk, unit_data: dict, reihenfolge: int) -> LehrwerkUnit:
        """Get or create a LehrwerkUnit."""
        unit, created = LehrwerkUnit.objects.get_or_create(
            lehrwerk=lehrwerk,
            name=unit_data['name'],
            defaults={
                'beschreibung': unit_data.get('beschreibung', ''),
                'reihenfolge': reihenfolge,
            }
        )

        if not created:
            unit.beschreibung = unit_data.get('beschreibung', '')
            unit.reihenfolge = reihenfolge
            unit.save()

        return unit

    def create_or_update_lernblock(
        self,
        unit: LehrwerkUnit,
        block_data: dict,
        felder_config: dict,
        import_quelle: str,
        import_hash: str
    ) -> tuple[Lernblock, int]:
        """
        Create or update a Lernblock with its cards.

        Returns:
            Tuple of (Lernblock, number of cards created)
        """
        block_name = block_data['name']

        # Try to find existing block by unit and name
        lernblock = Lernblock.objects.filter(
            lehrwerk_unit=unit,
            name=block_name
        ).first()

        if lernblock:
            # Update existing block
            lernblock.beschreibung = block_data.get('beschreibung', '')
            lernblock.bidirektional = block_data.get('bidirektional', True)
            lernblock.feld_konfiguration = felder_config
            lernblock.import_quelle = import_quelle
            lernblock.import_hash = import_hash
            lernblock.save()

            # Delete existing cards for re-import
            lernblock.karten.all().delete()
        else:
            # Create new block
            lernblock = Lernblock.objects.create(
                name=block_name,
                beschreibung=block_data.get('beschreibung', ''),
                lehrwerk_unit=unit,
                bidirektional=block_data.get('bidirektional', True),
                feld_konfiguration=felder_config,
                import_quelle=import_quelle,
                import_hash=import_hash,
                # Also set legacy fields for backwards compatibility
                schulfach=unit.lehrwerk.schulfach,
                jahrgangsstufe=unit.lehrwerk.jahrgangsstufe,
            )

        # Create cards
        cards_created = 0
        for karte_data in block_data.get('karten', []):
            self.create_karteikarte(lernblock, karte_data)
            cards_created += 1

        return lernblock, cards_created

    def create_karteikarte(self, lernblock: Lernblock, karte_data: dict) -> Karteikarte:
        """Create a single Karteikarte."""
        # Handle beispiel (can be string or object)
        beispiel = karte_data.get('beispiel', '')
        beispiele_text = ''
        beispiel_json = {}

        if isinstance(beispiel, str):
            beispiele_text = beispiel
        elif isinstance(beispiel, dict):
            beispiel_json = beispiel
            # Also create text version for display
            beispiele_text = ' / '.join(f"{k}: {v}" for k, v in beispiel.items())

        # Handle zusatz (can be dict)
        zusatz = karte_data.get('zusatz', {})
        zusatz_json = zusatz if isinstance(zusatz, dict) else {}

        # Legacy zusatz fields (use first key-value pair if available)
        zusatz_label = ''
        zusatz_wert = ''
        if zusatz_json:
            first_key = list(zusatz_json.keys())[0]
            zusatz_label = first_key
            zusatz_wert = str(zusatz_json[first_key])

        # Tags
        tags = karte_data.get('tags', [])
        if not isinstance(tags, list):
            tags = [tags] if tags else []

        # Create card (use get_or_create to handle duplicates)
        karte, created = Karteikarte.objects.get_or_create(
            lernblock=lernblock,
            begriff=karte_data['vorne'],
            defaults={
                'definition': karte_data['hinten'],
                'beispiele': beispiele_text,
                'beispiel_json': beispiel_json,
                'zusatz_label': zusatz_label,
                'zusatz_wert': zusatz_wert,
                'zusatz_json': zusatz_json,
                'tags': tags,
                'seite': str(karte_data.get('seite', '')),
            }
        )

        if not created:
            # Update existing card
            karte.definition = karte_data['hinten']
            karte.beispiele = beispiele_text
            karte.beispiel_json = beispiel_json
            karte.zusatz_label = zusatz_label
            karte.zusatz_wert = zusatz_wert
            karte.zusatz_json = zusatz_json
            karte.tags = tags
            karte.seite = str(karte_data.get('seite', ''))
            karte.save()

        return karte

    def archive_file(self, filepath: Path, success: bool = True) -> str:
        """
        Move imported file to archive.

        Args:
            filepath: Original file path
            success: Whether import was successful

        Returns:
            Archive path as string
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        status_prefix = 'success' if success else 'error'
        archive_name = f"{status_prefix}_{timestamp}_{filepath.name}"
        archive_path = self.archive_dir / archive_name

        shutil.move(str(filepath), str(archive_path))

        return str(archive_path)

    def import_file(self, filepath: Path) -> ImportLog:
        """
        Import a single JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            ImportLog entry
        """
        logger.info(f"Importing {filepath}")

        # Calculate hash
        file_hash = self.calculate_file_hash(filepath)

        # Check if already imported
        if self.is_already_imported(file_hash):
            logger.info(f"File already imported: {filepath}")
            archive_path = self.archive_file(filepath, success=True)
            log = ImportLog.objects.create(
                dateiname=filepath.name,
                dateipfad=str(filepath),
                datei_hash=file_hash,
                status='skipped',
                nachricht='Datei wurde bereits importiert (gleicher Hash)',
                archiv_pfad=archive_path,
            )
            return log

        try:
            # Load JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate BEFORE starting transaction
            is_valid, error_msg = self.validate_json(data)
            if not is_valid:
                raise ImportError(f"Validierungsfehler: {error_msg}")

            # Import data in transaction
            with transaction.atomic():
                meta = data['meta']
                felder = data.get('felder', {})
                inhalt = data['inhalt']

                # Create/get Lehrwerk
                lehrwerk = self.get_or_create_lehrwerk(meta)

                # Process units and blocks
                total_cards = 0
                total_blocks = 0

                for unit_idx, unit_data in enumerate(inhalt):
                    unit = self.get_or_create_unit(lehrwerk, unit_data, unit_idx)

                    for block_data in unit_data.get('bloecke', []):
                        lernblock, cards_count = self.create_or_update_lernblock(
                            unit=unit,
                            block_data=block_data,
                            felder_config=felder,
                            import_quelle=filepath.name,
                            import_hash=file_hash,
                        )
                        total_cards += cards_count
                        total_blocks += 1

            # Archive file AFTER successful transaction
            archive_path = self.archive_file(filepath, success=True)

            # Log success
            log = ImportLog.objects.create(
                dateiname=filepath.name,
                dateipfad=str(filepath),
                datei_hash=file_hash,
                status='success',
                nachricht=f"Erfolgreich importiert: {total_blocks} Blöcke, {total_cards} Karten",
                lehrwerk=lehrwerk,
                anzahl_karten=total_cards,
                anzahl_bloecke=total_blocks,
                archiv_pfad=archive_path,
            )

            logger.info(f"Successfully imported {filepath}: {total_blocks} blocks, {total_cards} cards")
            return log

        except Exception as e:
            logger.error(f"Error importing {filepath}: {e}")

            # Archive with error status - ALWAYS archive to prevent retry loops
            try:
                archive_path = self.archive_file(filepath, success=False)
            except Exception as archive_error:
                logger.error(f"Failed to archive {filepath}: {archive_error}")
                archive_path = str(filepath)

            # Log error
            log = ImportLog.objects.create(
                dateiname=filepath.name,
                dateipfad=str(filepath),
                datei_hash=file_hash,
                status='error',
                nachricht=str(e),
                archiv_pfad=archive_path,
            )

            return log

    def scan_and_import(self) -> list[ImportLog]:
        """
        Scan import directory and import all JSON files.

        Returns:
            List of ImportLog entries
        """
        logger.info(f"Scanning {self.import_dir} for JSON files")

        results = []

        # Find all JSON files
        json_files = list(self.import_dir.glob('*.json'))

        logger.info(f"Found {len(json_files)} JSON file(s)")

        for filepath in json_files:
            try:
                log = self.import_file(filepath)
                results.append(log)
            except Exception as e:
                logger.error(f"Unexpected error processing {filepath}: {e}")

        return results

    def get_import_history(self, limit: int = 50) -> list[ImportLog]:
        """Get recent import history."""
        return list(ImportLog.objects.all()[:limit])

    def get_archived_files(self) -> list[dict]:
        """List all archived files."""
        files = []
        for filepath in self.archive_dir.iterdir():
            if filepath.is_file():
                stat = filepath.stat()
                files.append({
                    'name': filepath.name,
                    'path': str(filepath),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                })
        return sorted(files, key=lambda x: x['modified'], reverse=True)
