"""
Management command to import learning content from JSON files.

Usage:
    python manage.py import_lerninhalte                    # Scan default import dir
    python manage.py import_lerninhalte --dir /path/to/dir # Scan specific dir
    python manage.py import_lerninhalte --file /path/to/file.json  # Import single file
    python manage.py import_lerninhalte --list-history     # Show import history
    python manage.py import_lerninhalte --list-archive     # Show archived files
"""

from django.core.management.base import BaseCommand, CommandError
from pathlib import Path

from karteikarten.services.json_importer import JSONImporter


class Command(BaseCommand):
    help = 'Import learning content from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            help='Directory to scan for JSON files (default: from settings/env)',
        )
        parser.add_argument(
            '--archive-dir',
            type=str,
            help='Directory for archived files (default: from settings/env)',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Import a single JSON file',
        )
        parser.add_argument(
            '--list-history',
            action='store_true',
            help='List recent import history',
        )
        parser.add_argument(
            '--list-archive',
            action='store_true',
            help='List archived files',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate files without importing',
        )

    def handle(self, *args, **options):
        import_dir = options.get('dir')
        archive_dir = options.get('archive_dir')

        importer = JSONImporter(
            import_dir=import_dir,
            archive_dir=archive_dir,
        )

        # List history
        if options['list_history']:
            self.list_history(importer)
            return

        # List archive
        if options['list_archive']:
            self.list_archive(importer)
            return

        # Import single file
        if options['file']:
            filepath = Path(options['file'])
            if not filepath.exists():
                raise CommandError(f"File not found: {filepath}")

            if options['dry_run']:
                self.dry_run_file(importer, filepath)
            else:
                self.import_single_file(importer, filepath)
            return

        # Scan directory
        if options['dry_run']:
            self.dry_run_directory(importer)
        else:
            self.scan_and_import(importer)

    def import_single_file(self, importer: JSONImporter, filepath: Path):
        """Import a single file."""
        self.stdout.write(f"Importing {filepath}...")

        log = importer.import_file(filepath)

        if log.status == 'success':
            self.stdout.write(self.style.SUCCESS(
                f"OK: {log.anzahl_bloecke} Bloecke, {log.anzahl_karten} Karten importiert"
            ))
        elif log.status == 'skipped':
            self.stdout.write(self.style.WARNING(
                f"Uebersprungen: {log.nachricht}"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"Fehler: {log.nachricht}"
            ))

    def scan_and_import(self, importer: JSONImporter):
        """Scan directory and import all files."""
        import_dir = importer.import_dir
        self.stdout.write(f"Scanning {import_dir}...")

        # Check if directory exists
        if not import_dir.exists():
            self.stdout.write(self.style.WARNING(
                f"Import-Verzeichnis existiert nicht: {import_dir}"
            ))
            return

        # List directory contents for debugging
        all_files = list(import_dir.iterdir()) if import_dir.is_dir() else []
        json_files = [f for f in all_files if f.suffix == '.json']

        self.stdout.write(f"  Verzeichnisinhalt: {len(all_files)} Dateien gesamt")
        self.stdout.write(f"  JSON-Dateien: {len(json_files)}")

        if json_files:
            for f in json_files:
                self.stdout.write(f"    - {f.name}")

        results = importer.scan_and_import()

        if not results:
            self.stdout.write(self.style.WARNING("Keine JSON-Dateien gefunden"))
            return

        # Summary
        success = sum(1 for r in results if r.status == 'success')
        skipped = sum(1 for r in results if r.status == 'skipped')
        errors = sum(1 for r in results if r.status == 'error')
        total_cards = sum(r.anzahl_karten for r in results)
        total_blocks = sum(r.anzahl_bloecke for r in results)

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Import abgeschlossen:")
        self.stdout.write(f"  Erfolgreich: {success}")
        self.stdout.write(f"  Uebersprungen: {skipped}")
        self.stdout.write(f"  Fehler: {errors}")
        self.stdout.write(f"  Gesamt Bloecke: {total_blocks}")
        self.stdout.write(f"  Gesamt Karten: {total_cards}")
        self.stdout.write("=" * 50)

        if errors > 0:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("Fehler bei folgenden Dateien:"))
            for r in results:
                if r.status == 'error':
                    self.stdout.write(f"  - {r.dateiname}: {r.nachricht}")

    def dry_run_file(self, importer: JSONImporter, filepath: Path):
        """Validate a single file without importing."""
        self.stdout.write(f"Validating {filepath}...")

        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        is_valid, error_msg = importer.validate_json(data)

        if is_valid:
            meta = data.get('meta', {})
            inhalt = data.get('inhalt', [])
            total_blocks = sum(len(u.get('bloecke', [])) for u in inhalt)
            total_cards = sum(
                len(b.get('karten', []))
                for u in inhalt
                for b in u.get('bloecke', [])
            )

            self.stdout.write(self.style.SUCCESS("Validierung erfolgreich!"))
            self.stdout.write(f"  Fach: {meta.get('fach', 'N/A')}")
            self.stdout.write(f"  Lehrwerk: {meta.get('lehrwerk', 'N/A')}")
            self.stdout.write(f"  Band: {meta.get('band', 'N/A')}")
            self.stdout.write(f"  Units: {len(inhalt)}")
            self.stdout.write(f"  Bloecke: {total_blocks}")
            self.stdout.write(f"  Karten: {total_cards}")
        else:
            self.stdout.write(self.style.ERROR(f"Validierung fehlgeschlagen: {error_msg}"))

    def dry_run_directory(self, importer: JSONImporter):
        """Validate all files in directory without importing."""
        import json

        self.stdout.write(f"Validating files in {importer.import_dir}...")

        json_files = list(importer.import_dir.glob('*.json'))

        if not json_files:
            self.stdout.write(self.style.WARNING("Keine JSON-Dateien gefunden"))
            return

        for filepath in json_files:
            self.stdout.write(f"\n{filepath.name}:")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                is_valid, error_msg = importer.validate_json(data)

                if is_valid:
                    self.stdout.write(self.style.SUCCESS("  OK"))
                else:
                    self.stdout.write(self.style.ERROR(f"  Fehler: {error_msg}"))
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"  JSON-Fehler: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Fehler: {e}"))

    def list_history(self, importer: JSONImporter):
        """List recent import history."""
        history = importer.get_import_history(limit=20)

        if not history:
            self.stdout.write("Keine Import-Historie vorhanden")
            return

        self.stdout.write("Import-Historie (letzte 20):")
        self.stdout.write("-" * 80)

        for log in history:
            status_style = {
                'success': self.style.SUCCESS,
                'error': self.style.ERROR,
                'skipped': self.style.WARNING,
            }.get(log.status, lambda x: x)

            self.stdout.write(
                f"{log.importiert_am.strftime('%Y-%m-%d %H:%M')} | "
                f"{status_style(log.status.ljust(8))} | "
                f"{log.dateiname[:40].ljust(40)} | "
                f"{log.anzahl_karten} Karten"
            )

    def list_archive(self, importer: JSONImporter):
        """List archived files."""
        files = importer.get_archived_files()

        if not files:
            self.stdout.write("Keine archivierten Dateien vorhanden")
            return

        self.stdout.write(f"Archiv ({importer.archive_dir}):")
        self.stdout.write("-" * 80)

        for f in files[:20]:
            size_kb = f['size'] / 1024
            self.stdout.write(
                f"{f['modified'].strftime('%Y-%m-%d %H:%M')} | "
                f"{size_kb:8.1f} KB | "
                f"{f['name']}"
            )
