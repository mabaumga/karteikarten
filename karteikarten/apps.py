import os
import sys

from django.apps import AppConfig


class KarteikartenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'karteikarten'
    verbose_name = 'Karteikarten'

    def ready(self):
        """Start background import scheduler when app is ready."""
        # Only start scheduler in the main process (not in migrations, shell, etc.)
        # and only when running the server (gunicorn or runserver)
        if self._should_start_scheduler():
            from karteikarten.services.import_scheduler import start_scheduler

            # Get interval from environment (default: 60 seconds)
            interval = int(os.environ.get('KARTEIKARTEN_IMPORT_INTERVAL', '60'))
            start_scheduler(interval_seconds=interval)

    def _should_start_scheduler(self) -> bool:
        """Check if we should start the scheduler in this process."""
        # Don't start during migrations
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return False

        # Don't start during shell or other management commands
        if len(sys.argv) > 1 and sys.argv[1] in [
            'shell', 'dbshell', 'test', 'collectstatic',
            'createsuperuser', 'check', 'showmigrations',
            'import_lerninhalte',  # Don't run scheduler during manual import
        ]:
            return False

        # Check for RUN_MAIN to avoid double-start with runserver's reloader
        # This env var is set by Django's autoreloader for the child process
        if os.environ.get('RUN_MAIN') == 'true':
            return True

        # For gunicorn/production, always start
        if 'gunicorn' in sys.argv[0] or 'gunicorn' in ' '.join(sys.argv):
            return True

        # For runserver without autoreload
        if 'runserver' in sys.argv and '--noreload' in sys.argv:
            return True

        # Default: don't start (let RUN_MAIN handle it for runserver)
        return False
