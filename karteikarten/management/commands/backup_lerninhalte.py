"""
Management command to backup all learning content to JSON files.

Usage:
    python manage.py backup_lerninhalte              # Backup each Lehrwerk separately
    python manage.py backup_lerninhalte --single    # Backup all to single file
    python manage.py backup_lerninhalte --list      # List existing backups
"""

from django.core.management.base import BaseCommand

from karteikarten.services.json_exporter import JSONExporter


class Command(BaseCommand):
    help = 'Backup all learning content to JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Output directory for backup files (default: data/backup)'
        )
        parser.add_argument(
            '--single',
            action='store_true',
            help='Backup all content to a single JSON file'
        )
        parser.add_argument(
            '--no-timestamp',
            action='store_true',
            help='Do not include timestamp in filenames'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List existing backup files'
        )

    def handle(self, *args, **options):
        exporter = JSONExporter(backup_dir=options.get('output_dir'))

        if options['list']:
            self._list_backups(exporter)
            return

        include_timestamp = not options['no_timestamp']

        if options['single']:
            filepath = exporter.backup_all_to_single_file()
            self.stdout.write(
                self.style.SUCCESS(f'Backup created: {filepath}')
            )
        else:
            files = exporter.backup_all(include_timestamp=include_timestamp)
            self.stdout.write(
                self.style.SUCCESS(f'Created {len(files)} backup file(s):')
            )
            for f in files:
                self.stdout.write(f'  - {f}')

    def _list_backups(self, exporter: JSONExporter):
        """List existing backup files."""
        backups = exporter.list_backups()

        if not backups:
            self.stdout.write('No backup files found.')
            return

        self.stdout.write(f'Found {len(backups)} backup file(s):\n')
        for backup in backups:
            size_kb = backup['size'] / 1024
            self.stdout.write(
                f"  {backup['name']:50} {size_kb:8.1f} KB  {backup['modified']:%Y-%m-%d %H:%M}"
            )
